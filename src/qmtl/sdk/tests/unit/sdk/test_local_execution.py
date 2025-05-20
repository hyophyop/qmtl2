"""
로컬 실행 메커니즘 테스트

이 모듈은 SDK의 로컬 실행 메커니즘(토폴로지 정렬, 노드 간 데이터 전송, 결과 수집)을 테스트합니다.
"""

import time

import pytest

from qmtl.sdk.execution import LocalExecutionEngine
from qmtl.sdk.node import ProcessingNode
from qmtl.sdk.pipeline import Pipeline
from qmtl.sdk.models import IntervalEnum, IntervalSettings, NodeStreamSettings


# 테스트용 간단한 노드 함수들
def node_a_fn():
    """의존성 없는 소스 노드"""
    return 42


def node_b_fn():
    """의존성 없는 소스 노드"""
    return "hello"


def node_c_fn(a):
    """A에 의존하는 노드"""
    return a * 2


def node_d_fn(b):
    """B에 의존하는 노드"""
    return f"{b} world"


def node_e_fn(c, d):
    """C와 D에 의존하는 노드"""
    return f"{d} ({c})"


def node_f_fn(**kwargs):
    """여러 업스트림에 의존하는 노드 (키워드 인자로 받음)"""
    return sum(len(v) if isinstance(v, str) else v for v in kwargs.values())


def node_with_error_fn(a):
    """오류를 발생시키는 노드"""
    raise ValueError("테스트용 의도적 오류")


