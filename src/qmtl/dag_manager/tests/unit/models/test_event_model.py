# filepath: tests/unit/models/test_event_model.py
from qmtl.models.event import NodeStatusEvent, PipelineStatusEvent, AlertEvent, EventType
from datetime import datetime

def test_node_status_event():
    event = NodeStatusEvent(node_id="n1", status="RUNNING")
    assert event.event_type == EventType.NODE_STATUS
    assert event.node_id == "n1"
    assert event.status == "RUNNING"
    assert isinstance(event.timestamp, datetime)

def test_pipeline_status_event():
    event = PipelineStatusEvent(pipeline_id="p1", status="COMPLETED")
    assert event.event_type == EventType.PIPELINE_STATUS
    assert event.pipeline_id == "p1"
    assert event.status == "COMPLETED"
    assert isinstance(event.timestamp, datetime)

def test_alert_event():
    event = AlertEvent(target_id="n1", message="Test alert")
    assert event.event_type == EventType.ALERT
    assert event.target_id == "n1"
    assert event.message == "Test alert"
    assert event.level == "INFO"
    assert isinstance(event.timestamp, datetime)
