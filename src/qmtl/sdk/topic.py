"""
Kafka/Redpanda 토픽 명명 및 생성 유틸리티
"""

import re
from typing import Any, Dict, Optional

try:
    from confluent_kafka.admin import AdminClient, NewTopic

    KAFKA_ADMIN_AVAILABLE = True
except ImportError:
    KAFKA_ADMIN_AVAILABLE = False


def sanitize_name(name: str) -> str:
    """Kafka 토픽에 사용할 수 있도록 이름을 정규화"""
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", name)


def get_input_topic(pipeline_name: str, node_name: str) -> str:
    return f"qmtl.input.{sanitize_name(pipeline_name)}.{sanitize_name(node_name)}"


def get_output_topic(pipeline_name: str, node_name: str) -> str:
    return f"qmtl.output.{sanitize_name(pipeline_name)}.{sanitize_name(node_name)}"


def create_topic(
    brokers: str,
    topic: str,
    num_partitions: int = 1,
    replication_factor: int = 1,
    config: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Kafka/Redpanda에 토픽을 생성합니다.
    이미 존재하면 무시합니다.
    """
    if not KAFKA_ADMIN_AVAILABLE:
        raise ImportError("confluent-kafka 패키지와 AdminClient가 필요합니다.")
    admin = AdminClient({"bootstrap.servers": brokers})
    # 이미 존재하는지 확인
    if topic in admin.list_topics(timeout=5).topics:
        return True
    new_topic = NewTopic(
        topic,
        num_partitions=num_partitions,
        replication_factor=replication_factor,
        config=config or {},
    )
    fs = admin.create_topics([new_topic])
    try:
        fs[topic].result(timeout=10)
        return True
    except Exception as e:
        # 이미 존재하는 경우 등은 무시
        if "Topic already exists" in str(e):
            return True
        import logging

        logging.warning(f"토픽 생성 실패: {topic} ({e})")
        return False
