# Protobuf 기반 분석기 모델로 마이그레이션됨
# 필요시 protos/analyzer.proto 및 generated 코드 import
# from qmtl.models.generated import analyzer_pb2

# 기존 Pydantic 모델은 모두 protobuf 메시지로 대체됨

# 임시: AnalyzerResult 모킹 (실제 구현 필요)
class AnalyzerResult:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

# 임시: AnalyzerActivateRequest 모킹 (실제 구현 필요)
class AnalyzerActivateRequest:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

# 임시: AnalyzerDefinition 모킹 (실제 구현 필요)
class AnalyzerDefinition:
    def __init__(self, name, description=None, tags=None, parameters=None):
        self.name = name
        self.description = description
        self.tags = tags or []
        self.parameters = parameters or {}

# 임시: AnalyzerMetadata 모킹 (실제 구현 필요)
class AnalyzerMetadata:
    def __init__(self, analyzer_id, name, description, tags, created_at, status, parameters):
        self.analyzer_id = analyzer_id
        self.name = name
        self.description = description
        self.tags = tags
        self.created_at = created_at
        self.status = status
        self.parameters = parameters