
class QMTLError(Exception):
    """QMTL 시스템의 기본 예외."""


class NodeFaultError(QMTLError):
    """노드 장애/에러 발생 예외."""
    def __init__(self, node_id: str, message: str = None, code: str = None):
        self.node_id = node_id
        self.message = message or f"Node fault detected: {node_id}"
        self.code = code
        super().__init__(self.message)


class DataConsistencyError(QMTLError):
    """데이터 정합성 오류/중복 실행/손실 방지 예외."""
    def __init__(self, node_id: str = None, message: str = None):
        self.node_id = node_id
        self.message = message or (f"Data consistency error on node: {node_id}" if node_id else "Data consistency error")
        super().__init__(self.message)


class DatabaseError(QMTLError):
    """데이터베이스 관련 예외."""


class ValidationError(QMTLError):
    """유효성 검사 실패 예외."""


class NotFoundError(QMTLError):
    """리소스 미발견 예외."""


class AuthError(QMTLError):
    """인증/인가 실패 예외."""


class HTTPError(QMTLError):
    """HTTP 통신 예외."""

    status_code: int = 500
    detail: str = "Internal Server Error"

    def __init__(self, detail: str = None, status_code: int = 500):
        self.detail = detail or self.detail
        self.status_code = status_code
        super().__init__(self.detail)


class StrategyNotFoundError(NotFoundError):
    """전략을 찾을 수 없을 때 발생하는 예외."""


class PipelineExecutionError(QMTLError):
    """파이프라인 실행 중 발생하는 예외."""


class StatusServiceError(QMTLError):
    """상태 서비스 관련 예외."""


class CyclicDependencyError(QMTLError):
    """순환 의존성 감지 시 발생하는 예외."""


class RegistryServiceError(QMTLError):
    """Registry 서비스 관련 예외."""


class RegistryClientError(QMTLError):
    """Registry 클라이언트 사용 중 발생하는 예외."""


class RegistryConnectionError(RegistryClientError):
    """Registry 서비스 연결 실패 예외."""
