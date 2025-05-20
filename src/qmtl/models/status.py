
# Protobuf 기반 모델로 마이그레이션됨
from qmtl.models.generated import qmtl_events_pb2

# 예시: NodeStatusEvent, PipelineStatusEvent 등 protobuf 메시지 사용
# 기존 Pydantic 모델은 모두 protobuf 메시지로 대체됨

# 변환 유틸 함수 예시 (필요시 확장)
def node_status_to_proto(node_id: str, status: str, timestamp: int, meta: dict = None) -> qmtl_events_pb2.NodeStatusEvent:
    event = qmtl_events_pb2.NodeStatusEvent(
        node_id=node_id,
        status=status,
        timestamp=timestamp,
    )
    if meta:
        for k, v in meta.items():
            event.meta[k] = str(v)
    return event

def pipeline_status_to_proto(pipeline_id: str, status: str, timestamp: int, meta: dict = None) -> qmtl_events_pb2.PipelineStatusEvent:
    event = qmtl_events_pb2.PipelineStatusEvent(
        pipeline_id=pipeline_id,
        status=status,
        timestamp=timestamp,
    )
    if meta:
        for k, v in meta.items():
            event.meta[k] = str(v)
    return event

# 기타 필요한 변환 함수 및 protobuf 메시지 import를 여기에 추가