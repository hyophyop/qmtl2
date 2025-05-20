"""
Unit tests for src/qmtl/sdk/execution/parallel_engine.py
커버리지 80% 달성을 위한 실제 단위/엣지케이스 테스트
"""
import asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.qmtl.sdk.execution.parallel_engine import ParallelExecutionEngine


class DummyPipeline:
    def __init__(self, nodes=None, name="testpipe"):
        self.nodes = nodes or {}
        self.name = name
        self.execution_order = list(self.nodes.keys())

    def _topological_sort(self):
        return list(self.nodes.keys())


class DummyNode:
    def __init__(self, name, upstreams=None, interval_settings=None):
        self.name = name
        self.upstreams = upstreams or []
        self.interval_settings = interval_settings or {}
        self.node_id = name

    def execute(self, inputs):
        return {"result": self.name, **inputs}


@patch("src.qmtl.sdk.execution.parallel_engine.StreamProcessor")
@patch("src.qmtl.sdk.execution.parallel_engine.StateManager")
def test_parallel_engine_init(mock_state, mock_stream):
    engine = ParallelExecutionEngine(brokers="b", redis_uri="r", max_workers=2)
    assert engine.brokers == "b"
    assert engine.redis_uri == "r"
    assert engine.max_workers == 2
    assert hasattr(engine, "stream")
    assert hasattr(engine, "state")


@patch("src.qmtl.sdk.execution.parallel_engine.topic")
def test_register_node_success(mock_topic):
    engine = ParallelExecutionEngine()
    mock_topic.get_input_topic.return_value = "in"
    mock_topic.get_output_topic.return_value = "out"
    mock_topic.create_topic.return_value = None
    in_topic, out_topic = engine.register_node("n1", "p1")
    assert in_topic == "in"
    assert out_topic == "out"
    assert engine.node_topics["n1"] == ("in", "out")


@patch("src.qmtl.sdk.execution.parallel_engine.topic")
def test_register_node_topic_create_fail(mock_topic):
    engine = ParallelExecutionEngine()
    mock_topic.get_input_topic.return_value = "in"
    mock_topic.get_output_topic.return_value = "out"
    mock_topic.create_topic.side_effect = [Exception("fail"), None]
    # Should not raise, just log warning
    in_topic, out_topic = engine.register_node("n2", "p2")
    assert in_topic == "in"
    assert out_topic == "out"


@patch("src.qmtl.sdk.execution.parallel_engine.topic")
def test_prepare_pipeline_registers_all_nodes(mock_topic):
    engine = ParallelExecutionEngine()
    pipeline = DummyPipeline(nodes={"a": DummyNode("a"), "b": DummyNode("b")})
    engine.register_node = MagicMock()
    engine.prepare_pipeline(pipeline)
    assert engine.register_node.call_count == 2


@patch("src.qmtl.sdk.execution.parallel_engine.StreamProcessor")
@patch("src.qmtl.sdk.execution.parallel_engine.StateManager")
def test_execute_pipeline_empty_pipeline(mock_state, mock_stream):
    engine = ParallelExecutionEngine()
    pipeline = DummyPipeline(nodes={})
    # Should not raise, should return empty dict
    result = engine.execute_pipeline(pipeline)
    assert result == {}


@patch("src.qmtl.sdk.execution.parallel_engine.StreamProcessor")
@patch("src.qmtl.sdk.execution.parallel_engine.StateManager")
def test_stop_sets_running_false(mock_state, mock_stream):
    engine = ParallelExecutionEngine()
    engine.running = True
    engine.stop()
    assert engine.running is False


