from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from qmtl.models.datanode import DataNode, NodeStreamSettings, IntervalSettings
from qmtl.sdk.models import IntervalEnum
from qmtl.common.utils.serialization import to_str_map

# StatusType enum 대신 문자열 상수 사용
from qmtl.dag_manager.execution.status_service import StatusService
from qmtl.common.errors.exceptions import StatusServiceError


@pytest.fixture
def mock_nodes():
    stream_settings = NodeStreamSettings(
        intervals={IntervalEnum.HOUR: IntervalSettings(interval=IntervalEnum.HOUR, period=1)}
    )
    data_format = {"type": "csv"}
    nodes = [
        dict(
            node_id="00000000000000000000000000000001",
            dependencies=[],
            data_format=data_format,
            stream_settings=stream_settings,
        ),
        dict(
            node_id="00000000000000000000000000000002",
            dependencies=["00000000000000000000000000000001"],
            data_format=data_format,
            stream_settings=stream_settings,
        ),
        dict(
            node_id="00000000000000000000000000000003",
            dependencies=["00000000000000000000000000000002"],
            data_format=data_format,
            stream_settings=stream_settings,
        ),
    ]
    # 타입 검증
    for node_args in nodes:
        assert isinstance(node_args["stream_settings"], NodeStreamSettings)
        for k, v in node_args["stream_settings"].intervals.items():
            assert isinstance(k, IntervalEnum)
            assert isinstance(v, IntervalSettings)
    return [DataNode(**node_args) for node_args in nodes]


@pytest.fixture
def status_service():
    return StatusService()


