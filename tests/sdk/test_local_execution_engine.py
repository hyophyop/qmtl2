# pytest: test
"""
Unit tests for LocalExecutionEngine in qmtl.sdk.execution.local
"""
import time
import pytest
from qmtl.sdk.execution.local import LocalExecutionEngine

class DummyNode:
    def __init__(self, name, fn, upstreams=None):
        self.name = name
        self.fn = fn
        self.upstreams = upstreams or []
        self.stream_settings = None
        self.interval_settings = None
    def execute(self, inputs):
        return self.fn(**inputs) if inputs else self.fn()

def test_execute_pipeline_basic():
    engine = LocalExecutionEngine(debug=True)
    class DummyPipeline:
        def __init__(self):
            self.name = "p1"
            self.nodes = {
                "A": DummyNode("A", lambda: 1),
                "B": DummyNode("B", lambda A: A + 1, upstreams=["A"]),
            }
            self.execution_order = ["A", "B"]
            self._topological_sort = lambda: self.execution_order
    pipeline = DummyPipeline()
    results = engine.execute_pipeline(pipeline)
    assert results["A"] == 1
    assert results["B"] == 2

def test_execute_pipeline_with_inputs():
    engine = LocalExecutionEngine()
    class DummyPipeline:
        def __init__(self):
            self.name = "p2"
            self.nodes = {
                "X": DummyNode("X", lambda x: x * 2),
            }
            self.execution_order = ["X"]
            self._topological_sort = lambda: self.execution_order
    pipeline = DummyPipeline()
    results = engine.execute_pipeline(pipeline, inputs={"X": 10})
    assert results["X"] == 10  # 입력값이 있으면 그대로 사용

def test_save_and_get_interval_data():
    engine = LocalExecutionEngine()
    engine.save_interval_data("n1", "1d", 123, max_items=2, ttl=1)
    data = engine.get_interval_data("n1", "1d")
    assert data[0]["value"] == 123
    # 만료 테스트
    time.sleep(1.1)
    engine._cleanup_expired_data()
    data2 = engine.get_interval_data("n1", "1d")
    assert data2 == []

def test_clear_cache():
    engine = LocalExecutionEngine()
    engine.save_interval_data("n2", "1d", 1)
    engine.save_interval_data("n2", "1h", 2)
    engine.clear_cache(node_id="n2", interval="1d")
    assert engine.get_interval_data("n2", "1d") == []
    assert engine.get_interval_data("n2", "1h") != []
    engine.clear_cache(node_id="n2")
    assert engine.get_interval_data("n2", "1h") == []

def test_get_node_metadata():
    engine = LocalExecutionEngine()
    engine.save_interval_data("n3", "1d", 100)
    meta = engine.get_node_metadata("n3")
    assert meta["node_id"] == "n3"
    assert "1d" in meta["intervals"]
