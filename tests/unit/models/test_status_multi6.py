# docker_compose_up_down autouse 우회: 단위 테스트에서만 적용
import sys
if 'tests.conftest' in sys.modules:
    sys.modules['tests.conftest'].docker_compose_up_down = lambda: None
# docker_compose_up_down fixture 우회: 이 파일은 단위(Pydantic) 테스트만 포함
import pytest
# 테스트: 장애 복구 및 데이터 정합성 보장 (MULTI-6)
import pytest
from datetime import datetime, timedelta
from qmtl.models.status import NodeStatus, NodeErrorDetail, PipelineStatus
from qmtl.common.errors.exceptions import NodeFaultError, DataConsistencyError


def test_node_status_error_detail():
    now = datetime.utcnow()
    err = NodeErrorDetail(
        code="E1001",
        message="Test node failure",
        occurred_at=now,
        recovered_at=now + timedelta(minutes=1),
        recovery_count=1,
        extra={"trace": "stacktrace..."}
    )
    status = NodeStatus(
        node_id="abcd1234abcd1234abcd1234abcd1234",
        status="FAILED",
        error_detail=err,
        last_recovered_at=now + timedelta(minutes=1),
        recovery_count=1
    )
    assert status.status == "FAILED"
    assert status.error_detail.code == "E1001"
    assert status.error_detail.recovery_count == 1
    assert status.last_recovered_at is not None
    assert status.recovery_count == 1


def test_pipeline_status_error_detail():
    now = datetime.utcnow()
    err = NodeErrorDetail(
        code="P2001",
        message="Pipeline error",
        occurred_at=now
    )
    status = PipelineStatus(
        pipeline_id="abcd1234abcd1234abcd1234abcd1234",
        status="FAILED",
        params={},
        start_time=now,
        last_update=now,
        error_detail=err,
        last_recovered_at=None,
        recovery_count=0
    )
    assert status.status == "FAILED"
    assert status.error_detail.code == "P2001"
    assert status.error_detail.message == "Pipeline error"


def test_node_fault_error_exception():
    with pytest.raises(NodeFaultError) as exc:
        raise NodeFaultError(node_id="abcd1234abcd1234abcd1234abcd1234", message="Node crashed", code="E9999")
    assert "Node crashed" in str(exc.value)
    assert exc.value.code == "E9999"


def test_data_consistency_error_exception():
    with pytest.raises(DataConsistencyError) as exc:
        raise DataConsistencyError(node_id="abcd1234abcd1234abcd1234abcd1234", message="Duplicate execution detected")
    assert "Duplicate execution" in str(exc.value)
