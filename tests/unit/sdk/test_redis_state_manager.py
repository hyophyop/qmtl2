"""
Redis 상태 관리 모듈 테스트

이 모듈은 SDK의 Redis 기반 상태 관리 메커니즘(인터벌별 데이터 저장, TTL 관리, 히스토리 조회 최적화)을 테스트합니다.
"""

import json
import time
from unittest.mock import MagicMock, patch

import pytest

from qmtl.sdk.execution import StateManager


class TestStateManager:
    """Redis 기반 상태 관리자 테스트"""

    @pytest.fixture
    def mock_redis(self):
        """Redis 모킹"""
        with patch("redis.from_url") as mock_redis:
            # Redis 클라이언트 모의 객체 생성
            redis_client = MagicMock()
            redis_client.ping.return_value = True
            mock_redis.return_value = redis_client
            yield redis_client

    @pytest.fixture
    def state_manager(self, mock_redis):
        """모의 Redis를 사용하는 상태 관리자 생성"""
        manager = StateManager(
            redis_uri="redis://localhost:6379/0", connection_pool_size=5, connection_timeout=2.0
        )
        return manager

    def test_initialization(self, mock_redis):
        """초기화 테스트"""
        # StateManager 생성
        manager = StateManager(
            redis_uri="redis://testhost:6379/1",
            connection_pool_size=10,
            connection_timeout=3.0,
            retry_on_timeout=True,
            health_check_interval=60,
        )

        # Redis 연결 파라미터 검증
        assert manager.redis_uri == "redis://testhost:6379/1"
        assert manager._connection_params["max_connections"] == 10
        assert manager._connection_params["socket_timeout"] == 3.0
        assert manager._connection_params["retry_on_timeout"] == True
        assert manager._connection_params["health_check_interval"] == 60

    def test_redis_connection(self, mock_redis, state_manager):
        """Redis 연결 테스트"""
        # redis 속성 접근 시 연결 초기화 확인
        redis_client = state_manager.redis
        assert redis_client is mock_redis

        # 연결 테스트(ping) 호출 확인
        mock_redis.ping.assert_called_once()

    def test_set_get_delete(self, mock_redis, state_manager):
        """기본 값 설정/조회/삭제 테스트"""
        # 모의 응답 설정
        mock_redis.set.return_value = True
        mock_redis.get.return_value = json.dumps({"test": "value"}).encode("utf-8")
        mock_redis.delete.return_value = 1

        # 값 설정
        result = state_manager.set("test_key", {"test": "value"}, expire=60)
        assert result == True
        mock_redis.set.assert_called_with("test_key", json.dumps({"test": "value"}), ex=60)

        # 값 조회
        value = state_manager.get("test_key")
        assert value == {"test": "value"}
        mock_redis.get.assert_called_with("test_key")

        # 값 삭제
        delete_result = state_manager.delete("test_key")
        assert delete_result == True
        mock_redis.delete.assert_called_with("test_key")

    def test_save_history(self, mock_redis, state_manager):
        """히스토리 저장 테스트"""
        # Redis 파이프라인 모의 객체 설정
        pipeline_mock = MagicMock()
        mock_redis.pipeline.return_value = pipeline_mock
        mock_redis.llen.return_value = 5

        # 히스토리 저장
        node_id = "test_node_123"
        interval = "1d"
        test_value = {"price": 100.5}
        result = state_manager.save_history(node_id, interval, test_value, max_items=10, ttl=86400)

        # 결과 검증
        assert result == True

        # 히스토리 키 검증
        expected_key = f"node:{node_id}:history:{interval}"
        pipeline_mock.lpush.assert_called_once()
        pipeline_mock.ltrim.assert_called_once_with(expected_key, 0, 9)
        pipeline_mock.expire.assert_called_once_with(expected_key, 86400)
        pipeline_mock.execute.assert_called_once()

    def test_get_history(self, mock_redis, state_manager):
        """히스토리 조회 테스트"""
        # 모의 데이터 생성
        node_id = "test_node_123"
        interval = "1d"
        expected_key = f"node:{node_id}:history:{interval}"

        # 모의 히스토리 항목
        history_items = [
            json.dumps({"timestamp": int(time.time()) - i * 3600, "value": f"value_{i}"}).encode(
                "utf-8"
            )
            for i in range(3)
        ]

        # 모의 응답 설정
        mock_redis.lrange.return_value = history_items

        # 히스토리 조회
        history = state_manager.get_history(node_id, interval, count=3)

        # 결과 검증
        assert len(history) == 3
        assert history[0]["value"] == "value_0"
        assert history[1]["value"] == "value_1"
        assert history[2]["value"] == "value_2"

        # lrange 호출 검증
        mock_redis.lrange.assert_called_with(expected_key, 0, 2)

    def test_get_history_with_timestamp_filters(self, mock_redis, state_manager):
        """타임스탬프 필터로 히스토리 조회 테스트"""
        # 현재 시간
        now = int(time.time())

        # 모의 데이터 생성
        node_id = "test_node_123"
        interval = "1d"

        # 모의 히스토리 항목 (3시간 간격으로 3개 항목)
        history_items = [
            json.dumps({"timestamp": now - i * 3600, "value": f"value_{i}"}).encode("utf-8")
            for i in range(3)
        ]

        # 모의 응답 설정
        mock_redis.lrange.return_value = history_items

        # 중간 시점 이후 항목만 필터링
        mid_time = now - 1.5 * 3600  # 1.5시간 전 (첫 번째 항목만 포함)
        history = state_manager.get_history(node_id, interval, count=3, start_ts=mid_time)

        # 결과 검증
        assert len(history) == 2
        assert history[0]["value"] == "value_0"
        assert history[1]["value"] == "value_1"

    def test_update_ttl(self, mock_redis, state_manager):
        """TTL 업데이트 테스트"""
        # 모의 응답 설정
        mock_redis.expire.return_value = True
        mock_redis.get.return_value = json.dumps({"count": 5, "max_items": 10}).encode("utf-8")
        mock_redis.set.return_value = True

        # TTL 업데이트
        node_id = "test_node_123"
        interval = "1d"
        result = state_manager.update_ttl(node_id, interval, 7200)  # 2시간 TTL

        # 결과 검증
        assert result == True

        # 히스토리 및 메타 키에 expire 호출 검증
        history_key = f"node:{node_id}:history:{interval}"
        meta_key = f"node:{node_id}:meta:{interval}"
        mock_redis.expire.assert_any_call(history_key, 7200)
        mock_redis.expire.assert_any_call(meta_key, 7200)

    def test_clean_expired_data(self, mock_redis, state_manager):
        """만료 데이터 정리 테스트"""
        # 만료된 키 목록 설정
        mock_redis.scan_iter.return_value = [
            b"node:test_node:history:1d",
            b"node:test_node:meta:1d",
        ]

        # TTL 값 설정 (-2는 만료됨을 의미)
        def ttl_side_effect(key):
            return -2

        mock_redis.ttl.side_effect = ttl_side_effect
        mock_redis.delete.return_value = 1

        # 만료된 데이터 정리
        cleaned = state_manager.clean_expired_data()

        # 결과 검증
        assert cleaned == 2
        assert mock_redis.delete.call_count == 2

    def test_clear_all(self, mock_redis, state_manager):
        """전체 데이터 삭제 테스트"""
        # 키 목록 설정
        mock_redis.scan_iter.return_value = [
            b"node:node1:history:1d",
            b"node:node1:meta:1d",
            b"node:node2:history:1h",
        ]

        mock_redis.delete.return_value = 1

        # 전체 데이터 삭제
        deleted = state_manager.clear_all()

        # 결과 검증
        assert deleted == 3
        assert mock_redis.delete.call_count == 3

    def test_clear_by_node_id(self, mock_redis, state_manager):
        """노드별 데이터 삭제 테스트"""

        # 노드 ID 지정하여 키 목록 필터링
        def scan_iter_side_effect(match):
            if match == "node:test_node:*":
                return [b"node:test_node:history:1d", b"node:test_node:meta:1d"]
            return []

        mock_redis.scan_iter.side_effect = scan_iter_side_effect
        mock_redis.delete.return_value = 1

        # 특정 노드 데이터만 삭제
        deleted = state_manager.clear_all(node_id="test_node")

        # 결과 검증
        assert deleted == 2
        assert mock_redis.delete.call_count == 2

    def test_get_interval_data(self, mock_redis, state_manager):
        """인터벌 데이터만 조회 테스트"""
        # 모의 데이터 생성
        node_id = "test_node_123"
        interval = "1d"

        # 모의 히스토리 항목
        history_items = [
            json.dumps({"timestamp": int(time.time()) - i * 3600, "value": i * 100}).encode("utf-8")
            for i in range(3)
        ]

        # 모의 응답 설정
        mock_redis.lrange.return_value = history_items

        # 인터벌 데이터만 조회
        values = state_manager.get_interval_data(node_id, interval, count=3)

        # 결과 검증
        assert len(values) == 3
        assert values == [0, 100, 200]

    def test_get_history_metadata(self, mock_redis, state_manager):
        """히스토리 메타데이터 조회 테스트"""
        # 모의 데이터 생성
        node_id = "test_node_123"
        interval = "1d"
        meta_key = f"node:{node_id}:meta:{interval}"
        history_key = f"node:{node_id}:history:{interval}"

        # 모의 메타데이터
        meta_data = {"last_update": int(time.time()), "count": 7, "max_items": 10, "ttl": 86400}

        # 모의 응답 설정
        mock_redis.get.return_value = json.dumps(meta_data).encode("utf-8")
        mock_redis.llen.return_value = 8  # 실제 항목 수

        # 메타데이터 조회
        meta = state_manager.get_history_metadata(node_id, interval)

        # 결과 검증
        assert meta["count"] == 7
        assert meta["max_items"] == 10
        assert meta["ttl"] == 86400
        assert meta["actual_count"] == 8  # 실제 항목 수 추가됨

        # 호출 검증
        mock_redis.get.assert_called_with(meta_key)
        mock_redis.llen.assert_called_with(history_key)

    def test_redis_connection_error_handling(self):
        """Redis 연결 오류 처리 테스트"""
        with patch("redis.from_url") as mock_redis_factory:
            # 첫 번째 호출에서 ConnectionError 발생
            mock_redis_factory.side_effect = [
                Exception("Connection refused"),  # 첫 번째 호출에서 오류
                MagicMock(),  # 두 번째 호출에서 성공
            ]

            # StateManager 생성 (바로 연결하지 않음)
            manager = StateManager(redis_uri="redis://errorhost:6379/0")

            # redis 속성 접근 시 연결 시도
            redis_client = manager.redis

            # 실패해도 객체는 반환됨
            assert redis_client is not None
