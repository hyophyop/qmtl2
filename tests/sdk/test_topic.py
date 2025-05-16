"""
# Kafka/Redpanda 토픽 명명 및 생성 유틸리티 테스트
"""

import pytest

from qmtl.sdk import topic


def test_sanitize_name():
    assert topic.sanitize_name("my pipeline@2025") == "my_pipeline_2025"
    assert topic.sanitize_name("node#1") == "node_1"
    assert topic.sanitize_name("A.B-C") == "A.B-C"


def test_get_input_output_topic():
    assert topic.get_input_topic("my pipeline", "node1") == "qmtl.input.my_pipeline.node1"
    assert topic.get_output_topic("my pipeline", "node1") == "qmtl.output.my_pipeline.node1"


@pytest.mark.skipif(not topic.KAFKA_ADMIN_AVAILABLE, reason="confluent-kafka 미설치")
def test_create_topic(monkeypatch):
    class DummyAdmin:
        def __init__(self, *a, **kw):
            pass

        def list_topics(self, timeout=5):
            class T:
                topics = {"exists": None}

            return T()

        def create_topics(self, topics):
            class F:
                def result(self, timeout=10):
                    return True

            return {t.topic: F() for t in topics}

    monkeypatch.setattr(topic, "AdminClient", DummyAdmin)
    monkeypatch.setattr(topic, "NewTopic", lambda t, **kw: type("T", (), {"topic": t})())
    assert topic.create_topic("dummy:9092", "newtopic")
    assert topic.create_topic("dummy:9092", "exists")
