# Gateway Integration Tests

This directory contains end-to-end (E2E) integration tests for the Gateway service, focusing on the interaction between SDK, Gateway, and DAG Manager components.

## Test Scenarios

### 1. Protocol Buffer Serialization/Deserialization
- Round-trip serialization/deserialization of protocol buffer messages
- Schema validation and version compatibility
- Data integrity verification

### 2. Authentication & Authorization
- JWT token-based authentication
- Role-based access control (RBAC)
- Permission validation for protected resources

### 3. Data Node Management
- CRUD operations for data nodes
- Schema validation
- Node metadata management

### 4. Strategy Management
- Strategy registration and lifecycle management
- Strategy metadata validation
- Status tracking and updates

### 5. Error Handling
- Invalid input validation
- Error response formats
- Edge case handling

## Docker 기반 통합 테스트 자동화

이 프로젝트의 E2E/통합 테스트는 주요 서비스(Gateway, Neo4j, Redis, Redpanda 등)를 모두 docker-compose 기반 pytest fixture로 자동 기동/정리합니다.

### 주요 서비스별 fixture
- `gateway_session`: Gateway 컨테이너 자동 관리 (base_url 반환)
- `neo4j_session`: Neo4j 컨테이너 자동 관리 (Neo4j client 반환)
- `redis_session`: Redis 컨테이너 자동 관리 (Redis client 반환)
- `redpanda_session`: Redpanda 컨테이너 자동 관리 (broker 주소 반환)

### 사용 예시
```python
import pytest
import requests

@pytest.mark.usefixtures("gateway_session", "neo4j_session", "redis_session")
def test_e2e_example(gateway_session, neo4j_session, redis_session):
    # Gateway health check
    resp = requests.get(f"{gateway_session}/api/v1/health")
    assert resp.status_code == 200
    # Neo4j, Redis 등도 동일하게 활용 가능
```

### 통합 테스트 실행
```bash
pytest tests/e2e/
```

- 별도 docker-compose up/down 명령 없이, pytest가 자동으로 컨테이너 상태를 관리합니다.
- 각 서비스별 fixture는 session scope로 최초 1회만 기동/정리됩니다.

## Test Coverage

Current test coverage focuses on:
- Protocol buffer message integrity
- API contract validation
- Authentication and authorization flows
- Basic CRUD operations

## Adding New Tests

When adding new test cases, please follow these guidelines:
1. Group related test cases in the same file
2. Use descriptive test function names
3. Include docstrings explaining the test scenario
4. Use fixtures for common test data
5. Follow the Arrange-Act-Assert pattern
6. Include error case testing

## Debugging

To debug tests, use the following pytest flags:
```bash
# Stop on first failure
pytest -x

# Show output from test execution
pytest -s

# Run with debug logging
pytest --log-cli-level=DEBUG
```

## CI Integration

These tests are automatically run in the CI/CD pipeline. Any failures will block the deployment process.