@pytest.fixture
def initialized_status_service(status_service, mock_nodes):
    pipeline_id = "test-pipeline-123"
    params = {"param1": "value1"}
    status_service.initialize_pipeline(pipeline_id, mock_nodes, to_str_map(params))
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
        assert pipeline_status.pipeline_id == pipeline_id
        assert pipeline_status.status == "PENDING"
        assert dict(pipeline_status.params) == {k: str(v) for k, v in params.items()}
        assert pipeline_status.progress == 0.0
        # 노드 상태 확인
        for node in mock_nodes:
            node_status = status_service.get_node_status(pipeline_id, node.node_id)
            assert node_status is not None
            assert node_status.node_id == node.node_id
            assert node_status.status == "PENDING"
            assert node_status.start_time.seconds == 0  # default
            assert node_status.end_time.seconds == 0
            assert node_status.result == ""

    def test_update_pipeline_status(self, initialized_status_service):
        """파이프라인 상태 업데이트 테스트"""
        # Given
        status_service, pipeline_id = initialized_status_service
        result = {"test": "result_data"}
        # result는 dict(str, str)로 변환
        result = to_str_map(result)

        # When
        status_service.update_pipeline_status(pipeline_id, "RUNNING")

        # Then
        pipeline_status = status_service.get_pipeline_status(pipeline_id)
        assert pipeline_status.status == "RUNNING"

        # When (완료 상태로 업데이트)
        status_service.update_pipeline_status(pipeline_id, "COMPLETED", result)

        # Then
        pipeline_status = status_service.get_pipeline_status(pipeline_id)
        assert pipeline_status.status == "COMPLETED"
        # result는 dict(str, str)로 비교
        assert dict(pipeline_status.result) == result
        assert pipeline_status.end_time.seconds > 0
        assert pipeline_status.progress == 100.0

    def test_update_pipeline_status_invalid_pipeline(self, status_service):
        """존재하지 않는 파이프라인 상태 업데이트 테스트"""
        # Given
        invalid_pipeline_id = "non-existent-pipeline"

        # When/Then
        with pytest.raises(ValueError):
            status_service.update_pipeline_status(invalid_pipeline_id, "RUNNING")

    def test_update_node_status(self, initialized_status_service):
        """노드 상태 업데이트 테스트"""
        # Given
        status_service, pipeline_id = initialized_status_service
        node_id = "node-1"
        result = {"data": "node_result"}
        result = to_str_map(result)

        # When
        status_service.update_node_status(pipeline_id, node_id, "RUNNING")

        # Then
        node_status = status_service.get_node_status(pipeline_id, node_id)
        assert node_status.status == "RUNNING"
        assert node_status.start_time.seconds > 0

        # When (완료 상태로 업데이트)
        status_service.update_node_status(pipeline_id, node_id, "COMPLETED", result)

        # Then
        node_status = status_service.get_node_status(pipeline_id, node_id)
        assert node_status.status == "COMPLETED"
        assert dict(node_status.result) == result
        assert node_status.end_time.seconds > 0

        # 파이프라인 진행률 확인
        pipeline_status = status_service.get_pipeline_status(pipeline_id)
        # 3개 노드 중 1개 완료 = 33.3%
        assert pipeline_status.progress > 30 and pipeline_status.progress < 35

    def test_update_node_status_invalid_pipeline(self, status_service):
        """존재하지 않는 파이프라인의 노드 상태 업데이트 테스트"""
        # Given
        invalid_pipeline_id = "non-existent-pipeline"

        # When/Then
        with pytest.raises(ValueError):
            status_service.update_node_status(invalid_pipeline_id, "node-1", "RUNNING")

    def test_update_node_status_invalid_node(self, initialized_status_service):
        """존재하지 않는 노드 상태 업데이트 테스트"""
        # Given
        status_service, pipeline_id = initialized_status_service
        invalid_node_id = "non-existent-node"

        # When/Then
        with pytest.raises(ValueError):
            status_service.update_node_status(pipeline_id, invalid_node_id, "RUNNING")

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
            status_service.update_pipeline_status(pipeline2, "COMPLETED")

        # When
        # 기본 24시간보다 오래된 파이프라인 정리
        deleted_count = status_service.cleanup_old_pipelines()

        # Then
        assert deleted_count == 1
        assert status_service.get_pipeline_status(pipeline1) is not None  # 현재 파이프라인은 유지
        assert status_service.get_pipeline_status(pipeline2) is None  # 오래된 파이프라인은 삭제

    def test_initialize_pipeline_statusserviceerror(self, status_service, mock_nodes):
        """내부 예외 발생 시 StatusServiceError로 감싸서 raise되는지 테스트"""
        with patch.object(status_service, "_lock", side_effect=Exception("lock error")):
            with pytest.raises(StatusServiceError):
                status_service.initialize_pipeline("err-pipeline", mock_nodes)

    def test_update_pipeline_status_statusserviceerror(self, initialized_status_service):
        status_service, pipeline_id = initialized_status_service
        with patch.object(status_service, "pipelines", side_effect=Exception("db error")):
            with pytest.raises(StatusServiceError):
                status_service.update_pipeline_status(pipeline_id, "RUNNING")

    def test_update_node_status_statusserviceerror(self, initialized_status_service):
        status_service, pipeline_id = initialized_status_service
        with patch.object(status_service, "nodes", side_effect=Exception("db error")):
            with pytest.raises(StatusServiceError):
                status_service.update_node_status(pipeline_id, "node-1", "RUNNING")

    def test_update_node_status_with_function_name_and_tags(self, initialized_status_service):
        status_service, pipeline_id = initialized_status_service
        # function_name, tags 필드가 있는 mock node
        node_id = "node-1"
        status_service.nodes[pipeline_id][node_id].function_name = "test_func"
        status_service.nodes[pipeline_id][node_id].tags = ["tag1", "tag2"]
        status_service.update_node_status(pipeline_id, node_id, "RUNNING")
        node_status = status_service.get_node_status(pipeline_id, node_id)
        assert node_status.function_name == "test_func"
        assert node_status.tags == ["tag1", "tag2"]

    def test_update_pipeline_progress_zero_nodes(self, status_service):
        pipeline_id = "empty-pipeline"
        # 노드가 0개인 파이프라인 강제 등록
        status_service.pipelines[pipeline_id] = status_service.pipelines[
            next(iter(status_service.pipelines))
        ].__class__(
            pipeline_id=pipeline_id,
            status="PENDING",
            params={},
            start_time=datetime.now(),
            last_update=datetime.now(),
            progress=0.0,
        )
        status_service.nodes[pipeline_id] = {}
        # 예외 없이 정상 종료되는지 확인
        status_service._update_pipeline_progress(pipeline_id)
        assert status_service.pipelines[pipeline_id].progress == 0.0
