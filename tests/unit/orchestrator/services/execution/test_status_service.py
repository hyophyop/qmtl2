from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time

from qmtl.models.datanode import DataNode
from qmtl.models.status import StatusType
from qmtl.orchestrator.services.execution.status_service import StatusService


@pytest.fixture
def mock_nodes():
    nodes = []
    for i in range(1, 4):
        node = MagicMock(spec=DataNode)
        node.node_id = f"node-{i}"

        # node-1은 의존성 없음 (루트 노드)
        # node-2는 node-1에 의존
        # node-3는 node-2에 의존
        if i == 1:
            node.dependencies = []
        elif i == 2:
            node.dependencies = ["node-1"]
        else:
            node.dependencies = ["node-2"]

        nodes.append(node)
    return nodes


@pytest.fixture
def status_service():
    return StatusService()


@pytest.fixture
def initialized_status_service(status_service, mock_nodes):
    pipeline_id = "test-pipeline-123"
    params = {"param1": "value1"}
    status_service.initialize_pipeline(pipeline_id, mock_nodes, params)
    return status_service, pipeline_id


class TestStatusService:
    """StatusService 테스트"""

    def test_initialize_pipeline(self, status_service, mock_nodes):
        """파이프라인 상태 초기화 테스트"""
        # Given
        pipeline_id = "test-pipeline-123"
        params = {"param1": "value1"}
        # When
        status_service.initialize_pipeline(pipeline_id, mock_nodes, params)
        # Then
        pipeline_status = status_service.get_pipeline_status(pipeline_id)
        assert pipeline_status is not None
        assert pipeline_status["pipeline_id"] == pipeline_id
        assert pipeline_status["status"] == StatusType.PENDING
        assert pipeline_status["params"] == params
        assert pipeline_status["progress"] == 0.0
        # 노드 상태 확인
        for node in mock_nodes:
            node_status = status_service.get_node_status(pipeline_id, node.node_id)
            assert node_status is not None
            assert node_status["node_id"] == node.node_id
            assert node_status["status"] == StatusType.PENDING
            assert node_status["start_time"] is None
            assert node_status["end_time"] is None
            assert node_status["result"] is None

    def test_update_pipeline_status(self, initialized_status_service):
        """파이프라인 상태 업데이트 테스트"""
        # Given
        status_service, pipeline_id = initialized_status_service
        result = {"test": "result_data"}

        # When
        status_service.update_pipeline_status(pipeline_id, StatusType.RUNNING)

        # Then
        pipeline_status = status_service.get_pipeline_status(pipeline_id)
        assert pipeline_status["status"] == StatusType.RUNNING

        # When (완료 상태로 업데이트)
        status_service.update_pipeline_status(pipeline_id, StatusType.COMPLETED, result)

        # Then
        pipeline_status = status_service.get_pipeline_status(pipeline_id)
        assert pipeline_status["status"] == StatusType.COMPLETED
        assert pipeline_status["result"] == result
        assert pipeline_status["end_time"] is not None
        assert pipeline_status["progress"] == 100.0

    def test_update_pipeline_status_invalid_pipeline(self, status_service):
        """존재하지 않는 파이프라인 상태 업데이트 테스트"""
        # Given
        invalid_pipeline_id = "non-existent-pipeline"

        # When/Then
        with pytest.raises(ValueError):
            status_service.update_pipeline_status(invalid_pipeline_id, StatusType.RUNNING)

    def test_update_node_status(self, initialized_status_service):
        """노드 상태 업데이트 테스트"""
        # Given
        status_service, pipeline_id = initialized_status_service
        node_id = "node-1"
        result = {"data": "node_result"}

        # When
        status_service.update_node_status(pipeline_id, node_id, StatusType.RUNNING)

        # Then
        node_status = status_service.get_node_status(pipeline_id, node_id)
        assert node_status["status"] == StatusType.RUNNING
        assert node_status["start_time"] is not None

        # When (완료 상태로 업데이트)
        status_service.update_node_status(pipeline_id, node_id, StatusType.COMPLETED, result)

        # Then
        node_status = status_service.get_node_status(pipeline_id, node_id)
        assert node_status["status"] == StatusType.COMPLETED
        assert node_status["result"] == result
        assert node_status["end_time"] is not None

        # 파이프라인 진행률 확인
        pipeline_status = status_service.get_pipeline_status(pipeline_id)
        # 3개 노드 중 1개 완료 = 33.3%
        assert pipeline_status["progress"] > 30 and pipeline_status["progress"] < 35

    def test_update_node_status_invalid_pipeline(self, status_service):
        """존재하지 않는 파이프라인의 노드 상태 업데이트 테스트"""
        # Given
        invalid_pipeline_id = "non-existent-pipeline"

        # When/Then
        with pytest.raises(ValueError):
            status_service.update_node_status(invalid_pipeline_id, "node-1", StatusType.RUNNING)

    def test_update_node_status_invalid_node(self, initialized_status_service):
        """존재하지 않는 노드 상태 업데이트 테스트"""
        # Given
        status_service, pipeline_id = initialized_status_service
        invalid_node_id = "non-existent-node"

        # When/Then
        with pytest.raises(ValueError):
            status_service.update_node_status(pipeline_id, invalid_node_id, StatusType.RUNNING)

    def test_get_pipeline_status_invalid_pipeline(self, status_service):
        """존재하지 않는 파이프라인 상태 조회 테스트"""
        # Given
        invalid_pipeline_id = "non-existent-pipeline"

        # When
        result = status_service.get_pipeline_status(invalid_pipeline_id)

        # Then
        assert result is None

    def test_get_node_status_invalid_pipeline(self, status_service):
        """존재하지 않는 파이프라인의 노드 상태 조회 테스트"""
        # Given
        invalid_pipeline_id = "non-existent-pipeline"

        # When
        result = status_service.get_node_status(invalid_pipeline_id, "node-1")

        # Then
        assert result is None

    def test_get_node_status_invalid_node(self, initialized_status_service):
        """존재하지 않는 노드 상태 조회 테스트"""
        # Given
        status_service, pipeline_id = initialized_status_service
        invalid_node_id = "non-existent-node"

        # When
        result = status_service.get_node_status(pipeline_id, invalid_node_id)

        # Then
        assert result is None

    def test_get_all_node_statuses(self, initialized_status_service):
        """모든 노드 상태 조회 테스트"""
        # Given
        status_service, pipeline_id = initialized_status_service

        # When
        all_statuses = status_service.get_all_node_statuses(pipeline_id)

        # Then
        assert len(all_statuses) == 3
        assert "node-1" in all_statuses
        assert "node-2" in all_statuses
        assert "node-3" in all_statuses

    def test_cleanup_pipeline(self, initialized_status_service):
        """파이프라인 상태 정리 테스트"""
        # Given
        status_service, pipeline_id = initialized_status_service

        # 상태가 제대로 초기화되었는지 확인
        assert status_service.get_pipeline_status(pipeline_id) is not None
        assert status_service.get_all_node_statuses(pipeline_id) is not None

        # When
        status_service.cleanup_pipeline(pipeline_id)

        # Then
        assert status_service.get_pipeline_status(pipeline_id) is None
        assert status_service.get_all_node_statuses(pipeline_id) == {}

    def test_cleanup_old_pipelines(self, status_service, mock_nodes):
        """오래된 파이프라인 상태 정리 테스트"""
        # Given
        # 현재 시간 파이프라인
        pipeline1 = "pipeline-current"
        status_service.initialize_pipeline(pipeline1, mock_nodes)

        # 오래된 파이프라인
        pipeline2 = "pipeline-old"
        status_service.initialize_pipeline(pipeline2, mock_nodes)

        # 오래된 파이프라인의 마지막 업데이트 시간을 과거로 설정
        # freezegun을 사용하여 시간을 25시간 전으로 변경 후 업데이트
        with freeze_time(datetime.now() - timedelta(hours=25)):
            status_service.update_pipeline_status(pipeline2, StatusType.COMPLETED)

        # When
        # 기본 24시간보다 오래된 파이프라인 정리
        deleted_count = status_service.cleanup_old_pipelines()

        # Then
        assert deleted_count == 1
        assert status_service.get_pipeline_status(pipeline1) is not None  # 현재 파이프라인은 유지
        assert status_service.get_pipeline_status(pipeline2) is None  # 오래된 파이프라인은 삭제
