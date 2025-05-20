import pytest

from src.qmtl.sdk.execution.stream_processor import StreamProcessor


@pytest.mark.skipif("confluent_kafka" not in globals(), reason="confluent-kafka 미설치 시 스킵")
def test_stream_processor_init(redpanda_session):
    """
    [FIXTURE-3] redpanda_session fixture를 사용하여 docker-compose 기반 Redpanda 브로커 주소로 테스트
    """
    sp = StreamProcessor(brokers=redpanda_session)
    assert sp.brokers == redpanda_session
    assert sp.group_id.startswith("qmtl-group-")
    assert sp.client_id.startswith("qmtl-client-")


# 실제 Kafka 브로커가 없으면 publish/consume 테스트는 생략
