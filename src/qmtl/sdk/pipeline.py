"""
Pipeline class for QMTL SDK.

This module provides the Pipeline class which serves as the main entry point
for creating data processing pipelines in QMTL.
"""

from typing import Any, Dict, List, Optional, Set

from qmtl.sdk.models import QueryNodeResultSelector
from qmtl.sdk.node import ProcessingNode, QueryNode
from qmtl.sdk.visualization import visualize_pipeline
from qmtl.sdk.models import IntervalSettings, IntervalEnum


class Pipeline:
    """
    전략 파이프라인의 추상 인터페이스.

    여러 노드를 포함하는 파이프라인을 정의하고 실행하는 클래스입니다.
    PyTorch 스타일의 선언적 API를 제공합니다.
    """

    def __init__(
        self,
        name: str,
        default_intervals: Optional[Dict[IntervalEnum, "IntervalSettings"]] = None,
        **kwargs,
    ):
        """
        파이프라인 초기화

        Args:
            name: 파이프라인의 고유 이름
            default_intervals: 파이프라인 전체에 공용으로 적용할 interval별 IntervalSettings (Enum 기반)
            **kwargs: 파이프라인 설정 및 메타데이터
        """
        self.name = name
        self.kwargs = kwargs
        self.nodes = {}  # name -> ProcessingNode
        self.query_nodes = {}  # name -> QueryNode
        self.execution_order = []  # 실행 순서 (위상 정렬 결과)
        self.results_cache = {}  # 실행 결과 캐시
        self.default_intervals = default_intervals or {}

    def _apply_default_intervals(self, node):
        """
        노드의 stream_settings에 없는 interval/period를 파이프라인의 default_intervals로 보완 (Enum 기반)
        """
        from qmtl.sdk.models import NodeStreamSettings

        if not hasattr(node, "stream_settings") or node.stream_settings is None:
            if not self.default_intervals or len(self.default_intervals) == 0:
                raise ValueError(
                    f"노드 '{getattr(node, 'name', '?')}'의 stream_settings가 없고, "
                    f"파이프라인 default_intervals도 없습니다. 최소 1개 이상의 interval이 필요합니다."
                )
            node.stream_settings = NodeStreamSettings(intervals=self.default_intervals.copy())
        intervals = node.stream_settings.intervals
        # intervals가 비어 있으면 default_intervals로 대체, 없으면 명확한 예외 발생
        if not intervals or len(intervals) == 0:
            if not self.default_intervals or len(self.default_intervals) == 0:
                raise ValueError(
                    f"노드 '{getattr(node, 'name', '?')}'의 intervals가 비어 있고, "
                    f"파이프라인 default_intervals도 없습니다. 최소 1개 이상의 interval이 필요합니다."
                )
            node.stream_settings = NodeStreamSettings(intervals=self.default_intervals.copy())
            intervals = node.stream_settings.intervals
        else:
            # 파이프라인의 default_intervals에서 누락된 interval/period 보완
            for interval_key, default_setting in self.default_intervals.items():
                if interval_key not in intervals:
                    intervals[interval_key] = default_setting
                else:
                    # period가 1(기본값) 또는 None이면 default의 period로 보완
                    period = getattr(intervals[interval_key], "period", None)
                    if period is None or period == 1:
                        intervals[interval_key].period = default_setting.period
        # intervals와 default_intervals를 합쳐서 모든 interval에 대해 period가 반드시 지정되어야 함
        all_intervals = dict(self.default_intervals)
        all_intervals.update(intervals)
        for k, v in all_intervals.items():
            period_val = getattr(v, "period", None) or (
                v.get("period") if isinstance(v, dict) else None
            )
            if period_val is None:
                raise ValueError(
                    f"노드 '{getattr(node, 'name', '?')}'의 interval '{k}'에 period가 누락되었습니다. "
                    f"(파이프라인 default_intervals에도 없음)"
                )
        # intervals가 1개 이상인지, 각 interval에 interval 필드가 있는지 최종 검증
        if not intervals or len(intervals) == 0:
            raise ValueError(f"노드 '{getattr(node, 'name', '?')}'의 intervals가 비어 있습니다.")
        for k, v in intervals.items():
            interval_val = getattr(v, "interval", None) or (
                v.get("interval") if isinstance(v, dict) else None
            )
            if not interval_val:
                raise ValueError(
                    f"노드 '{getattr(node, 'name', '?')}'의 intervals[{k}]에 interval 필드가 누락되었습니다."
                )

    def add_node(self, node: ProcessingNode) -> ProcessingNode:
        """
        파이프라인에 노드를 추가합니다.

        Args:
            node: 추가할 노드 객체

        Returns:
            추가된 노드 객체

        Raises:
            ValueError: 이미 동일한 이름의 노드가 존재하는 경우
        """
        if node.name in self.nodes:
            raise ValueError(f"노드 '{node.name}'가 이미 파이프라인에 존재합니다.")

        # default_intervals 적용
        self._apply_default_intervals(node)

        # 노드 등록
        self.nodes[node.name] = node

        # 실행 순서 무효화 (다시 계산 필요)
        self.execution_order = []

        return node

    def add_query_node(self, node: QueryNode) -> str:
        """
        파이프라인에 쿼리 노드를 추가합니다.

        Args:
            node: 추가할 쿼리 노드 객체

        Returns:
            추가된 쿼리 노드의 이름 (다운스트림 노드에서 참조 가능)

        Raises:
            ValueError: 이미 동일한 이름의 노드가 존재하는 경우
        """
        if node.name in self.nodes or node.name in self.query_nodes:
            raise ValueError(f"노드 '{node.name}'가 이미 파이프라인에 존재합니다.")

        # default_intervals 적용
        self._apply_default_intervals(node)

        # 쿼리 노드 등록
        self.query_nodes[node.name] = node

        # 실행 순서 무효화 (다시 계산 필요)
        self.execution_order = []

        return node.name

    def get_node(self, name: str) -> Optional[ProcessingNode]:
        """
        이름으로 노드를 조회합니다.

        Args:
            name: 노드 이름

        Returns:
            해당 이름의 노드 또는 None (존재하지 않는 경우)
        """
        return self.nodes.get(name)

    def get_dependencies(self) -> Dict[str, Set[str]]:
        """
        모든 노드와 해당 의존성을 포함하는 사전을 반환합니다.

        Returns:
            노드 이름을 키로 하고 업스트림 노드 이름 집합을 값으로 하는 사전
        """
        dependencies = {}
        for name, node in self.nodes.items():
            dependencies[name] = set(node.upstreams)
        return dependencies

    def _validate_dependencies(self) -> bool:
        """
        모든 노드의 의존성이 유효한지 검사합니다.

        Returns:
            모든 의존성이 유효하면 True, 아니면 False

        Raises:
            ValueError: 누락된 의존성이 발견된 경우
        """
        for name, node in self.nodes.items():
            for upstream in node.upstreams:
                if upstream not in self.nodes:
                    raise ValueError(
                        f"노드 '{name}'가 존재하지 않는 업스트림 '{upstream}'을 참조합니다."
                    )
        return True

    def _topological_sort(self) -> List[str]:
        """
        노드 간 의존성을 기반으로 실행 순서를 위상 정렬합니다.

        Returns:
            노드 이름의 정렬된 리스트

        Raises:
            ValueError: 순환 의존성이 감지된 경우
        """
        # 의존성 유효성 검사
        self._validate_dependencies()

        # 그래프 구성
        graph = {}
        for name, node in self.nodes.items():
            graph[name] = set(node.upstreams)

        # 정렬 결과
        result = []

        # 방문 상태 (0: 미방문, 1: 현재 경로에서 방문 중, 2: 완료)
        visited = {name: 0 for name in graph}

        def dfs(node):
            # 이미 처리 완료된 노드
            if visited[node] == 2:
                return

            # 순환 의존성 감지
            if visited[node] == 1:
                raise ValueError(f"순환 의존성이 감지되었습니다: {node}")

            # 현재 경로에서 방문 중으로 표시
            visited[node] = 1

            # 의존 노드 먼저 처리
            for upstream in graph[node]:
                dfs(upstream)

            # 처리 완료로 표시
            visited[node] = 2
            result.append(node)

        # 모든 노드에 대해 DFS 실행
        for node in graph:
            if visited[node] == 0:
                dfs(node)

        return result

    def get_execution_order(self) -> List[str]:
        """
        파이프라인의 노드 실행 순서를 반환합니다.

        Returns:
            위상 정렬된 노드 이름 리스트
        """
        if not self.execution_order:
            self.execution_order = self._topological_sort()
        return self.execution_order.copy()

    def _prepare_node_inputs(self, node: ProcessingNode, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        노드 실행을 위한 입력을 준비합니다.

        Args:
            node: 실행할 노드
            results: 지금까지의 실행 결과

        Returns:
            노드 실행을 위한 입력 딕셔너리

        Raises:
            ValueError: 필요한 업스트림 결과가 없는 경우
        """
        # 업스트림 결과 수집
        upstream_results = {}
        for upstream in node.upstreams:
            if upstream not in results:
                raise ValueError(f"노드 '{node.name}'의 업스트림 '{upstream}'의 결과가 없습니다.")
            upstream_results[upstream] = results[upstream]

        return upstream_results

    def execute(
        self,
        brokers: str = "localhost:9092",
        redis_uri: str = "redis://localhost:6379/0",
        timeout: Optional[float] = None,
        background: bool = False,
        inputs: Dict[str, Any] = None,
        test_mode: bool = False,
        debug: bool = False,
        parallel: bool = False,
        selectors: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        파이프라인을 실행합니다.

        로컬 실행 모드에서는 토폴로지 정렬에 따라 순차적으로 노드를 실행합니다.
        병렬/백그라운드/모킹 실행은 아직 지원하지 않습니다.
        """
        from qmtl.sdk.execution import LocalExecutionEngine

        # 위상 정렬이 필요한 경우
        if not self.execution_order:
            self.execution_order = self._topological_sort()

        # 쿼리 노드 실행 및 결과 수집 지원
        query_results = {}
        if self.query_nodes:
            for qname, qnode in self.query_nodes.items():
                matched_nodes = self.find_nodes_by_query(qnode)
                node_list = matched_nodes
                # selectors 인자가 있으면 우선 적용, 없으면 쿼리노드의 result_selectors 적용
                selectors_to_apply = None
                if selectors and qname in selectors:
                    selectors_to_apply = selectors[qname]
                elif hasattr(qnode, "result_selectors") and qnode.result_selectors:
                    selectors_to_apply = qnode.result_selectors
                if selectors_to_apply:
                    node_list = self.apply_selectors(node_list, selectors_to_apply)
                node_results = {}
                for node in node_list:
                    if hasattr(self, "results_cache") and node.name in self.results_cache:
                        node_results[node.name] = self.results_cache[node.name]
                    else:
                        node_inputs = self._prepare_node_inputs(
                            node, self.results_cache if hasattr(self, "results_cache") else {}
                        )
                        try:
                            node_results[node.name] = node.execute(node_inputs)
                        except Exception:
                            node_results[node.name] = None
                query_results[qname] = node_results

        # 병렬/백그라운드/모킹 실행은 아직 미지원
        if parallel or background:
            raise NotImplementedError(
                "병렬 실행, 백그라운드 실행, 모킹 실행 엔진은 아직 지원하지 않습니다. LocalExecutionEngine만 사용 가능합니다."
            )

        # 로컬 실행 모드
        engine = LocalExecutionEngine(debug=debug)
        results = engine.execute_pipeline(self, inputs=inputs, timeout=timeout)
        self.results_cache = results.copy()
        self._local_engine = engine  # 실행 엔진 인스턴스 저장
        if query_results:
            results.update(query_results)
        return results

    # StateManager 클래스를 외부에서 patch/mocking 가능하도록 클래스 속성으로 분리
    state_manager_cls = None

    def get_history(
        self,
        node_name: str,
        interval: IntervalEnum = "1d",
        count: int = 10,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
        redis_uri: str = "local",
    ) -> List[Any]:
        """
        특정 노드의 히스토리 데이터를 가져옵니다.
        (로컬 실행: Node 객체의 get_history만 사용, 분산/컨테이너 환경: Redis StateManager 사용)
        """
        if node_name not in self.nodes:
            raise ValueError(f"존재하지 않는 노드: {node_name}")
        node = self.nodes[node_name]
        # redis_uri가 명시적으로 redis URI인 경우(StateManager 사용)
        if redis_uri and redis_uri != "local":
            try:
                # StateManager 클래스를 클래스 속성에서 가져오도록 변경 (patch/mocking 지원)
                cls = (
                    self.state_manager_cls
                    if self.state_manager_cls is not None
                    else Pipeline.state_manager_cls
                )
                if cls is None:
                    from qmtl.sdk.execution import StateManager

                    cls = StateManager
                    Pipeline.state_manager_cls = StateManager
                state_manager = cls(redis_uri=redis_uri)
                items = state_manager.get_history(
                    node_id=node.node_id,
                    interval=interval,
                    count=count,
                    start_ts=start_ts,
                    end_ts=end_ts,
                )
                # dict 리스트면 그대로 반환 (count 슬라이싱은 StateManager에서 담당)
                return items
            except Exception as e:
                import logging

                logging.warning(f"Redis에서 히스토리 조회 중 오류 발생: {e}")
                return []
        # pipeline.results_cache 기반 로컬 실행 결과 우선 반환
        if hasattr(self, "results_cache") and node_name in self.results_cache:
            return [self.results_cache[node_name]]
        # Node 객체의 get_history 사용 (로컬 실행 캐시)
        if hasattr(node, "get_history"):
            local_hist = node.get_history(interval=interval, count=count)
            if local_hist:
                return local_hist
        # LocalExecutionEngine의 history 조회 (로컬 실행 시)
        if hasattr(self, "_local_engine") and hasattr(self._local_engine, "history"):
            engine_history = self._local_engine.history
            if node_name in engine_history and interval in engine_history[node_name]:
                results = engine_history[node_name][interval]
                # 중복 제거: value 기준으로 유니크 처리
                unique_items = []
                seen = set()
                for item in results:
                    val = item.get("value")
                    if val not in seen:
                        unique_items.append(item)
                        seen.add(val)
                return [item.get("value") for item in unique_items][-count:][::-1]
        # 기존: results_cache 기반 로컬 캐시 히스토리 반환
        if hasattr(node, "results_cache") and interval in node.results_cache:
            results = node.results_cache[interval]
            # 중복 제거: value 기준으로 유니크 처리
            unique_items = []
            seen = set()
            for item in results:
                val = item.get("value")
                if val not in seen:
                    unique_items.append(item)
                    seen.add(val)
            return [item.get("value") for item in unique_items][-count:][::-1]
        return []

    def get_interval_data(
        self,
        node_name: str,
        interval: IntervalEnum = "1d",
        count: int = 1,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
        redis_uri: str = "redis://localhost:6379/0",
    ) -> List[Any]:
        """
        특정 노드의 인터벌 데이터만 가져옵니다. (타임스탬프 없이 값만 반환)
        """
        history = self.get_history(
            node_name=node_name,
            interval=interval,
            count=count,
            start_ts=start_ts,
            end_ts=end_ts,
            redis_uri=redis_uri,
        )
        # history가 dict 리스트면 value만 추출, 아니면 그대로 반환
        if history and isinstance(history[0], dict) and "value" in history[0]:
            return [item["value"] for item in history]
        return history

    def get_node_metadata(
        self,
        node_name: str,
        interval: IntervalEnum = "1d",
        redis_uri: str = "redis://localhost:6379/0",
    ) -> Dict[str, Any]:
        """
        특정 노드의 히스토리 메타데이터를 가져옵니다.

        Args:
            node_name: 노드 이름
            interval: 인터벌 (예: "1d", "1h")
            redis_uri: Redis 연결 URI

        Returns:
            메타데이터 딕셔너리 (last_update, count, max_items, ttl 등)

        Raises:
            ValueError: 존재하지 않는 노드인 경우
        """
        if node_name not in self.nodes:
            raise ValueError(f"노드 '{node_name}'가 존재하지 않습니다.")

        node = self.nodes[node_name]

        # 로컬 히스토리 확인
        from qmtl.sdk.execution import LocalExecutionEngine

        try:
            engine = LocalExecutionEngine()
            if (
                hasattr(engine, "history")
                and node_name in engine.history
                and interval in engine.history[node_name]
            ):
                history = engine.history[node_name][interval]
                return {
                    "count": len(history),
                    "last_update": history[0].get("timestamp") if history else None,
                    "source": "local",
                }
        except Exception:
            pass

        # Redis에서 메타데이터 조회
        try:
            from qmtl.sdk.execution import StateManager

            # Redis 패키지 확인
            try:
                redis_available = True
            except ImportError:
                redis_available = False

            if redis_available:
                # StateManager 인스턴스 생성
                state_manager = StateManager(redis_uri=redis_uri)

                # 메타데이터 조회
                meta = state_manager.get_history_metadata(node_id=node.node_id, interval=interval)

                if meta:
                    meta["source"] = "redis"
                    return meta
        except Exception as e:
            import logging

            logging.warning(f"Redis에서 메타데이터 조회 중 오류 발생: {e}")

        # 기본 메타데이터 반환
        return {"count": 0, "last_update": None, "source": "none"}

    def to_definition(self) -> Dict[str, Any]:
        """
        파이프라인을 직렬화 가능한 딕셔너리로 변환합니다.

        Returns:
            파이프라인 정의 딕셔너리
        """
        return {
            "name": self.name,
            "nodes": [node.to_definition() for node in self.nodes.values()],
            "query_nodes": [node.to_definition() for node in self.query_nodes.values()],
            "metadata": self.kwargs,
        }

    def visualize(self) -> None:
        """
        파이프라인 DAG를 시각화합니다. (networkx와 matplotlib 필요)
        호출 시 그래프가 화면에 표시됩니다.
        """
        visualize_pipeline(self.nodes, pipeline_name=self.name)

    def __repr__(self) -> str:
        node_count = len(self.nodes)
        query_node_count = len(self.query_nodes)
        return f"Pipeline(name='{self.name}', nodes={node_count}, query_nodes={query_node_count})"

    def find_nodes_by_query(self, query_node: "QueryNode") -> List["ProcessingNode"]:
        """
        QueryNode의 조건(tags, interval, period)에 맞는 실제 노드 리스트 반환
        AND 조건 기반 필터링
        """
        result = []
        for node in self.nodes.values():
            # 태그 필터 (AND)
            if query_node.query_tags:
                if not all(tag in (node.tags or []) for tag in query_node.query_tags):
                    continue

            # interval 필터
            if query_node.interval:
                node_interval = None
                if hasattr(node, "stream_settings") and node.stream_settings:
                    # 모든 interval을 순회하면서 일치하는 것이 있는지 확인
                    intervals = getattr(node.stream_settings, "intervals", {})
                    for interval_key, interval_setting in intervals.items():
                        if (
                            hasattr(interval_setting, "interval")
                            and interval_setting.interval == query_node.interval
                        ):
                            node_interval = query_node.interval
                            break
                # 하위 호환성을 위한 interval_settings 체크
                elif hasattr(node, "interval_settings") and node.interval_settings:
                    interval_settings = node.interval_settings
                    if isinstance(interval_settings, dict):
                        if "interval" in interval_settings:
                            node_interval = interval_settings["interval"]
                        # 중첩된 딕셔너리 처리
                        else:
                            for key, setting in interval_settings.items():
                                if (
                                    isinstance(setting, dict)
                                    and setting.get("interval") == query_node.interval
                                ):
                                    node_interval = query_node.interval
                                    break

                if node_interval != query_node.interval:
                    continue

            # period 필터
            if query_node.period:
                node_period = None
                if hasattr(node, "stream_settings") and node.stream_settings:
                    # 모든 interval을 순회하면서 일치하는 것이 있는지 확인
                    intervals = getattr(node.stream_settings, "intervals", {})
                    for interval_key, interval_setting in intervals.items():
                        if (
                            hasattr(interval_setting, "period")
                            and interval_setting.period == query_node.period
                        ):
                            node_period = query_node.period
                            break
                # 하위 호환성을 위한 interval_settings 체크
                elif hasattr(node, "interval_settings") and node.interval_settings:
                    interval_settings = node.interval_settings
                    if isinstance(interval_settings, dict):
                        if "period" in interval_settings:
                            node_period = interval_settings["period"]
                        # 중첩된 딕셔너리 처리
                        else:
                            for key, setting in interval_settings.items():
                                if (
                                    isinstance(setting, dict)
                                    and setting.get("period") == query_node.period
                                ):
                                    node_period = query_node.period
                                    break

                if node_period != query_node.period:
                    continue

            result.append(node)
        return result

    def apply_selectors(
        self, nodes: List["ProcessingNode"], selectors: List["QueryNodeResultSelector"]
    ) -> List["ProcessingNode"]:
        """
        QueryNode 결과 노드 리스트에 selector(중간 API)들을 순차적으로(체이닝) 적용합니다.
        Args:
            nodes: QueryNode로 필터링된 노드 리스트
            selectors: QueryNodeResultSelector 리스트(순서대로 적용)
        Returns:
            selector가 모두 적용된 최종 노드 리스트
        """
        for selector in selectors:
            if selector.mode == "list":
                continue  # 그대로 반환
            elif selector.mode == "batch":
                batch_size = selector.batch_size or 1
                # batch 모드는 리스트를 n개씩 묶어 반환(여기선 평탄화)
                batched = [nodes[i : i + batch_size] for i in range(0, len(nodes), batch_size)]
                nodes = [item for batch in batched for item in batch]
            elif selector.mode == "random":
                import random

                sample_size = selector.sample_size or 1
                # 노드가 비어있으면 에러 방지
                if nodes:
                    nodes = random.sample(nodes, min(sample_size, len(nodes)))
            elif selector.mode == "filter":
                meta = selector.filter_meta or {}

                def match(node):
                    # 업데이트: stream_settings 또는 interval_settings 지원
                    for k, v in meta.items():
                        if k == "stream_settings":
                            # stream_settings 구조 검사
                            if not hasattr(node, "stream_settings"):
                                return False
                            # intervals 구조가 있는지 확인
                            if "intervals" in v:
                                if not hasattr(node.stream_settings, "intervals"):
                                    return False
                                # intervals 내 각 인터벌 확인
                                for interval_key, interval_value in v["intervals"].items():
                                    if interval_key not in node.stream_settings.intervals:
                                        return False
                                    # 각 interval 설정의 속성 확인
                                    interval_obj = node.stream_settings.intervals[interval_key]
                                    for attr_k, attr_v in interval_value.items():
                                        if (
                                            not hasattr(interval_obj, attr_k)
                                            or getattr(interval_obj, attr_k) != attr_v
                                        ):
                                            return False
                            return True
                        # 하위 호환성을 위한 interval_settings 지원
                        elif k == "interval_settings":
                            if not hasattr(node, "stream_settings") or not hasattr(
                                node.stream_settings, "intervals"
                            ):
                                if not hasattr(node, "interval_settings"):
                                    return False
                                # interval_settings가 있으면 그 값을 확인
                                for attr_k, attr_v in v.items():
                                    if attr_k not in node.interval_settings:
                                        return False
                                    if node.interval_settings[attr_k] != attr_v:
                                        return False
                            else:
                                # stream_settings로 매핑하여 확인
                                for attr_k, attr_v in v.items():
                                    found = False
                                    for (
                                        interval_key,
                                        interval_obj,
                                    ) in node.stream_settings.intervals.items():
                                        if (
                                            hasattr(interval_obj, attr_k)
                                            and getattr(interval_obj, attr_k) == attr_v
                                        ):
                                            found = True
                                            break
                                    if not found:
                                        return False
                            return True
                        # 일반 속성 검사
                        elif not hasattr(node, k) or getattr(node, k) != v:
                            return False
                    return True

                nodes = [n for n in nodes if match(n)]
        return nodes
