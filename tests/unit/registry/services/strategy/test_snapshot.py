import pytest
import json
from qmtl.models.strategy import StrategySnapshot
from qmtl.registry.services.strategy.snapshot import StrategySnapshotService


@pytest.fixture
def mock_neo4j_pool():
    class DummyClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def execute_query(self, cypher, params, database):
            if hasattr(self, "_force_return"):
                return self._force_return
            # pipeline_id 정책에 맞춘 mock 동작
            if "CREATE (s:StrategySnapshot" in cypher:
                return [{"snapshot_id": params["snapshot_id"]}]
            if "MATCH (s:StrategySnapshot {pipeline_id: $pipeline_id})" in cypher:
                # 조회 mock: 2개 스냅샷 반환
                return [
                    {
                        "s": {
                            "pipeline_id": params["pipeline_id"],
                            "created_at": 1111,
                            "nodes": json.dumps([]),
                            "edges": json.dumps([]),
                            "metadata": json.dumps({}),
                        }
                    },
                    {
                        "s": {
                            "pipeline_id": params["pipeline_id"],
                            "created_at": 2222,
                            "nodes": json.dumps([]),
                            "edges": json.dumps([]),
                            "metadata": json.dumps({}),
                        }
                    },
                ]
            if (
                "MATCH (s:StrategySnapshot {snapshot_id: $snapshot_id, pipeline_id: $pipeline_id})"
                in cypher
            ):
                # 롤백 mock: 단일 스냅샷 반환
                return [
                    {
                        "s": {
                            "pipeline_id": params["pipeline_id"],
                            "created_at": 3333,
                            "nodes": json.dumps([]),
                            "edges": json.dumps([]),
                            "metadata": json.dumps({}),
                        }
                    }
                ]
            return []

    class DummyPool:
        def __init__(self):
            self.client_instance = DummyClient()

        def client(self):
            return self.client_instance

    return DummyPool()


@pytest.fixture
def service(mock_neo4j_pool):
    return StrategySnapshotService(mock_neo4j_pool, database="testdb")


def test_create_snapshot(service):
    snap = StrategySnapshot(
        pipeline_id="v1",
        created_at=1234,
        nodes=[],
        edges=[],
        metadata={"foo": "bar"},
    )
    snapshot_id = service.create_snapshot(snap)
    assert snapshot_id == "v1_1234"


def test_get_snapshots(service):
    snaps = service.get_snapshots("v1")
    assert len(snaps) == 2
    assert all(isinstance(s, StrategySnapshot) for s in snaps)


def test_rollback_to_snapshot(service):
    snap = service.rollback_to_snapshot("v1", "v1_3333")
    assert isinstance(snap, StrategySnapshot)
    assert snap.created_at == 3333


def test_get_snapshots_empty(service, monkeypatch):
    # 조회 결과가 없을 때
    dummy_client = service.neo4j_pool.client()
    dummy_client._force_return = []
    snaps = service.get_snapshots("notfound")
    assert snaps == []


def test_rollback_to_snapshot_none(service, monkeypatch):
    # 롤백 결과가 없을 때
    dummy_client = service.neo4j_pool.client()
    dummy_client._force_return = []
    snap = service.rollback_to_snapshot("v1", "notfound")
    assert snap is None
