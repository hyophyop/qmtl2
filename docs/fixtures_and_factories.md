# Pytest Fixtures & Factory 클래스 문서 (DAG Manager)

본 문서는 QMTL DAG Manager의 테스트 코드에서 사용하는 주요 fixture, factory/dummy 클래스의 역할과 사용법을 정리합니다.

---

## 1. DummyRedis

- **역할**: 실제 Redis 서버 없이, 메모리 기반으로 Redis의 list/hash 연산을 흉내내는 테스트 double
- **위치**: `tests/unit/core/test_queue_repository.py`, `test_queue_worker.py` 등
- **주요 메서드**:
  - `lpush(key, value)`, `brpoplpush(src, dest, timeout)`, `lrem(key, num, value)`
  - `hset(key, field, value)`, `hget(key, field)`
  - `expire(key, ttl)`, `list_contents(key)`
- **활용 예시**:
  ```python
  dummy_redis = DummyRedis()
  repo = RedisQueueRepository(redis_client=dummy_redis)
  repo.push("item1")
  assert "item1" in dummy_redis.list_contents(repo.queue_key)
  ```

## 2. DummyNodeService

- **역할**: Neo4j 등 외부 DB 없이, 메모리 내 노드 리스트만 반환하는 NodeManagementService 대체 double
- **위치**: `tests/unit/core/test_graph_builder.py`, `test_ready_node_selector.py`, `test_queue_worker.py` 등
- **주요 메서드**:
  - `get_strategy_nodes(strategy_version_id)`
- **활용 예시**:
  ```python
  node_service = DummyNodeService([n1, n2, n3])
  builder = GraphBuilder(node_service)
  dag_service, topo = builder.build_strategy_dag("v1")
  ```

## 3. DummyStatusService

- **역할**: 실제 StatusService(싱글톤, lock, pydantic/protobuf 등) 대신, dict 기반으로 노드 상태를 관리하는 테스트 double
- **위치**: `tests/unit/core/test_queue_worker.py` 등
- **주요 메서드**:
  - `get_node_status(pipeline_id, node_id)`
  - `update_node_status(pipeline_id, node_id, status, result=None)`
- **활용 예시**:
  ```python
  status_service = DummyStatusService({("p1", n1.node_id): "COMPLETED"})
  status_service.update_node_status("p1", n2.node_id, "READY")
  assert status_service.get_node_status("p1", n2.node_id)["status"] == "READY"
  ```

---

## 4. Fixture/Factory 설계 원칙
- 외부 의존성(Neo4j, Redis, 실제 StatusService 등) 없이 순수 Python 객체로 테스트 가능해야 함
- 각 테스트 파일 내에서 직접 정의하거나, `conftest.py`/공용 모듈로 분리 가능
- 실제 서비스 객체와 동일한 인터페이스(메서드 시그니처) 유지 권장
- 상태/큐/노드 등은 dict/list 등 표준 자료구조로 단순화

---

## 5. 확장/공유 전략
- 공통 dummy/factory는 `tests/conftest.py` 또는 `tests/factories/`로 이동하여 재사용성 강화 가능
- 복잡한 시나리오(예: 상태 전이, 큐 동기화 등)는 fixture+factory 조합으로 계층화
- 실제 서비스와의 통합 테스트에서는 별도 mock/patch 전략 병행 