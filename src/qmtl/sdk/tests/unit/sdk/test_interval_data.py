"""
로컬 실행 엔진의 인터벌 데이터 관리 기능 테스트

이 모듈은 LocalExecutionEngine의 인터벌 데이터 관리 기능(저장, 조회, 캐싱)을 테스트합니다.
"""

import time

from qmtl.sdk.execution import LocalExecutionEngine
from qmtl.sdk.models import IntervalSettings, NodeStreamSettings, IntervalEnum
from qmtl.sdk.node import ProcessingNode
from qmtl.sdk.pipeline import Pipeline
from qmtl.sdk.node import SourceProcessor


def test_interval_data_save_and_retrieve():
    """인터벌 데이터 저장 및 조회 기능 테스트"""
    # 엔진 생성 및 캐시 초기화
    engine = LocalExecutionEngine(debug=True)
    engine.clear_cache()

    # 노드 ID 및 인터벌 설정
    node_id = "test_node"
    interval = 1

    # 데이터 저장
    test_data = {"value": 42}
    engine.save_interval_data(node_id, interval, test_data)

    # 데이터 조회
    history = engine.get_interval_data(node_id, interval)

    # 검증
    assert len(history) == 1
    assert history[0]["value"] == test_data
    assert "timestamp" in history[0]


def test_interval_data_max_items():
    """인터벌 데이터 최대 항목 수 제한 테스트"""
    # 엔진 생성 및 캐시 초기화
    engine = LocalExecutionEngine()
    engine.clear_cache()

    # 노드 ID 및 인터벌 설정
    node_id = "test_node"
    interval = 1
    max_items = 3

    # 최대 항목 수보다 많은 데이터 저장
    for i in range(5):
        engine.save_interval_data(node_id, interval, i, max_items=max_items)

    # 데이터 조회
    history = engine.get_interval_data(node_id, interval)

    # 검증
    assert len(history) == max_items
    # 최신 데이터가 먼저 오는지 확인 (0이 가장 최신)
    assert [item["value"] for item in history] == [4, 3, 2]


def test_ttl_expiration():
    """TTL 기반 데이터 만료 테스트"""
    # 엔진 생성 및 캐시 초기화
    engine = LocalExecutionEngine()
    engine.clear_cache()

    # 노드 ID 및 인터벌 설정
    node_id = "test_node"
    interval = 1

    # 즉시 만료되는 데이터 저장
    engine.save_interval_data(node_id, interval, "expired", ttl=0)

    # 약간의 시간을 두어 만료 처리가 이루어지도록 함
    time.sleep(0.01)

    # 만료되지 않는 데이터 저장
    engine.save_interval_data(node_id, interval, "not_expired")

    # 데이터 조회 전 명시적으로 만료 데이터 정리
    engine._cleanup_expired_data()

    # 데이터 조회
    history = engine.get_interval_data(node_id, interval)

    # 검증: 만료된 데이터는 제외되어야 함
    assert len(history) == 1
    assert history[0]["value"] == "not_expired"


def test_node_with_stream_settings():
    """스트림 설정이 있는 노드의 파이프라인 실행 및 데이터 관리 테스트"""
    # 파이프라인 생성
    pipeline = Pipeline(name="test_stream_settings")

    # SourceProcessor 기반 데이터 생성
    class DummySource(SourceProcessor):
        def fetch(self):
            return {"price": 100, "timestamp": time.time()}

    source = DummySource()

    # SourceNode를 파이프라인에 추가
    from qmtl.sdk.node import SourceNode

    source_stream_settings = NodeStreamSettings(
        intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
    )
    source_node = SourceNode(name="source", source=source, stream_settings=source_stream_settings)
    pipeline.nodes["source"] = source_node

    # 노드 생성 (업스트림 반드시 존재)
    stream_settings = NodeStreamSettings(
        intervals={
            IntervalEnum.DAY: IntervalSettings(max_history=2, interval=IntervalEnum.DAY, period=1),
            IntervalEnum.HOUR: IntervalSettings(
                max_history=3, interval=IntervalEnum.HOUR, period=1
            ),
        }
    )
    node = ProcessingNode(
        name="DataNode",
        fn=lambda value: value,
        upstreams=["source"],
        stream_settings=stream_settings,
    )
    pipeline.add_node(node)

    # 로컬 실행 엔진 생성 및 캐시 초기화
    engine = LocalExecutionEngine()
    engine.clear_cache()

    # 여러 번 실행하여 데이터 축적
    for _ in range(5):
        engine.execute_pipeline(pipeline)
        time.sleep(0.01)  # 타임스탬프 차이를 위해

    # 데이터 조회
    history_1d = engine.get_interval_data("DataNode", IntervalEnum.DAY)
    history_1h = engine.get_interval_data("DataNode", IntervalEnum.HOUR)

    # 검증
    assert len(history_1d) == 2  # 1d는 max_history=2
    assert len(history_1h) == 3  # 1h는 max_history=3

    # 모든 데이터는 price 필드를 가져야 함
    for item in history_1d:
        assert "price" in item["value"]

    for item in history_1h:
        assert "price" in item["value"]


