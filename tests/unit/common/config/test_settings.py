from qmtl.common.config.settings import load_settings
from qmtl.models.config import Settings


def test_load_settings_default(monkeypatch):
    monkeypatch.delenv("QMTL_ENV", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.setenv("NEO4J_URI", "bolt://test:7687")
    monkeypatch.setenv("REDIS_URI", "redis://test:6379")
    s = load_settings()
    assert isinstance(s, Settings)
    assert s.env.neo4j_uri == "bolt://test:7687"
    assert s.env.redis_uri == "redis://test:6379"
    assert s.env.env == "dev"


def test_load_settings_env(monkeypatch):
    monkeypatch.setenv("QMTL_ENV", "prod")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    s = load_settings()
    assert s.env.env == "prod"
    assert s.env.debug is True
    assert s.env.log_level == "DEBUG"
