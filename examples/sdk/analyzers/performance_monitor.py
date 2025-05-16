from qmtl.sdk.analyzer import Analyzer
from qmtl.sdk.node import QueryNode, Node
import numpy as np

class PerformanceMonitor(Analyzer):
    """
    SIGNAL 태그 노드들의 최근 값 변화율을 집계하는 예제 분석기
    """
    def __init__(self):
        super().__init__(name="performance_monitor", tags=["PERFORMANCE"])
        signal_query = QueryNode(
            name="signal_inputs",
            tags=["SIGNAL"],
            interval="1d",
            period="7d"
        )
        self.add_query_node(signal_query)
        self.add_node(Node(
            name="performance_stats",
            tags=["ANALYZER", "PERFORMANCE"],
            fn=self._monitor_performance,
            upstreams=[signal_query.name]
        ))

    def _monitor_performance(self, signal_data_dict):
        stats = {}
        for node_id, data in signal_data_dict.items():
            values = data.get("value", data) if isinstance(data, dict) else data
            arr = np.array(values)
            if len(arr) < 2:
                stats[node_id] = {"change_rate": None, "count": len(arr)}
            else:
                change_rate = float((arr[-1] - arr[0]) / arr[0]) if arr[0] != 0 else None
                stats[node_id] = {"change_rate": change_rate, "count": len(arr)}
        return {"performance_report": stats}
