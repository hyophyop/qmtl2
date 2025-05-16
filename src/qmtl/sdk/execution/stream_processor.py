"""
Kafka/Redpanda 스트림 처리를 위한 기본 클래스
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

try:
    from confluent_kafka import Consumer, KafkaError, Producer

    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False


class StreamProcessor:
    def __init__(
        self,
        brokers: str = "localhost:9092",
        group_id: Optional[str] = None,
        client_id: Optional[str] = None,
    ):
        if not KAFKA_AVAILABLE:
            raise ImportError(
                "병렬 실행을 위해서는 confluent-kafka 패키지가 필요합니다. "
                "pip install confluent-kafka 명령으로 설치하세요."
            )
        self.brokers = brokers
        self.group_id = group_id or f"qmtl-group-{int(time.time())}"
        self.client_id = client_id or f"qmtl-client-{int(time.time())}"
        self._producer = None
        self._consumer = None

    @property
    def producer(self):
        if self._producer is None:
            self._producer = Producer(
                {"bootstrap.servers": self.brokers, "client.id": f"{self.client_id}-producer"}
            )
        return self._producer

    @property
    def consumer(self):
        if self._consumer is None:
            self._consumer = Consumer(
                {
                    "bootstrap.servers": self.brokers,
                    "group.id": self.group_id,
                    "client.id": f"{self.client_id}-consumer",
                    "auto.offset.reset": "latest",
                }
            )
        return self._consumer

    def publish(self, topic: str, value: Any, key: Optional[str] = None) -> None:
        try:
            serialized_value = json.dumps(value).encode("utf-8")
            serialized_key = key.encode("utf-8") if key else None
            self.producer.produce(
                topic=topic,
                value=serialized_value,
                key=serialized_key,
                callback=self._delivery_report,
            )
            self.producer.flush(timeout=5)
        except Exception as e:
            logging.error(f"메시지 발행 중 오류 발생: {e}")
            raise

    def subscribe(self, topics: List[str]) -> None:
        try:
            self.consumer.subscribe(topics)
        except Exception as e:
            logging.error(f"토픽 구독 중 오류 발생: {e}")
            raise

    def consume(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        try:
            msg = self.consumer.poll(timeout)
            if msg is None:
                return None
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    return None
                else:
                    logging.error(f"메시지 소비 중 오류 발생: {msg.error()}")
                    return None
            try:
                value = json.loads(msg.value().decode("utf-8"))
                key = msg.key().decode("utf-8") if msg.key() else None
                return {
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "offset": msg.offset(),
                    "key": key,
                    "value": value,
                }
            except Exception as e:
                logging.error(f"메시지 역직렬화 중 오류 발생: {e}")
                return None
        except Exception as e:
            logging.error(f"메시지 소비 중 오류 발생: {e}")
            return None

    def _delivery_report(self, err, msg):
        if err is not None:
            logging.error(f"메시지 전송 실패: {err}")
        else:
            logging.debug(f"메시지 전송 성공: {msg.topic()} [{msg.partition()}] @ {msg.offset()}")

    def close(self):
        if self._producer:
            self.producer.flush()
        if self._consumer:
            self.consumer.close()
