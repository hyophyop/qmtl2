"""
MetadataService: Registry 메타데이터(노드/전략/DAG/의존성/이력) 관리 서비스
- 모든 엔티티/관계의 식별자는 정책 Node ID, Pipeline ID만 사용
- Neo4j 기반 엔티티/관계 관리, Pydantic v2 모델 기반 데이터 구조 강제
- 서비스 계층의 SoC, 타입 일관성, 테스트 용이성 보장
"""
from typing import List, Optional
from qmtl.models.datanode import DataNode
from qmtl.models.strategy import StrategyMetadata, StrategySnapshot
from qmtl.registry.services.node.management import NodeManagementService
from qmtl.registry.services.strategy.management import StrategyManagementService
from qmtl.registry.services.strategy.snapshot import StrategySnapshotService

class MetadataService:
    """
    Registry 메타데이터 관리의 진입점 서비스
    - 노드/전략/DAG/의존성/이력의 생성, 조회, 갱신, 삭제 및 관계 관리
    - 각 도메인 서비스(node, strategy 등)와 연동
    """
    def __init__(
        self,
        node_service: NodeManagementService,
        strategy_service: StrategyManagementService,
        snapshot_service: StrategySnapshotService,
    ):
        self.node_service = node_service
        self.strategy_service = strategy_service
        self.snapshot_service = snapshot_service

    def create_node(self, node: DataNode) -> None:
        """노드 생성 및 Neo4j 등록"""
        self.node_service.create_node(node)

    def get_node(self, node_id: str) -> Optional[DataNode]:
        """Node ID로 노드 조회"""
        return self.node_service.get_node(node_id)

    def update_node(self, node: DataNode) -> None:
        """노드 정보 갱신"""
        self.node_service.create_node(node)  # 보통 update는 upsert로 처리

    def delete_node(self, node_id: str) -> None:
        """노드 삭제"""
        self.node_service.delete_node(node_id)

    def create_strategy(self, strategy: StrategyMetadata) -> None:
        """전략 생성 및 등록"""
        # 실제 등록 로직에 맞게 구현 필요
        pass

    def get_strategy(self, pipeline_id: str) -> Optional[StrategyMetadata]:
        """Pipeline ID로 전략 조회"""
        return self.strategy_service.get_version(pipeline_id)

    def update_strategy(self, strategy: StrategyMetadata) -> None:
        """전략 정보 갱신"""
        # 실제 갱신 로직에 맞게 구현 필요
        pass

    def delete_strategy(self, pipeline_id: str) -> None:
        """전략 삭제"""
        # 실제 삭제 로직에 맞게 구현 필요
        pass

    def create_dag(self, dag: StrategySnapshot) -> None:
        """DAG 스냅샷 생성 및 등록"""
        self.snapshot_service.create_snapshot(dag)

    def get_dag(self, pipeline_id: str) -> Optional[StrategySnapshot]:
        """Pipeline ID로 DAG 조회"""
        snaps = self.snapshot_service.get_snapshots(pipeline_id)
        return snaps[0] if snaps else None

    def update_dag(self, dag: StrategySnapshot) -> None:
        """DAG 정보 갱신"""
        # 스냅샷은 불변이므로 update 대신 새로 생성
        self.snapshot_service.create_snapshot(dag)

    def delete_dag(self, pipeline_id: str) -> None:
        """DAG 삭제"""
        # 스냅샷 삭제 로직 필요시 구현
        pass

    # Dependency, History 관련 메서드는 주석 처리 또는 제거
    # def add_dependency(self, dependency: Dependency) -> None:
    #     """노드 간 의존성 추가"""
    #     # 의존성 추가 로직 필요시 구현
    #     pass

    # def remove_dependency(self, dependency: Dependency) -> None:
    #     """노드 간 의존성 제거"""
    #     # 의존성 제거 로직 필요시 구현
    #     pass

    # def get_history(self, node_id: str) -> List[HistoryRecord]:
    #     """이력 조회"""
    #     # 이력 조회 로직 필요시 구현
    #     return []

    # 기타 필요한 메타데이터 관리 메서드도 동일 패턴으로 위임/구현