def test_node_metadata():
    """노드 메타데이터 조회 테스트"""
    # 엔진 생성 및 캐시 초기화
    engine = LocalExecutionEngine()
    engine.clear_cache()

    # 노드 ID 및 인터벌 설정
    node_id = "test_node"

    # 여러 인터벌에 데이터 저장
    engine.save_interval_data(node_id, IntervalEnum.DAY, "daily data")
    engine.save_interval_data(node_id, IntervalEnum.HOUR, "hourly data")

    # 메타데이터 조회
    metadata = engine.get_node_metadata(node_id)

    # 검증
    assert metadata["node_id"] == node_id
    assert IntervalEnum.DAY in metadata["intervals"]
    assert IntervalEnum.HOUR in metadata["intervals"]
    assert metadata["intervals"][IntervalEnum.DAY]["count"] == 1
    assert metadata["intervals"][IntervalEnum.HOUR]["count"] == 1


def test_cache_clearing():
    """캐시 초기화 기능 테스트"""
    # 엔진 생성
    engine = LocalExecutionEngine()

    # 여러 노드 및 인터벌에 데이터 저장
    engine.save_interval_data("node1", IntervalEnum.DAY, "data1")
    engine.save_interval_data("node1", IntervalEnum.HOUR, "data2")
    engine.save_interval_data("node2", IntervalEnum.DAY, "data3")

    # 특정 노드 캐시 초기화
    engine.clear_cache(node_id="node1")

    # 검증
    assert engine.get_interval_data("node1", IntervalEnum.DAY) == []
    assert engine.get_interval_data("node1", IntervalEnum.HOUR) == []
    assert len(engine.get_interval_data("node2", IntervalEnum.DAY)) == 1

    # 모든 캐시 초기화
    engine.clear_cache()

    # 검증
    assert engine.get_interval_data("node2", IntervalEnum.DAY) == []


def test_pipeline_integration():
    """인터벌 데이터 관리 파이프라인 통합 테스트"""
    # 파이프라인 생성
    pipeline = Pipeline(name="test_pipeline_integration")

    # SourceProcessor 및 SourceNode 정의
    class DummySource(SourceProcessor):
        def fetch(self):
            return 42

    source_proc = DummySource()
    from qmtl.sdk.node import SourceNode

    source = SourceNode(
        name="Source",
        source=source_proc,
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )

    def process_node(source):
        return source * 2

    processor = ProcessingNode(
        name="Processor",
        fn=process_node,
        upstreams=["Source"],
        stream_settings=NodeStreamSettings(
            intervals={
                IntervalEnum.DAY: IntervalSettings(
                    max_history=3, interval=IntervalEnum.DAY, period=1
                )
            }
        ),
    )

    pipeline.nodes["Source"] = source
    pipeline.add_node(processor)

    # 로컬 실행 엔진 생성 및 캐시 초기화
    engine = LocalExecutionEngine()
    engine.clear_cache()

    # 파이프라인 여러 번 실행
    for _ in range(5):
        results = engine.execute_pipeline(pipeline)
        assert results["Source"] == 42
        assert results["Processor"] == 84

    # 데이터 조회
    source_history = engine.get_interval_data("Source", IntervalEnum.DAY)
    processor_history = engine.get_interval_data("Processor", IntervalEnum.DAY)

    # 검증
    assert len(source_history) == 5
    assert len(processor_history) == 3

    # 메타데이터 검증
    source_metadata = engine.get_node_metadata("Source")
    processor_metadata = engine.get_node_metadata("Processor")

    assert source_metadata["intervals"][IntervalEnum.DAY]["count"] == 5
    assert processor_metadata["intervals"][IntervalEnum.DAY]["count"] == 3
