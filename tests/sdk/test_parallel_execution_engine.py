import sys
print("PYTHONPATH:", sys.path)

# pytest: test
"""
Unit tests for ParallelExecutionEngine in qmtl.sdk.execution.parallel_engine
"""
import pytest
from unittest.mock import MagicMock, patch
from qmtl.sdk.execution.parallel_engine import ParallelExecutionEngine

class DummyPipeline:
    def __init__(self):
        self.name = "p1"
        self.nodes = {"A": MagicMock(name="A"), "B": MagicMock(name="B")}
        self.execution_order = ["A", "B"]
        self._topological_sort = lambda: self.execution_order

def test_register_node_creates_topics():
    engine = ParallelExecutionEngine(brokers="dummy:9092")
    with patch("qmtl.sdk.topic.create_topic") as mock_create:
        input_topic, output_topic = engine.register_node("A", pipeline_name="p1")
        assert input_topic.startswith("qmtl.input.p1.")
        assert output_topic.startswith("qmtl.output.p1.")
        assert mock_create.call_count == 2

def test_prepare_pipeline_registers_all_nodes():
    engine = ParallelExecutionEngine(brokers="dummy:9092")
    with patch.object(engine, "register_node", wraps=engine.register_node) as mock_reg:
        pipeline = DummyPipeline()
        with patch("qmtl.sdk.topic.create_topic"):
            engine.prepare_pipeline(pipeline)
        assert mock_reg.call_count == len(pipeline.nodes)

def test_init_sets_fields():
    engine = ParallelExecutionEngine(brokers="dummy:9092", redis_uri="redis://dummy", max_workers=3)
    assert engine.brokers == "dummy:9092"
    assert engine.redis_uri == "redis://dummy"
    assert engine.max_workers == 3
    assert hasattr(engine, "stream")
    assert hasattr(engine, "state")
    assert hasattr(engine, "executor")
    assert engine.running is False
    assert isinstance(engine.node_topics, dict)
    assert isinstance(engine.tasks, list)
