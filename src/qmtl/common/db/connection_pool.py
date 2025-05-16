"""Neo4j 연결 풀 관리 모듈.

이 모듈은 Neo4j 데이터베이스 연결을 효율적으로 관리하기 위한 연결 풀을 제공합니다.
"""

import threading
from contextlib import contextmanager
from typing import List, Optional

from qmtl.common.config.settings import get_settings
from qmtl.common.db.neo4j_client import Neo4jClient
from qmtl.common.errors.exceptions import DatabaseError


class Neo4jConnectionPool:
    """Neo4j 데이터베이스 연결 풀 관리 클래스."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """싱글톤 패턴 구현."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        max_size: int = 10,
    ):
        """Neo4j 연결 풀 초기화.

        Args:
            uri: Neo4j 데이터베이스 URI (예: bolt://localhost:7687)
            username: 인증 사용자명
            password: 인증 비밀번호
            max_size: 풀의 최대 크기
        """
        if self._initialized and uri is None and username is None and password is None:
            # 이미 초기화된 싱글톤 인스턴스의 경우 재초기화 방지
            return

        self._initialized = True
        self._uri = uri
        self._username = username
        self._password = password
        self._max_size = max_size
        self._pool: List[Neo4jClient] = []
        self._available = threading.Semaphore(max_size)
        self._lock = threading.RLock()

    def get_client(self) -> Neo4jClient:
        """연결 풀에서 Neo4j 클라이언트 획득.

        Returns:
            Neo4j 클라이언트 인스턴스

        Raises:
            DatabaseError: 연결 생성 실패 시
        """
        self._available.acquire()

        with self._lock:
            if not self._pool:
                try:
                    client = Neo4jClient(self._uri, self._username, self._password)
                    return client
                except Exception as e:
                    self._available.release()
                    raise DatabaseError(f"Neo4j 클라이언트 생성 실패: {str(e)}")
            else:
                return self._pool.pop()

    def release_client(self, client: Neo4jClient) -> None:
        """사용 완료된 클라이언트를 풀에 반환.

        Args:
            client: 반환할 Neo4j 클라이언트 인스턴스
        """
        with self._lock:
            self._pool.append(client)
        self._available.release()

    @contextmanager
    def client(self) -> Neo4jClient:
        """Neo4j 클라이언트를 컨텍스트 관리자로 제공.

        Yields:
            Neo4j 클라이언트 인스턴스
        """
        client = self.get_client()
        try:
            yield client
        finally:
            self.release_client(client)

    def close_all(self) -> None:
        """풀의 모든 연결 종료."""
        with self._lock:
            for client in self._pool:
                client.close()
            self._pool.clear()

    def __del__(self):
        """소멸자에서 열린 연결 정리."""
        self.close_all()


# 글로벌 Neo4j 연결 풀 인스턴스
_neo4j_pool = None


def get_neo4j_pool() -> Neo4jConnectionPool:
    """
    글로벌 Neo4j 연결 풀 인스턴스 반환 (싱글톤 패턴)

    Returns:
        Neo4j 연결 풀 인스턴스
    """
    global _neo4j_pool
    if _neo4j_pool is None:
        settings = get_settings()
        _neo4j_pool = Neo4jConnectionPool(
            uri=settings.env.neo4j_uri,
            username=settings.env.neo4j_user,
            password=settings.env.neo4j_password,
        )
    return _neo4j_pool
