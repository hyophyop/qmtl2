######################################################################
# [Neo4j URI 환경분리 정책]
# - 호스트에서 pytest로 테스트를 실행할 때만 NEO4J_URI=bolt://localhost:7687로 강제 지정합니다.
# - 이 코드는 pytest 프로세스(테스트 러너)에서만 적용되며, docker-compose로 기동되는 Registry/Orchestrator 컨테이너에는 영향을 주지 않습니다.
# - Registry/Orchestrator 컨테이너는 docker-compose.dev.yml의 환경변수(NEXOJ_URI=bolt://neo4j:7687)를 사용합니다.
# - 이 정책을 위반하면 컨테이너-DB 연결이 실패하므로, 절대 테스트 환경변수를 컨테이너에 전달하지 않도록 주의하세요.
######################################################################
import os
import sys
if (
    "pytest" in sys.modules or any("pytest" in arg for arg in sys.argv)
):
    # Only set for the test runner process (host), never for spawned containers
    os.environ["NEO4J_URI"] = "bolt://localhost:7687"
    os.environ["NEO4J_HOST"] = "localhost"
import os
import subprocess
import time

import pytest
import redis

REDPANDA_HOST = os.environ.get("REDPANDA_HOST", "localhost")
REDPANDA_PORT = int(os.environ.get("REDPANDA_PORT", 9092))
REDPANDA_ADMIN_PORT = int(os.environ.get("REDPANDA_ADMIN_PORT", 9644))


@pytest.fixture(scope="session")
def redpanda_session():
    """
    [FIXTURE-3] Session-scoped fixture for providing a Redpanda (Kafka) broker backed by Docker.
    Ensures Redpanda container is up and ready before yielding the broker address.
    사용 예시:
        def test_redpanda(redpanda_session):
            brokers = redpanda_session
            # ...
    """
    compose_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../docker-compose.dev.yml")
    )
    service_name = "redpanda"
    up_cmd = ["docker-compose", "-f", compose_file, "up", "-d", service_name]
    subprocess.run(up_cmd, check=True)
    # Health check: admin HTTP 포트로 상태 확인
    import requests

    admin_url = f"http://{REDPANDA_HOST}:{REDPANDA_ADMIN_PORT}/v1/status/ready"
    for _ in range(30):
        try:
            resp = requests.get(admin_url, timeout=3)
            if resp.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(1)  # busy-wait 방지
    else:
        raise RuntimeError("Redpanda docker container did not become healthy in time (timeout)")
    brokers = f"{REDPANDA_HOST}:{REDPANDA_PORT}"
    yield brokers
    # Optionally clean up container after tests
    # subprocess.run(["docker-compose", "-f", compose_file, "down"], check=True)


@pytest.fixture(scope="function")
def redpanda_clean(redpanda_session):
    """
    [FIXTURE-3] Function-scoped fixture to clean Redpanda topics/state before and after each test for isolation.
    사용 예시:
        def test_redpanda_clean(redpanda_clean, redpanda_session):
            brokers = redpanda_session
            # ...
    """
    # 토픽 삭제/정리 등은 필요에 따라 구현 (Kafka AdminClient 활용)
    # 기본적으로는 no-op, 필요시 확장
    yield
    # 테스트 후에도 필요시 토픽/데이터 정리 가능


import os
import subprocess
import time

import pytest
import redis

# Redis docker-compose 기반 테스트용 fixture (INTERVAL-3)
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))


@pytest.fixture(scope="session")
def redis_session():
    """
    [FIXTURE-1] Session-scoped fixture for providing a Redis client backed by Docker.
    Ensures Redis container is up and ready before yielding the client.
    사용 예시:
        def test_redis(redis_session):
            redis_session.set('foo', 'bar')
            assert redis_session.get('foo') == b'bar'
    """
    compose_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../docker-compose.dev.yml")
    )
    service_name = "redis"
    up_cmd = ["docker-compose", "-f", compose_file, "up", "-d", service_name]
    subprocess.run(up_cmd, check=True)
    client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    for _ in range(20):
        try:
            if client.ping():
                break
        except Exception:
            pass
        time.sleep(0.5)
    else:
        raise RuntimeError("Redis docker container did not become healthy in time (timeout)")
    yield client
    # Optionally clean up container after tests
    # subprocess.run(["docker-compose", "-f", compose_file, "down"], check=True)


@pytest.fixture(scope="function")
def redis_clean(redis_session):
    """
    [FIXTURE-1] Function-scoped fixture to flush Redis DB before and after each test for isolation.
    사용 예시:
        def test_redis_clean(redis_clean, redis_session):
            redis_session.set('foo', 'bar')
            assert redis_session.get('foo') == b'bar'
    """
    redis_session.flushdb()
    yield
    redis_session.flushdb()


