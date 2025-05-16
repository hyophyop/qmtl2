from qmtl.sdk.analyzer import Analyzer
from qmtl.sdk.node import QueryNode, Node
import pandas as pd

class CorrelationAnalyzer(Analyzer):
    """
    FEATURE 태그 노드들의 상관관계 행렬을 계산하는 예제 분석기
    """
    def __init__(self):
        super().__init__(name="feature_correlation", tags=["CORRELATION"])
        feature_query = QueryNode(
            name="feature_inputs",
            tags=["FEATURE"],
            interval="1d",
            period="14d"
        )
        self.add_query_node(feature_query)
        self.add_node(Node(
            name="correlation_matrix",
            tags=["ANALYZER", "CORRELATION"],
            fn=self._calculate_correlation,
            upstreams=[feature_query.name]
        ))

    def _calculate_correlation(self, feature_data_dict):
        all_data = pd.DataFrame()
        for node_id, data in feature_data_dict.items():
            all_data[node_id] = data.get("value", data) if isinstance(data, dict) else data
        correlation_matrix = all_data.corr()
        return {
            "correlation_matrix": correlation_matrix.to_dict(),
            "feature_count": len(feature_data_dict),
            "period": "14d"
        }
