"""
통합 성능 테스트 (TEST-2)
- 대규모 노드 처리 성능
- 동시 요청 처리 성능
- 메모리 사용량 모니터링

NOTE: 실제 성능 측정은 pytest-benchmark, memory_profiler 등과 연동 권장
"""

import time

import pytest

pytestmark = pytest.mark.usefixtures("docker_compose_up_down")

from src.qmtl.sdk.node import ProcessingNode, SourceNode
from src.qmtl.sdk.pipeline import Pipeline
from qmtl.sdk.models import NodeStreamSettings, IntervalSettings, IntervalEnum

# from src.qmtl.sdk.client import OrchestratorClient  # 필요시 사용


@pytest.mark.performance
@pytest.mark.skipif("CI" in globals(), reason="성능 테스트는 로컬/특정 환경에서만 실행")
def test_large_scale_node_execution():
    """대규모 노드 처리 성능 테스트 (예: 1000개 노드)"""
    N = 1000

    def make_fn(i):
        return lambda x: x + i

    # 첫 노드는 SourceNode로 생성
    mock_source = type("MockSource", (), {"fetch": staticmethod(lambda: 0)})()
    source_node = SourceNode(
        name="node_0",
        source=mock_source,
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    nodes = [source_node]
    for i in range(1, N):
        node = ProcessingNode(
            name=f"node_{i}",
            fn=make_fn(i),
            upstreams=[f"node_{i-1}"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        nodes.append(node)
    pipeline = Pipeline(name="perf_large_scale")
    for node in nodes:
        pipeline.add_node(node)
    start = time.time()
    # SourceNode는 외부 입력이 없으므로, inputs는 비워둠
    pipeline.execute()
    elapsed = time.time() - start
    print(f"[PERF] {N} nodes executed in {elapsed:.2f}s")
    # SourceNode의 fn이 실제 값을 반환하지 않으므로, 결과 검증은 생략 또는 mock 활용


@pytest.mark.performance
def test_concurrent_pipeline_execution():
    """동시 요청 처리 성능 테스트 (예: 10개 파이프라인 동시 실행)"""
    from concurrent.futures import ThreadPoolExecutor

    N = 100

    def run():
        pipeline = Pipeline(name="perf_concurrent")
        mock_source = type("MockSource", (), {"fetch": staticmethod(lambda: 0)})()
        source_node = SourceNode(
            name="n0",
            source=mock_source,
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node = ProcessingNode(
            name="n1",
            fn=lambda x: x + 1,
            upstreams=["n0"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        pipeline.add_node(source_node)
        pipeline.add_node(node)
        return pipeline.execute()["n1"]

    start = time.time()
    with ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(lambda _: run(), range(N)))
    elapsed = time.time() - start
    print(f"[PERF] {N} concurrent executions in {elapsed:.2f}s")
    print(f"[DEBUG] results: {results}")
    assert all(r == 1 for r in results)
    # TODO: 임계값/성능 기준치 설정


@pytest.mark.performance
def test_memory_usage_during_execution():
    """메모리 사용량 모니터링 테스트 (memory_profiler 등 연동 권장)"""
    try:
        from memory_profiler import memory_usage
    except ImportError:
        pytest.skip("memory_profiler 미설치")
    pipeline = Pipeline(name="perf_memory")
    mock_source = type("MockSource", (), {"fetch": staticmethod(lambda: 0)})()
    source_node = SourceNode(
        name="n0",
        source=mock_source,
        stream_settings=NodeStreamSettings(
            intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
        ),
    )
    pipeline.add_node(source_node)
    for i in range(1, 100):
        node = ProcessingNode(
            name=f"n{i}",
            fn=lambda x: x + 1,
            upstreams=[f"n{i-1}"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        pipeline.add_node(node)

    def run():
        pipeline.execute()

    mem_usage = memory_usage(run, interval=0.1)
    print(f"[PERF] Max memory usage: {max(mem_usage):.2f} MB")
    # TODO: 임계값/성능 기준치 설정
