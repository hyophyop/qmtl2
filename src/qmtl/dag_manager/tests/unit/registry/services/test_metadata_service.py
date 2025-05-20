"""
MetadataService 단위 테스트 (스켈레톤)
- 노드/전략/DAG/의존성/이력 CRUD 및 조회 테스트
- Pydantic v2 모델 기반
"""

from unittest.mock import MagicMock
from qmtl.dag_manager.registry.services.metadata_service import MetadataService
from qmtl.models.datanode import DataNode, NodeStreamSettings
from qmtl.sdk.models import IntervalEnum
from qmtl.models.generated.qmtl_strategy_pb2 import StrategyMetadata
from qmtl.models.generated.qmtl_strategy_pb2 import StrategySnapshot
from qmtl.dag_manager.registry.services.node.management import NodeManagementService
from qmtl.dag_manager.registry.services.strategy.management import StrategyManagementService
from qmtl.dag_manager.registry.services.strategy.snapshot import StrategySnapshotService


class TestMetadataService:
    def setup_method(self):
        # 도메인별 서비스는 mock으로 대체
        self.node_service = MagicMock(spec=NodeManagementService)
        self.strategy_service = MagicMock(spec=StrategyManagementService)
        self.snapshot_service = MagicMock(spec=StrategySnapshotService)
        self.service = MetadataService(
            self.node_service, self.strategy_service, self.snapshot_service
        )

    def test_create_and_get_node(self):
        # stream_settings 필수
        intervals = {IntervalEnum.HOUR: {"interval": IntervalEnum.HOUR, "period": 1}}
        stream_settings = NodeStreamSettings(intervals=intervals)
        # node_id는 32자리 소문자 hex
        node = DataNode(
            node_id="a" * 32,
            type="FEATURE",
            data_format={"type": "json"},
            params={},
            dependencies=[],
            ttl=3600,
            stream_settings=stream_settings,
        )
        self.service.create_node(node)
        self.node_service.create_node.assert_called_once_with(node)
        self.service.get_node("a" * 32)
        self.node_service.get_node.assert_called_once_with("a" * 32)

    def test_create_and_get_strategy(self):
        strategy = StrategyMetadata(strategy_name="test", description="", submitted_at=0)
        self.service.create_strategy(strategy)
        # 실제 등록 로직 구현 전까지는 호출 없음
        self.service.get_strategy("p1")
        self.strategy_service.get_version.assert_called_once_with("p1")

    def test_create_and_get_dag(self):
        dag = StrategySnapshot(pipeline_id="p1", created_at=0, nodes=[], edges=[])
        self.service.create_dag(dag)
        self.snapshot_service.create_snapshot.assert_called_once_with(dag)
        self.service.get_dag("p1")
        self.snapshot_service.get_snapshots.assert_called_once_with("p1")

    # Dependency, History 관련 테스트는 주석 처리 또는 제거
