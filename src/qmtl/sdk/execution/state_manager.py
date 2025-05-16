"""
Redis 기반 상태 관리자
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class StateManager:
    def __init__(
        self,
        redis_uri: str = "redis://localhost:6379/0",
        connection_pool_size: int = 10,
        connection_timeout: float = 5.0,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30,
    ):
        if not REDIS_AVAILABLE:
            raise ImportError(
                "상태 관리를 위해서는 redis 패키지가 필요합니다. "
                "pip install redis 명령으로 설치하세요."
            )
        self.redis_uri = redis_uri
        self._redis = None
        self._connection_params = {
            "max_connections": connection_pool_size,
            "socket_timeout": connection_timeout,
            "socket_connect_timeout": connection_timeout,
            "retry_on_timeout": retry_on_timeout,
            "health_check_interval": health_check_interval,
        }

    @property
    def redis(self):
        if self._redis is None:
            try:
                self._redis = redis.from_url(self.redis_uri, **self._connection_params)
                self._redis.ping()
                logging.debug("Redis 연결 성공")
            except redis.ConnectionError as e:
                logging.error(f"Redis 연결 실패: {e}")
                self._redis = redis.from_url(self.redis_uri, **self._connection_params)
            except Exception as e:
                logging.error(f"Redis 초기화 중 예외 발생: {e}")
                self._redis = redis.from_url(self.redis_uri, **self._connection_params)
        return self._redis

    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        try:
            serialized = json.dumps(value)
            result = self.redis.set(key, serialized, ex=expire)
            return result
        except Exception as e:
            logging.error(f"Redis 값 설정 중 오류 발생: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        try:
            value = self.redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logging.error(f"Redis 값 조회 중 오류 발생: {e}")
            return None

    def delete(self, key: str) -> bool:
        try:
            result = self.redis.delete(key)
            return result > 0
        except Exception as e:
            logging.error(f"Redis 키 삭제 중 오류 발생: {e}")
            return False

    def _get_storage_key(self, node_id: str, interval: str, key_type: str = "history") -> str:
        return f"node:{node_id}:{key_type}:{interval}"

    def save_history(
        self,
        node_id: str,
        interval: str,
        value: Any,
        max_items: int = 100,
        ttl: Optional[int] = None,
    ) -> bool:
        try:
            key = self._get_storage_key(node_id, interval)
            timestamp = int(time.time())
            item = {"timestamp": timestamp, "value": value}
            pipeline = self.redis.pipeline()
            serialized = json.dumps(item)
            pipeline.lpush(key, serialized)
            pipeline.ltrim(key, 0, max_items - 1)
            if ttl:
                pipeline.expire(key, ttl)
            pipeline.execute()
            meta_key = self._get_storage_key(node_id, interval, "meta")
            meta_data = {
                "last_update": timestamp,
                "count": min(max_items, self.redis.llen(key)),
                "max_items": max_items,
                "ttl": ttl,
            }
            self.set(meta_key, meta_data, ttl)
            return True
        except Exception as e:
            logging.error(f"히스토리 저장 중 오류 발생: {e}")
            return False

    def get_history(
        self,
        node_id: str,
        interval: str,
        count: int = 10,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        try:
            key = self._get_storage_key(node_id, interval)
            # start_ts, end_ts가 없으면 count만큼만 조회
            if not start_ts and not end_ts:
                items = self.redis.lrange(key, 0, count - 1)
                result = []
                for item in items:
                    try:
                        data = json.loads(item)
                        result.append(data)
                    except Exception as e:
                        logging.warning(f"히스토리 항목 역직렬화 중 오류: {e}")
                        continue
                return result
            # 필터가 있으면 전체 조회 후 필터링
            items = self.redis.lrange(key, 0, -1)
            filtered = []
            for item in items:
                try:
                    data = json.loads(item)
                    ts = data.get("timestamp", 0)
                    if start_ts and ts <= start_ts:
                        continue
                    if end_ts and ts > end_ts:
                        continue
                    filtered.append(data)
                except Exception as e:
                    logging.warning(f"히스토리 항목 역직렬화 중 오류: {e}")
                    continue
            return filtered[:count]
        except Exception as e:
            logging.error(f"히스토리 조회 중 오류 발생: {e}")
            return []

    def get_history_metadata(self, node_id: str, interval: str) -> Dict[str, Any]:
        meta_key = self._get_storage_key(node_id, interval, "meta")
        meta = self.get(meta_key) or {}
        history_key = self._get_storage_key(node_id, interval)
        try:
            count = self.redis.llen(history_key)
            meta["actual_count"] = count
        except Exception:
            meta["actual_count"] = meta.get("count", 0)
        return meta

    def update_ttl(self, node_id: str, interval: str, ttl: int) -> bool:
        try:
            history_key = self._get_storage_key(node_id, interval)
            history_result = self.redis.expire(history_key, ttl)
            meta_key = self._get_storage_key(node_id, interval, "meta")
            meta_result = self.redis.expire(meta_key, ttl)
            meta = self.get(meta_key) or {}
            meta["ttl"] = ttl
            meta["ttl_updated_at"] = int(time.time())
            self.set(meta_key, meta, ttl)
            return history_result and meta_result
        except Exception as e:
            logging.error(f"TTL 업데이트 중 오류 발생: {e}")
            return False

    def get_interval_data(self, node_id: str, interval: str, count: int = 1) -> List[Any]:
        history = self.get_history(node_id, interval, count)
        return [item["value"] for item in history]

    def clean_expired_data(self, node_id: str = None) -> int:
        try:
            pattern = f"node:{'*' if node_id is None else node_id}:*"
            cleaned = 0
            for key in self.redis.scan_iter(match=pattern):
                ttl = self.redis.ttl(key)
                if ttl >= 0:
                    continue
                if ttl == -1:
                    continue
                if self.redis.delete(key):
                    cleaned += 1
            return cleaned
        except Exception as e:
            logging.error(f"만료 데이터 정리 중 오류 발생: {e}")
            return 0

    def clear_all(self, node_id: str = None) -> int:
        try:
            pattern = f"node:{'*' if node_id is None else node_id}:*"
            deleted = 0
            for key in self.redis.scan_iter(match=pattern):
                if self.redis.delete(key):
                    deleted += 1
            return deleted
        except Exception as e:
            logging.error(f"데이터 삭제 중 오류 발생: {e}")
            return 0
