from __future__ import annotations

"""RedisQueueRepository
========================
DAG Manager 작업 큐 전용 레포지토리.

설계 목표
---------
1. Redis list 구조를 사용해 작업을 **LPUSH → BRPOPLPUSH** 로 가져오는 방식
2. pop 시 `queue_key → processing_key` 로 이동하여 in-flight 작업 추적
3. complete 호출 시 processing 리스트에서 제거하고 결과 해시(`results_key`)에 저장
   - 기본 TTL 1시간(3600s) 설정

※ 실제 프로덕션 환경에서는 protobuf WorkItem을 SerializeToString() 해서 push 함.
   여기서는 bytes 또는 str(any serialised form)을 그대로 저장하게끔 단순화.
"""

from datetime import datetime
from typing import Any, Optional

import json
import redis


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


class RedisQueueRepository:
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        redis_url: str = "redis://localhost:6379/0",
        queue_key: str = "qmtl:dag:work_queue",
        processing_key: str = "qmtl:dag:processing",
        results_key: str = "qmtl:dag:results",
    ) -> None:
        self.redis = redis_client or redis.from_url(redis_url)
        self.queue_key = queue_key
        self.processing_key = processing_key
        self.results_key = results_key

    # ------------------------------------------------------------------
    # Enqueue / Dequeue
    # ------------------------------------------------------------------
    def push(self, item: bytes | str) -> None:  # noqa: D401 simple
        """작업 큐에 항목 추가"""
        self.redis.lpush(self.queue_key, item)

    def pop(self, timeout: int = 0) -> Optional[bytes | str]:  # noqa: D401
        """blocking pop → processing list로 이동"""
        return self.redis.brpoplpush(self.queue_key, self.processing_key, timeout)

    # ------------------------------------------------------------------
    # Completion & Result
    # ------------------------------------------------------------------
    def complete(self, work_id: str, result: Any = None, ttl: int = 3600) -> bool:
        """작업 완료 처리. 결과를 해시로 기록 후 processing list 에서 제거."""
        # 처리 중 리스트 검색
        removed = self.redis.lrem(self.processing_key, 0, work_id)
        if removed:
            payload = {
                "completed_at": _now_iso(),
                "result": result,
            }
            self.redis.hset(self.results_key, work_id, json.dumps(payload))
            self.redis.expire(self.results_key, ttl)
            return True
        return False

    # ------------------------------------------------------------------
    # Result 조회 helpers
    # ------------------------------------------------------------------
    def get_result(self, work_id: str) -> Optional[dict]:  # noqa: D401
        data = self.redis.hget(self.results_key, work_id)
        if not data:
            return None
        try:
            return json.loads(data)
        except Exception:
            return {"raw": data}
