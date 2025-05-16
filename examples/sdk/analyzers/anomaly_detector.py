from qmtl.sdk.analyzer import Analyzer
from qmtl.sdk.node import QueryNode, Node
import numpy as np

class AnomalyDetector(Analyzer):
    """
    FEATURE 태그 노드들의 값에서 평균+N*표준편차 이상/이하를 이상치로 감지하는 예제 분석기
    """
    def __init__(self, threshold: float = 3.0):
        super().__init__(name="anomaly_detector", tags=["ANOMALY"])
        self.threshold = threshold
        feature_query = QueryNode(
            name="feature_inputs",
            tags=["FEATURE"],
            interval="1d",
            period="7d"
        )
        self.add_query_node(feature_query)
        self.add_node(Node(
            name="anomaly_detection",
            tags=["ANALYZER", "ANOMALY"],
            fn=self._detect_anomaly,
            upstreams=[feature_query.name]
        ))

    def _detect_anomaly(self, feature_data_dict):
        results = {}
        for node_id, data in feature_data_dict.items():
            values = data.get("value", data) if isinstance(data, dict) else data
            arr = np.array(values)
            mean = np.mean(arr)
            std = np.std(arr)
            anomalies = np.where((arr > mean + self.threshold * std) | (arr < mean - self.threshold * std))[0].tolist()
            results[node_id] = {
                "mean": float(mean),
                "std": float(std),
                "anomaly_indices": anomalies,
                "count": len(arr)
            }
        return {"anomaly_report": results, "threshold": self.threshold}
