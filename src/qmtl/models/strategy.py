# Protobuf 기반 전략 스냅샷 모델로 마이그레이션됨
# 필요시 protos/strategy_snapshot.proto 및 generated 코드 import
from qmtl.models.generated import qmtl_strategy_pb2

# 기존 Pydantic 모델은 모두 protobuf 메시지로 대체됨
