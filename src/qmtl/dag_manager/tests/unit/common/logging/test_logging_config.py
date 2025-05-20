from qmtl.common.logging.logging_config import get_logger


def test_get_logger_returns_structlog_logger():
    logger = get_logger("test")
    assert hasattr(logger, "info")
    assert hasattr(logger, "bind")
    logger.info("test log", foo=1)