@patch("src.qmtl.sdk.execution.parallel_engine.StreamProcessor")
@patch("src.qmtl.sdk.execution.parallel_engine.StateManager")
def test_execute_pipeline_with_nodes(mock_state, mock_stream):
    import asyncio
    node = DummyNode("n1", interval_settings={"1d": {"period": "1d", "max_history": 1}})
    pipeline = DummyPipeline(nodes={"n1": node})
    engine = ParallelExecutionEngine()
    engine.prepare_pipeline = MagicMock()
    engine.state.get_history.return_value = [{"value": 42}]
    # Patch event loop to use a real loop and patch run_until_complete
    real_loop = asyncio.new_event_loop()
    def fake_run_until_complete(coro):
        return {"n1": 42}
    real_loop.run_until_complete = fake_run_until_complete
    with patch("asyncio.get_event_loop", side_effect=RuntimeError):
        with patch("asyncio.new_event_loop", return_value=real_loop):
            result = engine.execute_pipeline(pipeline)
            assert result == {"n1": 42}
    real_loop.close()


@pytest.mark.asyncio
@patch("src.qmtl.sdk.execution.parallel_engine.StreamProcessor")
@patch("src.qmtl.sdk.execution.parallel_engine.StateManager")
async def test__execute_node_async_no_upstreams(mock_state, mock_stream):
    engine = ParallelExecutionEngine()
    engine.node_topics = {"n1": ("in", "out")}
    engine.running = False  # Should exit loop immediately
    node = DummyNode("n1")
    pipeline = DummyPipeline(nodes={"n1": node})
    # Patch stream.publish to check call
    engine.stream.publish = MagicMock()
    await engine._execute_node_async(node, pipeline)
    # publish should not be called since running is False
    engine.stream.publish.assert_not_called()


@pytest.mark.asyncio
@patch("src.qmtl.sdk.execution.parallel_engine.StreamProcessor")
@patch("src.qmtl.sdk.execution.parallel_engine.StateManager")
async def test__execute_node_async_with_exception(mock_state, mock_stream):
    engine = ParallelExecutionEngine()
    engine.node_topics = {"n1": ("in", "out")}
    engine.running = True
    node = DummyNode("n1")
    pipeline = DummyPipeline(nodes={"n1": node})
    # Patch node.execute to raise
    node.execute = MagicMock(side_effect=Exception("fail"))
    # Patch stream.publish to check call
    engine.stream.publish = MagicMock()
    # Patch asyncio.sleep to fast-forward
    with patch("asyncio.sleep", new=AsyncMock()):
        # Should not raise
        await engine._execute_node_async(node, pipeline)
    engine.stream.publish.assert_not_called()


# Edge case: register_node with default pipeline_name
@patch("src.qmtl.sdk.execution.parallel_engine.topic")
def test_register_node_default_pipeline_name(mock_topic):
    engine = ParallelExecutionEngine()
    mock_topic.get_input_topic.return_value = "in"
    mock_topic.get_output_topic.return_value = "out"
    in_topic, out_topic = engine.register_node("n3")
    assert in_topic == "in"
    assert out_topic == "out"


# Edge case: prepare_pipeline with no execution_order
@patch("src.qmtl.sdk.execution.parallel_engine.topic")
def test_prepare_pipeline_no_execution_order(mock_topic):
    engine = ParallelExecutionEngine()
    pipeline = DummyPipeline(nodes={"a": DummyNode("a")})
    pipeline.execution_order = []
    engine.register_node = MagicMock()
    engine.prepare_pipeline(pipeline)
    assert engine.register_node.call_count == 1


# Edge case: execute_pipeline KeyboardInterrupt
@patch("src.qmtl.sdk.execution.parallel_engine.StreamProcessor")
@patch("src.qmtl.sdk.execution.parallel_engine.StateManager")
def test_execute_pipeline_keyboard_interrupt(mock_state, mock_stream):
    import asyncio
    engine = ParallelExecutionEngine()
    pipeline = DummyPipeline(nodes={"n1": DummyNode("n1")})
    engine.prepare_pipeline = MagicMock()
    real_loop = asyncio.new_event_loop()
    def fake_run_until_complete(coro):
        raise KeyboardInterrupt()
    real_loop.run_until_complete = fake_run_until_complete
    with patch("asyncio.get_event_loop", side_effect=RuntimeError):
        with patch("asyncio.new_event_loop", return_value=real_loop):
            try:
                engine.execute_pipeline(pipeline)
            except KeyboardInterrupt:
                pass
    real_loop.close()
