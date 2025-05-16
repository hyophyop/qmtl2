"""
Redis 클라이언트 및 연결 관리 모듈 (INTERVAL-3)
- 싱글턴/풀 방식 지원
- 환경설정(Pydantic v2) 연동
- 연결 예외 처리 및 ping 테스트 함수 포함
"""

from typing import Optional

import redis

from src.qmtl.models.config import RedisSettings


class RedisClient:
    def save_history(
        self, node_id: str, interval: str, value, max_items: int = 100, ttl: Optional[int] = None
    ) -> None:
        """
        노드별/인터벌별 히스토리 데이터 저장 (리스트 push, TTL/max_items 관리)
        key: node:{node_id}:history:{interval}
        """
        key = f"node:{node_id}:history:{interval}"
        pipe = self.conn.pipeline()
        pipe.lpush(key, value)
        pipe.ltrim(key, 0, max_items - 1)
        if ttl:
            pipe.expire(key, ttl)
        pipe.execute()

    def get_history(self, node_id: str, interval: str, count: int = 100):
        """
        노드별/인터벌별 히스토리 데이터 조회 (최신순)
        """
        key = f"node:{node_id}:history:{interval}"
        return self.conn.lrange(key, 0, count - 1)

    def delete_history(self, node_id: str, interval: str) -> int:
        """
        노드별/인터벌별 히스토리 데이터 삭제
        """
        key = f"node:{node_id}:history:{interval}"
        return self.conn.delete(key)

    _instance: Optional["RedisClient"] = None
    _connection: Optional[redis.Redis] = None
    _settings: Optional[RedisSettings] = None

    def __new__(cls, settings: Optional[RedisSettings] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            if settings is not None:
                cls._settings = settings
            else:
                raise ValueError("RedisSettings must be provided on first init")
            cls._connection = redis.Redis(
                host=cls._settings.host,
                port=cls._settings.port,
                db=cls._settings.db,
                password=cls._settings.password,
                decode_responses=True,
                socket_timeout=cls._settings.socket_timeout,
            )
        return cls._instance

    @property
    def conn(self) -> redis.Redis:
        if self._connection is None:
            raise RuntimeError("Redis connection is not initialized")
        return self._connection

    def ping(self) -> bool:
        try:
            return self.conn.ping()
        except redis.RedisError as e:
            raise ConnectionError(f"Redis connection failed: {e}")

    def set(self, key: str, value, ex: Optional[int] = None):
        return self.conn.set(key, value, ex=ex)

    def get(self, key: str):
        return self.conn.get(key)
