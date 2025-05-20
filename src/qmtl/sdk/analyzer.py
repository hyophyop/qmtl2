"""
Analyzer classes for QMTL SDK pipelines.

This module provides the Analyzer class for tag-based automatic analysis of nodes.
"""

from typing import Any, Dict, List, Optional

from qmtl.sdk.models import QueryNodeResultSelector
from qmtl.sdk.pipeline import Pipeline


# 기존 Analyzer 추상 클래스 정의를 먼저 둠 (상속 순서 오류 방지)
class Analyzer(Pipeline):
    """
    태그 기반 자동 분석기 파이프라인의 추상 인터페이스.
    (예제 분석기 구현은 파일 하단 참조)
    """

    def __init__(self, name: str, **kwargs):
        # 분석기 태그 자동 추가
        kwargs.setdefault("analyzer_type", "custom")
        super().__init__(name, **kwargs)
        self.tags = ["ANALYZER"]
        if "tags" in kwargs:
            self.tags.extend(kwargs["tags"])

    def execute(
        self,
        local: bool = True,
        registry_client=None,
        selectors: Optional[Dict[str, List["QueryNodeResultSelector"]]] = None,
        inputs: Optional[dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        import time

        from qmtl.models.analyzer import AnalyzerResult

        results: Dict[str, Any] = {}
        analyzer_results: List[AnalyzerResult] = []
        if self.query_nodes and local:
            for qn in self.query_nodes.values():
                matched_nodes = self.find_nodes_by_query(qn)
                # selectors 인자가 있으면 우선 적용, 없으면 쿼리노드의 result_selectors 적용
                selectors_to_apply = None
                if selectors and qn.name in selectors:
                    selectors_to_apply = selectors[qn.name]
                elif hasattr(qn, "result_selectors") and qn.result_selectors:
                    selectors_to_apply = qn.result_selectors
                if selectors_to_apply:
                    matched_nodes = self.apply_selectors(matched_nodes, selectors_to_apply)
                node_results = {}
                for node in matched_nodes:
                    try:
                        node_result = node.execute(inputs=inputs or {})
                        node_results[node.name] = node_result
                        analyzer_results.append(
                            AnalyzerResult(
                                analyzer_id=self.name,
                                result={
                                    "query_node": qn.name,
                                    "node": node.name,
                                    "value": node_result,
                                },
                                generated_at=int(time.time()),
                                status="SUCCESS",
                            )
                        )
                    except Exception as e:
                        node_results[node.name] = f"ERROR: {e}"
                        analyzer_results.append(
                            AnalyzerResult(
                                analyzer_id=self.name,
                                result={"query_node": qn.name, "node": node.name, "error": str(e)},
                                generated_at=int(time.time()),
                                status="FAIL",
                                error=str(e),
                            )
                        )
                results[qn.name] = node_results
            self.results_cache = results.copy()
            self.analyzer_results = analyzer_results.copy()
            return results
        return super().execute(local=local, registry_client=registry_client, **kwargs)

    def to_definition(self) -> Dict[str, Any]:
        result = super().to_definition()
        result["type"] = "analyzer"
        result["tags"] = self.tags
        return result

    def __repr__(self) -> str:
        return f"Analyzer(name='{self.name}', tags={self.tags}, nodes={list(self.nodes.keys())})"