class TestLocalExecution:
    """로컬 실행 메커니즘 테스트"""

    def test_simple_pipeline_execution(self):
        """
        간단한 파이프라인 실행 테스트

        A → C
        B → D
        C, D → E
        """
        # 파이프라인 생성
        pipeline = Pipeline(name="test_simple_pipeline")

        # 노드 생성 및 추가
        from qmtl.sdk.node import SourceNode

        node_a = SourceNode(
            name="A",
            source=type("S", (), {"fetch": staticmethod(node_a_fn)})(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_b = SourceNode(
            name="B",
            source=type("S", (), {"fetch": staticmethod(node_b_fn)})(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_c = ProcessingNode(
            name="C",
            fn=node_c_fn,
            upstreams=["A"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_d = ProcessingNode(
            name="D",
            fn=node_d_fn,
            upstreams=["B"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_e = ProcessingNode(
            name="E",
            fn=node_e_fn,
            upstreams=["C", "D"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )

        pipeline.nodes["A"] = node_a
        pipeline.nodes["B"] = node_b
        pipeline.add_node(node_c)
        pipeline.add_node(node_d)
        pipeline.add_node(node_e)

        # 실행
        results = pipeline.execute(test_mode=True, debug=True)

        # 결과 검증
        assert "A" in results
        assert "B" in results
        assert "C" in results
        assert "D" in results
        assert "E" in results

        assert results["A"] == 42
        assert results["B"] == "hello"
        assert results["C"] == 84  # 42 * 2
        assert results["D"] == "hello world"
        assert results["E"] == "hello world (84)"

        # 실행 순서 검증 (위상 정렬)
        execution_order = pipeline.get_execution_order()

        # A와 B는 의존성이 없으므로 순서는 상관없지만,
        # C는 A 이후, D는 B 이후, E는 C와 D 이후에 와야함
        assert execution_order.index("C") > execution_order.index("A")
        assert execution_order.index("D") > execution_order.index("B")
        assert execution_order.index("E") > execution_order.index("C")
        assert execution_order.index("E") > execution_order.index("D")

    def test_complex_pipeline_execution(self):
        """복잡한 의존성을 가진 파이프라인 실행 테스트"""
        # 파이프라인 생성
        pipeline = Pipeline(name="test_complex_pipeline")

        # 노드 함수 정의
        def sum_fn(a, b):
            return a + b

        def mul_fn(a, c):
            return a * c

        def div_fn(d, e):
            return d / e

        # 노드 생성 및 추가 (복잡한 의존성 포함)
        from qmtl.sdk.node import SourceNode

        node_a = SourceNode(
            name="A",
            source=type("S", (), {"fetch": staticmethod(lambda: 10)})(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_b = SourceNode(
            name="B",
            source=type("S", (), {"fetch": staticmethod(lambda: 5)})(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_c = SourceNode(
            name="C",
            source=type("S", (), {"fetch": staticmethod(lambda: 2)})(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_d = ProcessingNode(
            name="D",
            fn=sum_fn,
            upstreams=["A", "B"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )  # 10 + 5 = 15
        node_e = ProcessingNode(
            name="E",
            fn=mul_fn,
            upstreams=["A", "C"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )  # 10 * 2 = 20
        node_f = ProcessingNode(
            name="F",
            fn=div_fn,
            upstreams=["D", "E"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )  # 15 / 20 = 0.75

        pipeline.nodes["A"] = node_a
        pipeline.nodes["B"] = node_b
        pipeline.nodes["C"] = node_c
        pipeline.add_node(node_d)
        pipeline.add_node(node_e)
        pipeline.add_node(node_f)

        # 실행
        results = pipeline.execute(test_mode=True)

        # 결과 검증
        assert results["A"] == 10
        assert results["B"] == 5
        assert results["C"] == 2
        assert results["D"] == 15
        assert results["E"] == 20
        assert results["F"] == 0.75

        # 각 노드의 업스트림 노드가 먼저 실행되었는지 검증
        execution_order = pipeline.get_execution_order()
        for node_name, node in pipeline.nodes.items():
            for upstream in node.upstreams:
                assert execution_order.index(upstream) < execution_order.index(
                    node_name
                ), f"노드 {node_name}의 업스트림 {upstream}이 먼저 실행되지 않았습니다."

    def test_pipeline_with_inputs(self):
        """외부 입력이 있는 파이프라인 실행 테스트"""
        # 파이프라인 생성
        pipeline = Pipeline(name="test_pipeline_with_inputs")

        # 노드 함수 정의
        def process_input(value):
            return value * 2

        def combine_inputs(a, b):
            return a + b  # 단순 합산

        # 노드 생성 및 추가
        from qmtl.sdk.node import SourceNode

        node_a = SourceNode(
            name="A",
            source=type("S", (), {"fetch": staticmethod(lambda: 10)})(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_b = SourceNode(
            name="B",
            source=type("S", (), {"fetch": staticmethod(lambda: 20)})(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_c = ProcessingNode(
            name="C",
            fn=combine_inputs,
            upstreams=["A", "B"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )

        pipeline.nodes["A"] = node_a
        pipeline.nodes["B"] = node_b
        pipeline.add_node(node_c)

        # 실행
        results = pipeline.execute(test_mode=True)

        # 결과 검증
        assert results["A"] == 10
        assert results["B"] == 20
        assert results["C"] == 30

    def test_execution_time_tracking(self):
        """노드 실행 시간 추적 기능 테스트"""
        # 파이프라인 생성
        pipeline = Pipeline(name="test_execution_time")

        # 실행 시간이 다른 노드 함수 정의
        def fast_node():
            return 42

        def slow_node():
            time.sleep(0.1)  # 0.1초 지연
            return 100

        # 파라미터 이름을 업스트림 노드와 일치시키기 위해 수정된 함수
        def combine_node(a, b):
            return a + b

        # 노드 생성 및 추가
        from qmtl.sdk.node import SourceNode

        node_a = SourceNode(
            name="A",
            source=type("S", (), {"fetch": staticmethod(fast_node)})(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_b = SourceNode(
            name="B",
            source=type("S", (), {"fetch": staticmethod(slow_node)})(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_c = ProcessingNode(
            name="C",
            fn=combine_node,
            upstreams=["A", "B"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        pipeline.nodes["A"] = node_a
        pipeline.nodes["B"] = node_b
        pipeline.add_node(node_c)

        # 실행 엔진 직접 생성
        engine = LocalExecutionEngine(debug=True)

        # 실행
        results = engine.execute_pipeline(pipeline)

        # 결과 검증
        assert results["A"] == 42
        assert results["B"] == 100
        assert results["C"] == 142

        # 실행 시간 검증
        stats = engine.get_execution_stats()
        assert "node_execution_times" in stats
        assert "A" in stats["node_execution_times"]
        assert "B" in stats["node_execution_times"]
        assert "C" in stats["node_execution_times"]

        # 빠른 노드(A)의 실행 시간이 느린 노드(B)보다 짧은지 검증
        assert stats["node_execution_times"]["A"] < stats["node_execution_times"]["B"]

        # 총 노드 수 검증
        assert stats["total_nodes"] == 3

        # 총 실행 시간 검증 (각 노드 실행 시간의 합)
        assert stats["total_time"] == sum(stats["node_execution_times"].values())

    def test_error_handling(self):
        """오류 처리 기능 테스트"""
        # 파이프라인 생성
        pipeline = Pipeline(name="test_error_handling")

        # 이름이 유지되면서 파라미터 수정된 함수
        def node_with_custom_error(a):
            # 명시적으로 의도적인 오류 발생시키기
            raise ValueError("테스트용 의도적 오류")

        # 노드 생성 및 추가
        from qmtl.sdk.node import SourceNode

        node_a = SourceNode(
            name="A",
            source=type("S", (), {"fetch": staticmethod(node_a_fn)})(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_error = ProcessingNode(
            name="Error",
            fn=node_with_custom_error,
            upstreams=["A"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )

        pipeline.nodes["A"] = node_a
        pipeline.add_node(node_error)

        # 오류 발생 예상
        with pytest.raises(RuntimeError) as excinfo:
            pipeline.execute(test_mode=True)

        # 오류 메시지 검증
        assert "오류 발생" in str(excinfo.value)
        assert "테스트용 의도적 오류" in str(excinfo.value)

    def test_timeout_handling(self):
        """타임아웃 처리 기능 테스트"""
        # 파이프라인 생성
        pipeline = Pipeline(name="test_timeout")

        # 오래 걸리는 노드 함수 정의 (무한 루프는 사용하지 않음)
        def very_slow_node():
            """타임아웃보다 오래 걸리는 함수"""
            time.sleep(0.5)  # 0.5초 지연
            return 42

        # 노드 생성 및 추가
        node = ProcessingNode(
            name="SlowNode",
            fn=very_slow_node,
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        pipeline.add_node(node)

        # 매우 짧은 타임아웃으로 실행 (타임아웃이 발생해야 함)
        with pytest.raises(TimeoutError) as excinfo:
            pipeline.execute(test_mode=True, timeout=0.1)  # 0.1초 타임아웃

        # 오류 메시지 검증
        assert "타임아웃" in str(excinfo.value)

    def test_history_tracking(self):
        """히스토리 관리 기능 테스트"""
        # 파이프라인 생성
        pipeline = Pipeline(name="test_history")

        # 카운터를 이용한 고유한 값 생성 노드 함수
        counter = {"count": 0}

        def counter_node():
            counter["count"] += 1
            return counter["count"]

        # 노드 생성 (인터벌 설정 포함)
        from qmtl.sdk.node import SourceNode

        node_a = SourceNode(
            name="A",
            source=type("S", (), {"fetch": staticmethod(counter_node)})(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        pipeline.nodes["A"] = node_a

        # 로컬 실행 엔진 생성
        engine = LocalExecutionEngine()
        # 히스토리 초기화 (static 변수 누적 방지)
        if "A" in engine.history and "1d" in engine.history["A"]:
            engine.history["A"]["1d"] = []

        # 실행 (여러 번 실행하여 히스토리 쌓기)
        for i in range(6):  # max_history(5)보다 많이 실행
            engine.execute_pipeline(pipeline)

        # 히스토리 데이터 검증
        assert "A" in engine.history
        assert "1d" in engine.history["A"]

        # 최신 5개 값이 올바르게 쌓였는지 검증
        assert [item["value"] for item in engine.history["A"]["1d"]][:5] == [6, 5, 4, 3, 2]

    def test_multiple_upstreams_with_same_name(self):
        """
        동일한 이름의 여러 업스트림 처리 테스트
        (키워드 인자로 모든 업스트림 결과를 받는 노드)
        """
        # 파이프라인 생성
        pipeline = Pipeline(name="test_multiple_upstreams")

        # 노드 생성 및 추가
        from qmtl.sdk.node import SourceNode

        node_a = SourceNode(
            name="A",
            source=type("S", (), {"fetch": staticmethod(lambda: 5)})(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_b = SourceNode(
            name="B",
            source=type("S", (), {"fetch": staticmethod(lambda: "text")})(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_c = SourceNode(
            name="C",
            source=type("S", (), {"fetch": staticmethod(lambda: 10)})(),
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )
        node_f = ProcessingNode(
            name="F",
            fn=node_f_fn,
            upstreams=["A", "B", "C"],
            stream_settings=NodeStreamSettings(
                intervals={IntervalEnum.DAY: IntervalSettings(interval=IntervalEnum.DAY, period=1)}
            ),
        )

        pipeline.nodes["A"] = node_a
        pipeline.nodes["B"] = node_b
        pipeline.nodes["C"] = node_c
        pipeline.add_node(node_f)

        # 실행
        results = pipeline.execute(test_mode=True)

        # 결과 검증 (node_f_fn은 모든 값의 길이 또는 값을 합산)
        # 5 + 4 (len("text")) + 10 = 19
        assert results["F"] == 19
