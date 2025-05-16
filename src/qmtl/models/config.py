from typing import Optional

from pydantic import BaseModel, field_validator


class RedisSettings(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    socket_timeout: int = 5
    model_config = {"extra": "ignore"}


class EnvConfig(BaseModel):
    env: str = "dev"  # dev, prod, test
    debug: bool = False
    log_level: str = "INFO"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_database: str = "neo4j"
    redis_uri: str = "redis://localhost:6379"
    kafka_brokers: str = "localhost:9092"
    redis: Optional[RedisSettings] = None

    @field_validator("env", mode="before")
    def env_lower(cls, v):
        return v.lower()

    model_config = {"extra": "ignore"}


class Settings(BaseModel):
    env: EnvConfig
    service_name: str = "qmtl"
    version: str = "0.1.0"

    model_config = {"extra": "ignore"}
