import time
from typing import Any, Dict, Optional

from .base import BaseExecutionEngine


class LocalExecutionEngine(BaseExecutionEngine):
    """
    로컬 실행 엔진
    파이프라인을 로컬에서 효율적으로 실행하는 엔진입니다.
    토폴로지 정렬을 사용하여 의존성 순서대로 노드를 실행하고,
    노드 간 데이터 전달과 결과 수집을 처리합니다.
    외부 의존성(Kafka, Redis)이 필요하지 않으며 단일 프로세스에서 동작합니다.
    """

    history = {}
    # 메모리 내 인터벌 데이터 캐시
    _in_memory_cache = {}

    def __init__(self, debug: bool = False):
        super().__init__(debug=debug)
        # history는 클래스 변수로 공유

    def execute_pipeline(
        self, pipeline, inputs: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        if not pipeline.execution_order:
            pipeline.execution_order = pipeline._topological_sort()
        self.results = {} if inputs is None else inputs.copy()
        if not hasattr(LocalExecutionEngine, "history"):
            LocalExecutionEngine.history = {}
        if self.debug:
            print(f"파이프라인 '{pipeline.name}' 실행 시작 (노드 {len(pipeline.nodes)}개)")
            print(f"실행 순서: {pipeline.execution_order}")
            if inputs:
                print(f"초기 입력: {list(inputs.keys())}")
        for node_name in pipeline.execution_order:
            if timeout and (time.time() - start_time > timeout):
                raise TimeoutError(f"파이프라인 실행 제한 시간 {timeout}초 초과")
            node = pipeline.nodes[node_name]
            # 업스트림이 없고, 외부 입력이 있는 경우: 입력값을 그대로 결과로 사용
            if inputs is not None and not node.upstreams and node_name in inputs:
                self.results[node_name] = inputs[node_name]
                continue
            # 초기 inputs에 지정되지 않고, upstream이 없는 노드는 건너뜀 (메모리 테스트 지원)
            if inputs is not None and not node.upstreams and node_name not in inputs:
                continue
            # 입력값이 있고 업스트림이 없는 노드는 항상 입력값을 함수에 넘겨서 실행
            if node_name in self.results and not node.upstreams and inputs is not None:
                node_inputs = self._prepare_node_inputs(node, self.results)
                result = node.execute(node_inputs)
                self.results[node_name] = result
            elif node_name in self.results and not node.upstreams:
                # 입력값만 사용하는 노드도 동일하게 기록
                result = self.results[node_name]
            else:
                node_inputs = self._prepare_node_inputs(node, self.results)
                node_start_time = time.time()
                if self.debug:
                    upstream_info = f" (업스트림: {node.upstreams})" if node.upstreams else ""
                    print(f"노드 '{node_name}' 실행 중{upstream_info}...")
                try:
                    execution_start_time = time.time()
                    if timeout:
                        wrapper_node = {
                            "fn": node.fn,
                            "start_time": execution_start_time,
                            "timeout_threshold": timeout - (execution_start_time - start_time),
                            "last_check": execution_start_time,
                        }

                        def timeout_checked_fn(**kwargs):
                            current_time = time.time()
                            if current_time - wrapper_node["last_check"] > 0.05:
                                wrapper_node["last_check"] = current_time
                                elapsed_time = current_time - start_time
                                if elapsed_time > timeout:
                                    raise TimeoutError(
                                        f"파이프라인 실행 제한 시간 {timeout}초 초과"
                                    )
                            return wrapper_node["fn"](**kwargs)

                        original_fn = node.fn
                        node.fn = timeout_checked_fn
                        try:
                            result = node.execute(node_inputs)
                        finally:
                            node.fn = original_fn
                    else:
                        result = node.execute(node_inputs)
                except Exception as e:
                    error_msg = f"노드 '{node_name}' 실행 중 오류 발생: {str(e)}"
                    if self.debug:
                        print(f"❌ {error_msg}")
                    raise RuntimeError(error_msg) from e
                self.results[node_name] = result
                execution_time = time.time() - node_start_time
                self.node_execution_times[node_name] = execution_time
                if self.debug:
                    result_preview = (
                        str(result)[:50] + "..." if len(str(result)) > 50 else str(result)
                    )
                    print(
                        f"노드 '{node_name}' 실행 완료 ({execution_time:.4f}초): {result_preview}"
                    )

                # 노드 실행 후 총 경과 시간이 timeout을 초과했는지 최종 확인
                if timeout and (time.time() - start_time > timeout):
                    raise TimeoutError(f"파이프라인 실행 제한 시간 {timeout}초 초과")

            # 노드 결과 기록(모든 분기에서 단 한 번만)
            node_has_settings = bool(
                getattr(node, "stream_settings", None)
                and getattr(node.stream_settings, "intervals", {})
            )
            settings = {}
            if node_has_settings:
                if hasattr(node, "interval_settings") and node.interval_settings:
                    settings = node.interval_settings
                elif hasattr(node, "stream_settings") and hasattr(
                    node.stream_settings, "intervals"
                ):
                    settings = node.stream_settings.intervals
                for interval, interval_settings in settings.items():
                    if isinstance(interval_settings, dict):
                        max_history = interval_settings.get("max_history", 100)
                        ttl = interval_settings.get("ttl")
                        # TTL 추출 (예: '1d' -> 86400초) - ttl이 명시적으로 없으면 유추
                        if ttl is None:
                            try:
                                value = int(interval[:-1])
                                unit = interval[-1]
                                if unit == "d":
                                    ttl = value * 86400
                                elif unit == "h":
                                    ttl = value * 3600
                                elif unit == "m":
                                    ttl = value * 60
                            except (ValueError, IndexError):
                                ttl = None
                    else:
                        max_history = 100
                        ttl = None
                    self.save_interval_data(
                        node_name, interval, result, max_items=max_history, ttl=ttl
                    )
            else:
                # 기본 인터벌 '1d' 사용
                self.save_interval_data(node_name, "1d", result, max_items=100)
            # (구) results_cache 직접 조작 코드는 interval 저장 로직으로 대체되어 필요 없음
        total_execution_time = time.time() - start_time
        if self.debug:
            print(f"파이프라인 '{pipeline.name}' 실행 완료 (총 {total_execution_time:.4f}초)")
            print(f"결과 노드: {list(self.results.keys())}")

        # 모든 노드/인터벌에 대해 max_history 강제 적용
        for node_name, node in pipeline.nodes.items():
            if (
                hasattr(node, "stream_settings")
                and node.stream_settings
                and node.stream_settings.intervals
            ):
                for interval, interval_settings in node.stream_settings.intervals.items():
                    max_history = getattr(interval_settings, "max_history", 100)
                    # history
                    if node_name in self.history and interval in self.history[node_name]:
                        self.history[node_name][interval] = self.history[node_name][interval][
                            :max_history
                        ]
                    # in-memory cache
                    cache_key = f"{node_name}:{interval}"
                    if cache_key in self._in_memory_cache:
                        self._in_memory_cache[cache_key] = self._in_memory_cache[cache_key][
                            :max_history
                        ]

        return self.results.copy()

    def _prepare_node_inputs(self, node, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        노드 실행에 필요한 입력값을 준비합니다.
        Args:
            node: 실행할 노드
            results: 현재까지의 실행 결과
        Returns:
            노드 함수에 전달할 입력값 딕셔너리
        """
        # 업스트림이 없는 노드이면서 외부 입력이 이미 results에 있는 경우,
        # {노드이름: 값} 형태로 반환하여 Node.execute에서 정상적으로 매핑되도록 한다.
        if node.name in results and not node.upstreams:
            return {node.name: results[node.name]}
        node_inputs = {}
        for upstream in node.upstreams:
            if upstream not in results:
                raise ValueError(f"노드 '{node.name}'의 업스트림 '{upstream}'의 결과가 없습니다.")
            node_inputs[upstream] = results[upstream]
        return node_inputs

    def get_interval_data(self, node_id: str, interval: str = "1d", limit: int = 100) -> list:
        """
        노드의 인터벌별 기록 데이터를 가져옵니다.
        만료된 항목은 자동으로 제외합니다.
        Args:
            node_id: 조회할 노드 ID 또는 이름
            interval: 조회할 인터벌 (기본값: "1d")
            limit: 반환할 최대 항목 수
        Returns:
            타임스탬프별로 정렬된 데이터 목록 (최신 데이터가 먼저 옴)
        """
        current_time = time.time()
        items = []
        if node_id in self.history and interval in self.history[node_id]:
            items = self.history[node_id][interval]
        else:
            cache_key = f"{node_id}:{interval}"
            if cache_key in self._in_memory_cache:
                items = self._in_memory_cache[cache_key]
        # 만료된 항목 제외
        valid_items = [
            item
            for item in items
            if not item.get("expires_at") or item["expires_at"] > current_time
        ]
        return valid_items[:limit]

    def save_interval_data(
        self,
        node_id: str,
        interval: str,
        data: Any,
        max_items: int = 100,
        ttl: Optional[int] = None,
    ):
        """
        노드의 인터벌별 데이터를 저장합니다.
        Args:
            node_id: 저장할 노드 ID 또는 이름
            interval: 저장할 인터벌 (예: "1d", "1h")
            data: 저장할 데이터
            max_items: 인터벌별 최대 저장 항목 수 (초과 시 오래된 항목부터 삭제)
            ttl: 데이터 유효 기간(초) (None일 경우 만료 없음)
        """
        now = time.time()
        # ttl=0이면 즉시 만료 처리
        expires_at = now + ttl if ttl and ttl > 0 else (now if ttl == 0 else None)
        new_item = {"timestamp": now, "value": data, "expires_at": expires_at}

        # 캐시 키 생성
        cache_key = f"{node_id}:{interval}"

        # 메모리 캐시에 저장
        if cache_key not in self._in_memory_cache:
            self._in_memory_cache[cache_key] = []
        self._in_memory_cache[cache_key].insert(0, new_item)  # 최신 데이터를 앞에 추가

        # max_items 제한 적용
        if len(self._in_memory_cache[cache_key]) > max_items:
            self._in_memory_cache[cache_key] = self._in_memory_cache[cache_key][:max_items]

        # history에도 동일하게 저장 (하위 호환성 유지)
        if node_id not in self.history:
            self.history[node_id] = {}
        if interval not in self.history[node_id]:
            self.history[node_id][interval] = []
        self.history[node_id][interval].insert(0, new_item)  # 최신 데이터를 앞에 추가

        # max_items 제한 적용
        if len(self.history[node_id][interval]) > max_items:
            self.history[node_id][interval] = self.history[node_id][interval][:max_items]

    def _cleanup_expired_data(self):
        """
        만료된 캐시 데이터를 정리합니다.
        """
        current_time = time.time()

        # in-memory 캐시 정리
        for cache_key, items in list(self._in_memory_cache.items()):
            # 각 항목 리스트에서 만료되지 않은 항목만 필터링
            valid_items = [
                item
                for item in items
                if not item.get("expires_at") or item["expires_at"] > current_time
            ]
            if not valid_items:
                # 모든 항목이 만료된 경우 키 자체를 삭제
                del self._in_memory_cache[cache_key]
            else:
                self._in_memory_cache[cache_key] = valid_items

        # history 캐시 정리 (하위 호환성)
        for node_id, intervals in list(LocalExecutionEngine.history.items()):
            for interval, items in list(intervals.items()):
                valid_items = [
                    item
                    for item in items
                    if not item.get("expires_at") or item["expires_at"] > current_time
                ]
                if not valid_items:
                    del LocalExecutionEngine.history[node_id][interval]
                else:
                    LocalExecutionEngine.history[node_id][interval] = valid_items
            # 빈 노드 삭제
            if not LocalExecutionEngine.history[node_id]:
                del LocalExecutionEngine.history[node_id]

    def clear_cache(self, node_id: Optional[str] = None, interval: Optional[str] = None):
        """
        캐시 데이터를 지웁니다.

        Args:
            node_id: 특정 노드 ID만 지울 경우 지정 (None이면 모든 노드)
            interval: 특정 인터벌만 지울 경우 지정 (None이면 모든 인터벌)
        """
        # 모든 캐시 지우기
        if node_id is None:
            if interval is None:
                self._in_memory_cache.clear()
                LocalExecutionEngine.history.clear()
            else:
                # 특정 인터벌만 지우기
                for cache_key in list(self._in_memory_cache.keys()):
                    if cache_key.endswith(f":{interval}"):
                        del self._in_memory_cache[cache_key]
                for node_hist in LocalExecutionEngine.history.values():
                    if interval in node_hist:
                        del node_hist[interval]
        else:
            # 특정 노드만 지우기
            if interval is None:
                # 노드의 모든 인터벌 지우기
                for cache_key in list(self._in_memory_cache.keys()):
                    if cache_key.startswith(f"{node_id}:"):
                        del self._in_memory_cache[cache_key]
                if node_id in LocalExecutionEngine.history:
                    del LocalExecutionEngine.history[node_id]
            else:
                # 특정 노드의 특정 인터벌만 지우기
                cache_key = f"{node_id}:{interval}"
                if cache_key in self._in_memory_cache:
                    del self._in_memory_cache[cache_key]
                if (
                    node_id in LocalExecutionEngine.history
                    and interval in LocalExecutionEngine.history[node_id]
                ):
                    del LocalExecutionEngine.history[node_id][interval]

    def get_node_metadata(self, node_id: str) -> Dict[str, Any]:
        """
        노드 메타데이터를 가져옵니다.

        Args:
            node_id: 조회할 노드 ID 또는 이름

        Returns:
            노드 메타데이터 정보를 담은 딕셔너리
        """
        result = {
            "node_id": node_id,
            "intervals": {},
            "execution_times": {},
        }

        # 인터벌 정보 수집
        if node_id in LocalExecutionEngine.history:
            for interval, data in LocalExecutionEngine.history[node_id].items():
                if data:
                    latest = data[0]["timestamp"] if data else None
                    oldest = data[-1]["timestamp"] if data else None
                    result["intervals"][interval] = {
                        "count": len(data),
                        "latest_timestamp": latest,
                        "oldest_timestamp": oldest,
                    }

        # in-memory 캐시에서도 데이터 찾기
        for cache_key, data in self._in_memory_cache.items():
            if cache_key.startswith(f"{node_id}:"):
                interval = cache_key.split(":", 1)[1]
                if interval not in result["intervals"] and data:
                    latest = data[0]["timestamp"] if data else None
                    oldest = data[-1]["timestamp"] if data else None
                    result["intervals"][interval] = {
                        "count": len(data),
                        "latest_timestamp": latest,
                        "oldest_timestamp": oldest,
                    }

        # 실행 시간 정보 추가
        if node_id in self.node_execution_times:
            result["execution_times"]["last"] = self.node_execution_times[node_id]

        return result