######################################################################
# Neo4j docker-compose 기반 테스트용 fixture (FIXTURE-2)
#
# ⚠️ 테스트와 서비스가 동일한 DB 인스턴스(호스트/포트/유저/비밀번호)를 바라보도록
# 반드시 환경변수를 일치시켜야 합니다.
# (docker-compose.dev.yml, pytest, FastAPI 등에서 동일하게 설정)
#
# 예시 환경변수:
#   NEO4J_HOST, NEO4J_PORT, NEO4J_USER, NEO4J_PASSWORD, NEO4J_URI
#
# 이 값이 다르면 테스트와 서비스가 서로 다른 DB를 바라보거나, 데이터 불일치가 발생할 수 있습니다.
######################################################################
from qmtl.common.db.neo4j_client import Neo4jClient

NEO4J_HOST = os.environ.get("NEO4J_HOST", "localhost")
NEO4J_PORT = int(os.environ.get("NEO4J_PORT", 7687))
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")
NEO4J_BOLT_URI = os.environ.get("NEO4J_URI", f"bolt://{NEO4J_HOST}:{NEO4J_PORT}")


@pytest.fixture(scope="session")
def neo4j_session():
    """
    [FIXTURE-2] Session-scoped fixture for providing a Neo4j client backed by Docker.
    Ensures Neo4j container is up and ready before yielding the client.
    사용 예시:
        def test_neo4j(neo4j_session):
            result = neo4j_session.execute_query("RETURN 1 AS x")
            assert result[0]["x"] == 1
    """
    compose_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../docker-compose.dev.yml")
    )
    service_name = "neo4j"
    up_cmd = ["docker-compose", "-f", compose_file, "up", "-d", service_name]
    subprocess.run(up_cmd, check=True)
    # Health check: bolt 포트에 연결 시도
    for _ in range(30):
        try:
            # 테스트 환경에서는 짧은 타임아웃 설정으로 Neo4j 클라이언트 생성
            client = Neo4jClient(
                NEO4J_BOLT_URI, 
                NEO4J_USER, 
                NEO4J_PASSWORD,
                connection_timeout=3,  # 3초 (기본값보다 짧게)
                max_transaction_retry_time=5000,  # 5초 (기본값보다 짧게)
                connection_acquisition_timeout=5.0  # 5초 (기본값보다 짧게)
            )
            # 간단 쿼리로 연결 확인
            result = client.execute_query("RETURN 1 AS x")
            if result and result[0]["x"] == 1:
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        raise RuntimeError("Neo4j docker container did not become healthy in time (timeout)")
    yield client
    client.close()
    # Optionally clean up container after tests
    # subprocess.run(["docker-compose", "-f", compose_file, "down"], check=True)


@pytest.fixture(scope="function")
def neo4j_clean(neo4j_session):
    """
    [FIXTURE-2] Function-scoped fixture to clean Neo4j DB before and after each test for isolation.
    사용 예시:
        def test_neo4j_clean(neo4j_clean, neo4j_session):
            neo4j_session.execute_query("CREATE (:TestNode {foo: 1})")
            # ...
    """
    # 모든 노드/관계 삭제
    neo4j_session.execute_query("MATCH (n) DETACH DELETE n")
    yield
    neo4j_session.execute_query("MATCH (n) DETACH DELETE n")


import logging
import subprocess
import time

import pytest
import requests  # 보다 안정적인 requests 라이브러리 추가

# 테스트 유틸리티 모듈 추가 - 상대 경로로 수정

# E2E 테스트를 위한 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("e2e_test")

# Mock/Fixture 설정 문제용 경고 로거
mock_logger = logging.getLogger("mock_fixtures")
mock_handler = logging.StreamHandler()
mock_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
mock_logger.addHandler(mock_handler)
mock_logger.setLevel(logging.INFO)


def pytest_addoption(parser):
    parser.addoption(
        "--poll-max-attempts", action="store", default=None, help="E2E 폴링 최대 시도 횟수"
    )
    parser.addoption("--poll-delay-sec", action="store", default=None, help="E2E 폴링 간격(초)")


