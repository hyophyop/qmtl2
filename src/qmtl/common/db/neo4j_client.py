"""Neo4j 클라이언트 모듈.

이 모듈은 Neo4j 그래프 데이터베이스와의 상호작용을 위한 클라이언트를 제공합니다.
Pydantic v2 모델을 활용하여 타입 안전성을 보장합니다.
"""

from typing import Any, Callable, Dict, List, Optional, TypeVar

from neo4j import Driver, GraphDatabase, Transaction
from pydantic import BaseModel

from qmtl.common.errors.exceptions import DatabaseError

T = TypeVar("T", bound=BaseModel)


class Neo4jClient:
    """Neo4j 데이터베이스와 상호작용하기 위한 클라이언트 클래스."""

    def __init__(
        self, 
        uri: str, 
        username: str, 
        password: str,
        connection_timeout: int = 5,  # 5초 연결 타임아웃 (기본값: 30초)
        max_transaction_retry_time: int = 10000,  # 10초 트랜잭션 재시도 (기본값: 30초)
        connection_acquisition_timeout: float = 10.0  # 10초 연결 획득 타임아웃 (기본값: 60초)
    ):
        """Neo4j 클라이언트 초기화.

        Args:
            uri: Neo4j 데이터베이스 URI (예: bolt://localhost:7687)
            username: 인증 사용자명
            password: 인증 비밀번호
            connection_timeout: 연결 타임아웃 (초)
            max_transaction_retry_time: 트랜잭션 재시도 최대 시간 (밀리초)
            connection_acquisition_timeout: 연결 획득 타임아웃 (초)
        """
        try:
            self._driver = GraphDatabase.driver(
                uri, 
                auth=(username, password),
                connection_timeout=connection_timeout,
                max_transaction_retry_time=max_transaction_retry_time,
                connection_acquisition_timeout=connection_acquisition_timeout
            )
        except Exception as e:
            raise DatabaseError(f"Neo4j 연결 실패: {str(e)}")

    def close(self) -> None:
        """Neo4j 드라이버 연결 종료."""
        if hasattr(self, "_driver"):
            self._driver.close()

    def get_driver(self) -> Driver:
        """Neo4j 드라이버 인스턴스 반환.

        Returns:
            Neo4j 드라이버 인스턴스
        """
        return self._driver

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Cypher 쿼리 실행.

        Args:
            query: 실행할 Cypher 쿼리
            parameters: 쿼리 매개변수 (기본값: None)
            database: 사용할 데이터베이스 (기본값: None, 기본 데이터베이스 사용)

        Returns:
            쿼리 결과 목록

        Raises:
            DatabaseError: 쿼리 실행 중 오류 발생 시
        """
        parameters = parameters or {}

        try:
            with self._driver.session(database=database) as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
        except Exception as e:
            raise DatabaseError(f"쿼리 실행 실패: {str(e)}")

    def execute_with_model(
        self,
        query: str,
        model_class: type[T],
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
    ) -> List[T]:
        """Cypher 쿼리를 실행하고 결과를 Pydantic 모델로 변환.

        Args:
            query: 실행할 Cypher 쿼리
            model_class: 결과를 변환할 Pydantic 모델 클래스
            parameters: 쿼리 매개변수 (기본값: None)
            database: 사용할 데이터베이스 (기본값: None, 기본 데이터베이스 사용)

        Returns:
            Pydantic 모델 인스턴스 목록

        Raises:
            DatabaseError: 쿼리 실행 또는 모델 변환 오류 발생 시
        """
        raw_results = self.execute_query(query, parameters, database)

        try:
            return [model_class.model_validate(item) for item in raw_results]
        except Exception as e:
            raise DatabaseError(f"모델 변환 실패: {str(e)}")

    def execute_transaction(
        self,
        work_function: Callable[[Transaction], List[Dict[str, Any]]],
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """트랜잭션 내에서 작업 실행.

        Args:
            work_function: 트랜잭션 객체를 사용하는 작업 함수
            database: 사용할 데이터베이스 (기본값: None, 기본 데이터베이스 사용)

        Returns:
            작업 함수의 반환 결과

        Raises:
            DatabaseError: 트랜잭션 실행 중 오류 발생 시
        """
        try:
            with self._driver.session(database=database) as session:
                return session.execute_write(work_function)
        except Exception as e:
            raise DatabaseError(f"트랜잭션 실행 실패: {str(e)}")

    def execute_transaction_with_model(
        self,
        work_function: Callable[[Transaction], List[Dict[str, Any]]],
        model_class: type[T],
        database: Optional[str] = None,
    ) -> List[T]:
        """트랜잭션 내에서 작업을 실행하고 결과를 Pydantic 모델로 변환.

        Args:
            work_function: 트랜잭션 객체를 사용하는 작업 함수
            model_class: 결과를 변환할 Pydantic 모델 클래스
            database: 사용할 데이터베이스 (기본값: None, 기본 데이터베이스 사용)

        Returns:
            Pydantic 모델 인스턴스 목록

        Raises:
            DatabaseError: 트랜잭션 실행 또는 모델 변환 오류 발생 시
        """
        raw_results = self.execute_transaction(work_function, database)

        try:
            return [model_class.model_validate(item) for item in raw_results]
        except Exception as e:
            raise DatabaseError(f"모델 변환 실패: {str(e)}")

    def __enter__(self):
        """컨텍스트 관리자 진입."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 관리자 종료."""
        self.close()
