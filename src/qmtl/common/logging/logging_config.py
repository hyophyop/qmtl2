import sys

import structlog
from loguru import logger

# Loguru 기본 설정
logger.remove()
logger.add(sys.stderr, level="INFO", format="[{time:YYYY-MM-DD HH:mm:ss}] [{level}] {message}")

# structlog와 연동
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


def get_logger(name: str = None):
    """서비스별 표준 로거 반환 (structlog 래퍼)"""
    return structlog.get_logger(name) if name else structlog.get_logger()
