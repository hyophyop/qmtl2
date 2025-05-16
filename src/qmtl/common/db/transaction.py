"""Neo4j 트랜잭션 관리 모듈.

이 모듈은 트랜잭션 단위의 작업을 안전하게 처리할 수 있도록 도와줍니다.
"""

from typing import Any, Callable, Dict, List

from neo4j import Transaction

from qmtl.common.errors.exceptions import DatabaseError


def run_in_transaction(
    tx: Transaction, work_function: Callable[[Transaction], List[Dict[str, Any]]], *args, **kwargs
) -> List[Dict[str, Any]]:
    """트랜잭션 내에서 작업 함수 실행 및 예외 처리.

    Args:
        tx: Neo4j 트랜잭션 객체
        work_function: 트랜잭션 내에서 실행할 함수
        *args, **kwargs: 작업 함수에 전달할 추가 인자
    Returns:
        작업 함수의 반환값(List[Dict[str, Any]])
    Raises:
        DatabaseError: 트랜잭션 내 예외 발생 시
    """
    try:
        return work_function(tx, *args, **kwargs)
    except Exception as e:
        raise DatabaseError(f"트랜잭션 작업 실패: {str(e)}")