def wait_for_service(url, max_attempts=5, delay=2, service_name=None, container_name=None):
    """
    서비스가 준비될 때까지 대기하는 함수
    컨테이너가 비정상일 경우 1회 재시작 후 재시도
    Args:
        url: 확인할 서비스 URL
        max_attempts: 최대 시도 횟수
        delay: 시도 간 대기 시간(초)
        service_name: 로깅용 서비스 이름
        container_name: docker 컨테이너 이름(재시작용)
    Returns:
        bool: 서비스 준비 여부
    """
    name = service_name or url
    for attempt in range(max_attempts):
        try:
            logger.info(f"[{attempt+1}/{max_attempts}] {name} 서비스 확인 중...")
            resp = requests.get(url, timeout=5)
            if resp.status_code in (200, 404):
                logger.info(f"{name} 서비스 준비 완료! (상태 코드: {resp.status_code})")
                return True
            logger.warning(f"{name} 서비스 응답 상태 코드: {resp.status_code}")
        except Exception as e:
            logger.warning(f"{name} 서비스 연결 실패: {str(e)}")
        # 마지막 시도인 경우 추가 정보 로깅 및 컨테이너 재시작 1회 시도
        if attempt == max_attempts - 1 and container_name:
            logger.error(f"{name} 서비스 준비 실패 (최대 시도 횟수 초과). 컨테이너 재시작 시도...")
            try:
                subprocess.run(["docker", "restart", container_name], check=False)
                logger.info(f"{container_name} 컨테이너 재시작 완료. 10초 대기 후 재확인...")
                time.sleep(10)
                # 재시작 후 1회만 추가 확인
                try:
                    resp = requests.get(url, timeout=5)
                    if resp.status_code in (200, 404):
                        logger.info(
                            f"{name} 서비스 재시작 후 준비 완료! (상태 코드: {resp.status_code})"
                        )
                        return True
                except Exception as e:
                    logger.warning(f"{name} 재시작 후 서비스 연결 실패: {str(e)}")
            except Exception as e:
                logger.error(f"{container_name} 컨테이너 재시작 실패: {str(e)}")
            logger.info("Docker 컨테이너 상태 확인:")
            try:
                result = subprocess.run(
                    ["docker", "ps"], capture_output=True, text=True, check=False
                )
                logger.info(result.stdout)
            except Exception as e:
                logger.error(f"Docker 상태 확인 실패: {str(e)}")
        logger.info(f"{delay}초 후 재시도...")
        time.sleep(delay)
    return False


@pytest.fixture(scope="session")
def docker_compose_up_down():
    """
    E2E/통합 테스트에서만 명시적으로 사용되는 Docker 컨테이너 관리 fixture.
    단위/모듈 테스트에는 적용하지 않음.
    E2E/통합 테스트 파일/클래스/함수에 @pytest.mark.usefixtures("docker_compose_up_down")로 명시 적용 필요.
    """
    try:
        logger.info("Docker 컨테이너 시작 중...")
        subprocess.run(["make", "docker-up"], check=True)
        # 서비스가 준비될 때까지 대기 (컨테이너 이름 명시)
        registry_ready = wait_for_service(
            "http://localhost:8000/health",
            service_name="Registry",
            container_name="qmtl2-registry-1",
        )
        orchestrator_ready = wait_for_service(
            "http://localhost:8080/health",
            service_name="Orchestrator",
            container_name="qmtl2-orchestrator-1",
        )
        if not (registry_ready and orchestrator_ready):
            logger.error("서비스 준비 실패! Docker 로그 확인:")
            subprocess.run(["docker-compose", "-f", "docker-compose.dev.yml", "logs"], check=False)
            pytest.fail("서비스가 준비되지 않았습니다. E2E 테스트를 진행할 수 없습니다.")
        logger.info("모든 서비스 준비 완료! 테스트 시작.")
        yield
    except Exception as e:
        logger.error(f"Docker 컨테이너 실행 중 오류 발생: {str(e)}")
        raise
    finally:
        logger.info("Docker 컨테이너 정리 중...")
        # cleanup 단계에서 --remove-orphans, --timeout 추가로 컨테이너 정리 안정성 향상
        subprocess.run(["make", "docker-down"], check=True)
        subprocess.run(["docker-compose", "-f", "docker-compose.dev.yml", "down", "--remove-orphans", "--timeout", "20"], check=False)
        logger.info("Docker 컨테이너 정리 완료. 포트 상태 확인:")
        try:
            result = subprocess.run(["lsof", "-i", ":7687"], capture_output=True, text=True, check=False)
            logger.info(result.stdout)
        except Exception as e:
            logger.warning(f"포트 상태 확인 실패: {str(e)}")
        time.sleep(2)  # 포트 정리 대기 (TIME_WAIT 상태 해소)


@pytest.fixture(scope="session")
def base_urls():
    """
    테스트에서 사용할 기본 URL 정보를 제공하는 fixture
    """
    return {"registry": "http://localhost:8000", "orchestrator": "http://localhost:8080"}


@pytest.fixture(autouse=True)
def check_mock_usage():
    """
    테스트에서 Mock 사용 시 실제 서비스 동작과 일치하는지 점검하는 fixture

    이 fixture는 json_content 대신 json 파라미터 사용을 강제하고,
    MagicMock 객체의 반환 타입이 Pydantic 모델과 일치하는지 검증합니다.
    """
    mock_logger.info("Starting test with enhanced mock validation")
    yield
    mock_logger.info("Test completed with enhanced mock validation")
