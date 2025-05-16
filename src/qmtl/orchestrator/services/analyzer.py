"""
AnalyzerService: 분석기 등록/조회/활성화/결과조회 비즈니스 로직
"""

import time
import uuid
from typing import Dict, Optional

from qmtl.models.analyzer import (
    AnalyzerActivateRequest,
    AnalyzerDefinition,
    AnalyzerMetadata,
    AnalyzerResult,
)


class AnalyzerService:
    """분석기 관련 서비스 계층 (임시 인메모리 구현)"""

    _analyzers: Dict[str, AnalyzerMetadata] = {}
    _results: Dict[str, AnalyzerResult] = {}

    @classmethod
    def register_analyzer(cls, definition: AnalyzerDefinition) -> AnalyzerMetadata:
        analyzer_id = str(uuid.uuid4())
        now = int(time.time())
        meta = AnalyzerMetadata(
            analyzer_id=analyzer_id,
            name=definition.name,
            description=definition.description,
            tags=definition.tags,
            created_at=now,
            status="REGISTERED",
            parameters=definition.parameters,
        )
        cls._analyzers[analyzer_id] = meta
        return meta

    @classmethod
    def get_analyzer(cls, analyzer_id: str) -> Optional[AnalyzerMetadata]:
        return cls._analyzers.get(analyzer_id)

    @classmethod
    def activate_analyzer(cls, analyzer_id: str, req: AnalyzerActivateRequest) -> AnalyzerMetadata:
        meta = cls._analyzers.get(analyzer_id)
        if not meta:
            raise ValueError("Analyzer not found")
        meta.status = "ACTIVE"
        cls._analyzers[analyzer_id] = meta
        # 임시: 활성화 시점에 결과도 생성
        result = AnalyzerResult(
            analyzer_id=analyzer_id,
            result={"message": "Dummy analysis result"},
            generated_at=int(time.time()),
            status="SUCCESS",
            error=None,
        )
        cls._results[analyzer_id] = result
        return meta

    @classmethod
    def get_results(cls, analyzer_id: str) -> Optional[AnalyzerResult]:
        return cls._results.get(analyzer_id)
