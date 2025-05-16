from qmtl.common.config.env import get_env_vars
from qmtl.models.config import EnvConfig, Settings

SETTINGS_ENV_KEY = "QMTL_ENV"

# 글로벌 설정 객체 (싱글톤 패턴)
_settings = None


def load_settings() -> Settings:
    """환경 변수 기반 Settings 동적 로딩 (Pydantic v2 스타일)"""
    env_vars = get_env_vars()
    env = env_vars.get(SETTINGS_ENV_KEY, env_vars.get("ENV", "dev"))
    env_config = EnvConfig(
        env=env,
        debug=env_vars.get("DEBUG", "false").lower() == "true",
        log_level=env_vars.get("LOG_LEVEL", "INFO"),
        neo4j_uri=env_vars.get("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user=env_vars.get("NEO4J_USER", "neo4j"),
        neo4j_password=env_vars.get("NEO4J_PASSWORD", "password"),
        redis_uri=env_vars.get("REDIS_URI", "redis://localhost:6379"),
        kafka_brokers=env_vars.get("KAFKA_BROKERS", "localhost:9092"),
        neo4j_database=env_vars.get("NEO4J_DATABASE", "neo4j"),
    )
    return Settings(env=env_config)


def get_settings() -> Settings:
    """
    싱글톤 패턴으로 설정 객체 반환
    매번 환경 변수를 다시 로드하지 않고 캐시된 설정 객체 사용
    """
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def reset_settings() -> None:
    """테스트 등에서 설정 객체 초기화가 필요한 경우 사용"""
    global _settings
    _settings = None
