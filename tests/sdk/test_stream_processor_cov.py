"""
Unit tests for src/qmtl/sdk/execution/stream_processor.py
커버리지 80% 달성을 위한 smoke/엣지케이스 테스트 템플릿
"""
import sys
from unittest.mock import patch, MagicMock
import pytest

from src.qmtl.sdk.execution import stream_processor

def test_stream_processor_init():
    sp = stream_processor.StreamProcessor()
    assert sp is not None

# --- KAFKA_AVAILABLE=False 예외 테스트 ---
def test_stream_processor_importerror():
    with patch.object(stream_processor, "KAFKA_AVAILABLE", False):
        with pytest.raises(ImportError):
            stream_processor.StreamProcessor()

# --- 정상 publish/subscribe/consume/close ---
@patch("src.qmtl.sdk.execution.stream_processor.Producer")
@patch("src.qmtl.sdk.execution.stream_processor.Consumer")
def test_stream_processor_publish_subscribe_consume_close(MockConsumer, MockProducer):
    mock_producer = MagicMock()
    mock_consumer = MagicMock()
    MockProducer.return_value = mock_producer
    MockConsumer.return_value = mock_consumer
    sp = stream_processor.StreamProcessor()

    # publish 정상
    sp.publish("topic", {"foo": 1}, key="bar")
    mock_producer.produce.assert_called()
    mock_producer.flush.assert_called()

    # subscribe 정상
    sp.subscribe(["topic1", "topic2"])
    mock_consumer.subscribe.assert_called_with(["topic1", "topic2"])

    # consume 정상 (메시지 있음)
    mock_msg = MagicMock()
    mock_msg.error.return_value = None
    mock_msg.value.return_value = b'{"x": 1}'
    mock_msg.key.return_value = b"k"
    mock_msg.topic.return_value = "t"
    mock_msg.partition.return_value = 0
    mock_msg.offset.return_value = 1
    mock_consumer.poll.return_value = mock_msg
    result = sp.consume()
    assert result["value"] == {"x": 1}
    assert result["key"] == "k"

    # consume 정상 (메시지 없음)
    mock_consumer.poll.return_value = None
    assert sp.consume() is None

    # close 정상
    sp.close()
    mock_producer.flush.assert_called()
    mock_consumer.close.assert_called()

# --- publish/subscribe/consume 예외 경로 ---
@patch("src.qmtl.sdk.execution.stream_processor.Producer")
@patch("src.qmtl.sdk.execution.stream_processor.Consumer")
def test_stream_processor_publish_exception(MockConsumer, MockProducer):
    mock_producer = MagicMock()
    MockProducer.return_value = mock_producer
    sp = stream_processor.StreamProcessor()
    mock_producer.produce.side_effect = Exception("fail")
    with pytest.raises(Exception):
        sp.publish("topic", {"foo": 1})

@patch("src.qmtl.sdk.execution.stream_processor.Producer")
@patch("src.qmtl.sdk.execution.stream_processor.Consumer")
def test_stream_processor_subscribe_exception(MockConsumer, MockProducer):
    mock_consumer = MagicMock()
    MockConsumer.return_value = mock_consumer
    sp = stream_processor.StreamProcessor()
    mock_consumer.subscribe.side_effect = Exception("fail")
    with pytest.raises(Exception):
        sp.subscribe(["t"])

@patch("src.qmtl.sdk.execution.stream_processor.Producer")
@patch("src.qmtl.sdk.execution.stream_processor.Consumer")
def test_stream_processor_consume_error(MockConsumer, MockProducer):
    mock_consumer = MagicMock()
    MockConsumer.return_value = mock_consumer
    sp = stream_processor.StreamProcessor()
    # 메시지 error() True, code() == _PARTITION_EOF
    mock_msg = MagicMock()
    mock_msg.error.return_value = MagicMock(code=MagicMock(return_value=stream_processor.KafkaError._PARTITION_EOF))
    mock_consumer.poll.return_value = mock_msg
    assert sp.consume() is None
    # 메시지 error() True, code() != _PARTITION_EOF
    mock_msg.error.return_value = MagicMock(code=MagicMock(return_value=999))
    assert sp.consume() is None
    # 메시지 역직렬화 오류
    mock_msg.error.return_value = None
    mock_msg.value.return_value = b"not-json"
    mock_consumer.poll.return_value = mock_msg
    assert sp.consume() is None
    # poll 자체 예외
    mock_consumer.poll.side_effect = Exception("fail")
    assert sp.consume() is None
