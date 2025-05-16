from qmtl.sdk.node import ProcessingNode, SourceNode, SourceProcessor
from qmtl.sdk.pipeline import Pipeline
from qmtl.sdk.models import IntervalEnum, IntervalSettings, NodeStreamSettings
import pytest


@pytest.mark.integration
def test_redis_session_and_clean(redis_clean, redis_session):
    """
    [FIXTURE-1] 실제 Redis 컨테이너와 연동되는 기본 동작 테스트
    """
    redis_session.set("foo", "bar")
    assert redis_session.get("foo") == b"bar"
    redis_session.set("num", 123)
    assert int(redis_session.get("num")) == 123
    # clean fixture가 동작하면 다음 테스트에서 DB가 비워짐을 보장


"""
Redis 기반 인터벌 데이터 관리 테스트

이 모듈은 Pipeline 클래스의 Redis 기반 인터벌 데이터 관리 기능을 테스트합니다.
"""
import time
from unittest.mock import MagicMock, patch

import pytest

from qmtl.sdk.node import ProcessingNode, SourceNode
from qmtl.sdk.pipeline import Pipeline


class TestRedisIntervalData:
    # Redis 기반 인터벌 데이터 관리 테스트

    @pytest.fixture
    def mock_state_manager(self):
        """StateManager 모킹 및 Pipeline.state_manager_cls 패치"""
        from qmtl.sdk.pipeline import Pipeline

        with patch("qmtl.sdk.execution.StateManager") as mock_manager_cls:
            manager = MagicMock()
            mock_manager_cls.return_value = manager
            # Pipeline.state_manager_cls가 항상 이 매니저를 반환하도록 설정
            Pipeline.state_manager_cls = MagicMock(return_value=manager)
            yield manager
            Pipeline.state_manager_cls = None

    @pytest.fixture
    def test_pipeline(self):
        """테스트용 파이프라인과 노드 생성"""
        default_intervals = {
            IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=14),
            IntervalEnum.HOUR: IntervalSettings(interval=IntervalEnum.HOUR, period=7),
            IntervalEnum.MINUTE: IntervalSettings(interval=IntervalEnum.MINUTE, period=3),
        }
        pl = Pipeline(name="test_pipeline", default_intervals=default_intervals)

        # SourceNode로 교체 (업스트림 없음)
        class DummySourceA(SourceProcessor):
            def fetch(self):
                return 42

        class DummySourceB(SourceProcessor):
            def fetch(self):
                return "hello"

        node_a = SourceNode(
            name="node_a",
            source=DummySourceA(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_a.node_id = "test_node_a_id"  # 테스트용 고정 ID 설정
        node_b = SourceNode(
            name="node_b",
            source=DummySourceB(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_b.node_id = "test_node_b_id"  # 테스트용 고정 ID 설정
        # 여러 인터벌을 가진 노드 추가 (업스트림 지정)
        node_c = ProcessingNode(
            name="node_c",
            fn=lambda a, b: f"{a}-{b}",
            upstreams=["node_a", "node_b"],
            interval_settings={
                IntervalEnum.DAY: {"interval": IntervalEnum.DAY, "period": 14, "max_history": 100},
                IntervalEnum.HOUR: {"interval": IntervalEnum.HOUR, "period": 2, "max_history": 50},
                IntervalEnum.MINUTE: {
                    "interval": IntervalEnum.MINUTE,
                    "period": 1,
                    "max_history": 20,
                },
            },
        )
        node_c.node_id = "test_node_c_id"  # 테스트용 고정 ID 설정
        pl.add_node(node_a)
        pl.add_node(node_b)
        pl.add_node(node_c)
        return pl

    def test_get_history_redis(self, test_pipeline, mock_state_manager):
        """Redis에서 히스토리 조회 테스트"""
        test_pipeline.results_cache = {}
        if hasattr(test_pipeline, "_local_engine"):
            delattr(test_pipeline, "_local_engine")
        for node in test_pipeline.nodes.values():
            node.results_cache = {}
        # 모의 응답 설정
        mock_state_manager.get_history.return_value = [
            {"timestamp": int(time.time()), "value": 42},
            {"timestamp": int(time.time()) - 3600, "value": 41},
            {"timestamp": int(time.time()) - 7200, "value": 40},
        ]

        # 히스토리 조회
        history = test_pipeline.get_history(
            node_name="node_a", interval="1d", count=3, redis_uri="dummy://test"
        )

        # 결과 검증
        assert len(history) == 3
        assert history[0]["value"] == 42
        assert history[1]["value"] == 41
        assert history[2]["value"] == 40

        # StateManager.get_history 호출 검증
        mock_state_manager.get_history.assert_called_once_with(
            node_id="test_node_a_id", interval="1d", count=3, start_ts=None, end_ts=None
        )

    def test_get_history_with_timestamp_filters(self, test_pipeline, mock_state_manager):
        """타임스탬프 필터로 히스토리 조회 테스트"""
        test_pipeline.results_cache = {}
        if hasattr(test_pipeline, "_local_engine"):
            delattr(test_pipeline, "_local_engine")
        for node in test_pipeline.nodes.values():
            node.results_cache = {}
        now = int(time.time())
        items = [{"timestamp": now, "value": 42}, {"timestamp": now - 3600, "value": 41}]

        def get_history_side_effect(node_id, interval, count=10, start_ts=None, end_ts=None):
            filtered = [
                item
                for item in items
                if (start_ts is None or item["timestamp"] > start_ts)
                and (end_ts is None or item["timestamp"] <= end_ts)
            ]
            return filtered[:count]

        mock_state_manager.get_history.side_effect = get_history_side_effect
        # 파이프라인의 로컬 캐시/엔진 비우기 (항상 redis branch로 진입 보장)
        test_pipeline.results_cache = {}
        if hasattr(test_pipeline, "_local_engine"):
            delattr(test_pipeline, "_local_engine")
        # 타임스탬프 필터링 조회
        history = test_pipeline.get_history(
            node_name="node_a",
            interval="1d",
            count=5,
            start_ts=now - 4000,
            end_ts=now + 1000,
            redis_uri="dummy://test",
        )
        # 결과 검증
        assert len(history) == 2
        # StateManager.get_history 호출 검증
        mock_state_manager.get_history.assert_called_once_with(
            node_id="test_node_a_id", interval="1d", count=5, start_ts=now - 4000, end_ts=now + 1000
        )

    def test_get_interval_data(self, test_pipeline, mock_state_manager):
        """인터벌 데이터만 조회 테스트"""
        test_pipeline.results_cache = {}
        if hasattr(test_pipeline, "_local_engine"):
            delattr(test_pipeline, "_local_engine")
        for node in test_pipeline.nodes.values():
            node.results_cache = {}
        now = int(time.time())
        items = [{"timestamp": now, "value": 42}, {"timestamp": now - 3600, "value": 41}]

        def get_history_side_effect(node_id, interval, count=10, start_ts=None, end_ts=None):
            return items[:count]

        mock_state_manager.get_history.side_effect = get_history_side_effect
        test_pipeline.results_cache = {}
        if hasattr(test_pipeline, "_local_engine"):
            delattr(test_pipeline, "_local_engine")
        # 값만 조회
        values = test_pipeline.get_interval_data(
            node_name="node_a", interval="1d", count=2, redis_uri="dummy://test"
        )
        # 결과 검증
        assert values == [42, 41]
        # StateManager.get_history 호출 검증
        mock_state_manager.get_history.assert_called_once()

    def test_get_node_metadata(self, test_pipeline, mock_state_manager):
        """노드 메타데이터 조회 테스트"""
        test_pipeline.results_cache = {}
        if hasattr(test_pipeline, "_local_engine"):
            delattr(test_pipeline, "_local_engine")
        for node in test_pipeline.nodes.values():
            node.results_cache = {}
        # 모의 응답 설정
        mock_state_manager.get_history_metadata.return_value = {
            "count": 42,
            "max_items": 100,
            "last_update": int(time.time()),
            "ttl": 604800,  # 7일 (초)
            "actual_count": 42,
        }

        # 메타데이터 조회
        meta = test_pipeline.get_node_metadata(
            node_name="node_a", interval="1d", redis_uri="dummy://test"
        )

        # 결과 검증
        assert meta["count"] == 42
        assert meta["max_items"] == 100
        assert meta["ttl"] == 604800
        assert meta["source"] == "redis"

        # StateManager.get_history_metadata 호출 검증
        mock_state_manager.get_history_metadata.assert_called_once_with(
            node_id="test_node_a_id", interval="1d"
        )

    def test_multiple_interval_support(self, test_pipeline, mock_state_manager):
        """여러 인터벌 지원 테스트"""
        test_pipeline.results_cache = {}
        if hasattr(test_pipeline, "_local_engine"):
            delattr(test_pipeline, "_local_engine")
        for node in test_pipeline.nodes.values():
            node.results_cache = {}
        now = int(time.time())
        interval_data = {
            "1d": [{"timestamp": now, "value": "daily-value"}],
            "1h": [{"timestamp": now, "value": "hourly-value"}],
            "5m": [{"timestamp": now, "value": "5min-value"}],
        }

        def get_history_side_effect(node_id, interval, count=1, start_ts=None, end_ts=None):
            return interval_data[interval][:count]

        mock_state_manager.get_history.side_effect = get_history_side_effect
        test_pipeline.results_cache = {}
        if hasattr(test_pipeline, "_local_engine"):
            delattr(test_pipeline, "_local_engine")
        # 각 인터벌별로 데이터 조회
        daily_value = test_pipeline.get_interval_data(
            node_name="node_c", interval="1d", count=1, redis_uri="dummy://test"
        )
        hourly_value = test_pipeline.get_interval_data(
            node_name="node_c", interval="1h", count=1, redis_uri="dummy://test"
        )
        minute5_value = test_pipeline.get_interval_data(
            node_name="node_c", interval="5m", count=1, redis_uri="dummy://test"
        )
        # 결과 검증
        assert daily_value == ["daily-value"]
        assert hourly_value == ["hourly-value"]
        assert minute5_value == ["5min-value"]
        # get_history 호출 횟수 검증
        assert mock_state_manager.get_history.call_count == 3
