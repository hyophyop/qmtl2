import pytest
import subprocess
import time
import os


@pytest.fixture(scope="session", autouse=True)
def docker_compose():
    compose_file = "docker-compose.dev.yml"
    # 테스트 환경에서만 NEO4J_URI를 localhost로 오버라이드
    os.environ["NEO4J_URI"] = "bolt://localhost:7687"
    # 컨테이너 기동
    subprocess.run(["docker-compose", "-f", compose_file, "up", "-d"], check=True)
    # Neo4j가 뜰 때까지 간단히 대기 (실제 서비스라면 healthcheck polling 권장)
    time.sleep(10)
    yield
    # 테스트 종료 후 컨테이너 종료 및 정리
    subprocess.run(["docker-compose", "-f", compose_file, "down", "-v"], check=True)
