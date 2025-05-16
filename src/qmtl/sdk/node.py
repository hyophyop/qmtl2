"""
Node classes for QMTL SDK pipelines.

This module provides the Node and QueryNode classes which represent processing nodes
in a QMTL pipeline.
"""

import ast
import hashlib
import inspect
import json
from typing import Any, Callable, Dict, List, Optional
from abc import ABC, abstractmethod

from qmtl.sdk.models import (
    IntervalSettings,
    NodeStreamSettings,
    QueryNodeResultSelector,
)


class BaseNode(ABC):
    @abstractmethod
    def execute(self, *args, **kwargs): ...
    @abstractmethod
    def to_definition(self): ...


class ProcessingNode(BaseNode):
    """
    실제 연산/처리/파생 데이터 생성 노드 (기존 Node 역할)
    반드시 업스트림 필요, stream_settings 필수
    """

    def __init__(
        self,
        name: str,
        fn: Callable,
        tags: Optional[List[str]] = None,
        upstreams: Optional[List[str]] = None,
        key_params: Optional[List[str]] = None,
        interval_settings: Optional[Dict[str, Any]] = None,
        stream_settings: Optional[NodeStreamSettings] = None,
        **kwargs,
    ):
        if not upstreams or len(upstreams) == 0:
            raise ValueError(
                "ProcessingNode는 반드시 하나 이상의 업스트림을 가져야 합니다. 외부 입력/원천 데이터는 SourceNode 등 별도 추상화로 처리하세요."
            )
        self.name = name
        self.fn = fn
        self.tags = tags or []
        self.upstreams = upstreams or []
        self.key_params = key_params or []
        self.stream_settings = stream_settings
        self.kwargs = kwargs
        self.node_id = self._generate_node_id()
        self.results_cache = {}

    @staticmethod
    def _normalize_stream_settings(
        stream_settings: Optional[NodeStreamSettings], interval_settings: Optional[Dict[str, Any]]
    ) -> Optional[NodeStreamSettings]:
        if stream_settings is not None:
            return ProcessingNode._parse_stream_settings(stream_settings)
        elif interval_settings is not None:
            return ProcessingNode._parse_interval_settings(interval_settings)
        else:
            return None

    @staticmethod
    def _parse_stream_settings(stream_settings):
        if isinstance(stream_settings, NodeStreamSettings):
            return stream_settings
        elif isinstance(stream_settings, dict):
            return NodeStreamSettings(**stream_settings)
        else:
            raise ValueError("stream_settings는 NodeStreamSettings 또는 dict여야 합니다.")

    @staticmethod
    def _parse_interval_settings(interval_settings):
        if isinstance(interval_settings, NodeStreamSettings):
            return interval_settings
        elif isinstance(interval_settings, dict):
            intervals = {}
            for k, v in interval_settings.items():
                if isinstance(v, IntervalSettings):
                    intervals[k] = v
                elif isinstance(v, dict):
                    intervals[k] = IntervalSettings(**v)
            return NodeStreamSettings(intervals=intervals)
        else:
            raise ValueError("interval_settings는 dict 또는 NodeStreamSettings여야 합니다.")

    def _get_function_ast_source(self) -> str:
        if self.fn is None:
            return ""
        try:
            source = inspect.getsource(self.fn)
            source = inspect.cleandoc(source)
            tree = ast.parse(source)
            return ast.dump(tree, annotate_fields=True, include_attributes=False)
        except Exception:
            return str(self.fn)

    def _generate_node_id(self) -> str:
        # 1. 함수 객체의 __qualname__
        qualname = getattr(self.fn, "__qualname__", str(self.fn))
        # 2. 함수 소스코드(AST)
        fn_ast = self._get_function_ast_source()
        # 3. 업스트림 함수들의 __qualname__ 리스트 (업스트림이 노드 객체라면 .fn.__qualname__)
        upstream_qualnames = []
        for up in getattr(self, "upstreams", []):
            if hasattr(up, "fn") and hasattr(up.fn, "__qualname__"):
                upstream_qualnames.append(up.fn.__qualname__)
            elif hasattr(up, "__qualname__"):
                upstream_qualnames.append(up.__qualname__)
            elif isinstance(up, str):
                upstream_qualnames.append(up)
        # 4. stream_settings
        if self.stream_settings:
            stream_settings = self.stream_settings.model_dump()
        else:
            stream_settings = {}
        # 5. key_params 및 값
        key_params_dict = {}
        if self.key_params:
            for param in self.key_params:
                if param in self.kwargs:
                    key_params_dict[param] = self.kwargs[param]
        # dict로 묶어서 정렬
        signature_dict = {
            "qualname": qualname,
            "ast": fn_ast,
            "upstreams": upstream_qualnames,
            "stream_settings": stream_settings,
            "key_params": key_params_dict,
        }
        signature_str = json.dumps(signature_dict, sort_keys=True)
        return hashlib.md5(signature_str.encode("utf-8")).hexdigest()

    def execute(self, inputs: Dict[str, Any] = None, interval: str = "1d") -> Any:
        inputs = inputs or {}
        self._validate_upstreams(inputs)
        fn_args = self._build_fn_args(inputs)
        for k, v in self.kwargs.items():
            if k not in fn_args:
                fn_args[k] = v
        try:
            return self.fn(**fn_args)
        except Exception as e:
            raise RuntimeError(f"노드 '{self.name}' 실행 중 오류 발생: {str(e)}") from e

    def _validate_upstreams(self, inputs: Dict[str, Any]):
        for upstream in self.upstreams:
            if upstream not in inputs:
                raise ValueError(f"노드 '{self.name}'의 업스트림 '{upstream}'이 입력에 없습니다.")

    def _build_fn_args(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        sig = inspect.signature(self.fn)
        param_names = list(sig.parameters.keys())
        if not self.upstreams and len(inputs) > 0:
            return self._build_args_no_upstream(inputs, param_names)
        elif len(self.upstreams) == 1:
            return self._build_args_single_upstream(inputs, param_names)
        else:
            return self._build_args_multi_upstream(inputs, param_names, sig)

    def _build_args_no_upstream(
        self, inputs: Dict[str, Any], param_names: List[str]
    ) -> Dict[str, Any]:
        fn_args = {}
        if "value" in inputs and "value" in param_names:
            fn_args["value"] = inputs["value"]
        elif "value" in param_names and len(inputs) == 1:
            first_value = next(iter(inputs.values()))
            fn_args["value"] = first_value
        elif "upstream" in inputs and "value" in param_names:
            fn_args["value"] = inputs["upstream"]
        elif self.name in inputs and len(param_names) == 1:
            fn_args[param_names[0]] = inputs[self.name]
        elif node_name := next(iter(inputs), None):
            value = inputs[node_name]
            if isinstance(value, dict):
                for param_name in param_names:
                    if param_name in value:
                        fn_args[param_name] = value[param_name]
                if not fn_args and len(param_names) == 1:
                    fn_args = {param_names[0]: value}
            elif len(param_names) == 1:
                fn_args = {param_names[0]: value}
        return fn_args

    def _build_args_single_upstream(
        self, inputs: Dict[str, Any], param_names: List[str]
    ) -> Dict[str, Any]:
        fn_args = {}
        upstream = self.upstreams[0]
        value = inputs[upstream]
        if len(param_names) == 1:
            fn_args = {param_names[0]: value}
        else:
            fn_args[upstream] = value
        return fn_args

    def _build_args_multi_upstream(
        self, inputs: Dict[str, Any], param_names: List[str], sig
    ) -> Dict[str, Any]:
        fn_args = {}
        has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
        if has_kwargs:
            for upstream in self.upstreams:
                fn_args[upstream] = inputs[upstream]
        else:
            for i, upstream in enumerate(self.upstreams):
                if i < len(param_names):
                    fn_args[param_names[i]] = inputs[upstream]
        return fn_args

    def get_history(self, interval: str = "1d", count: int = 10) -> List[Any]:
        if hasattr(self, "results_cache") and isinstance(self.results_cache, dict):
            if interval in self.results_cache:
                results = self.results_cache[interval]
                unique_results = []
                seen = set()
                for item in results:
                    val = item.get("value")
                    if val not in seen:
                        unique_results.append(item)
                        seen.add(val)
                return [item["value"] for item in unique_results][-count:][::-1]
        return []

    def to_definition(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "node_id": self.node_id,
            "tags": self.tags,
            "upstreams": self.upstreams,
            "key_params": self.key_params,
            "stream_settings": self.stream_settings.model_dump() if self.stream_settings else {},
        }

    def __repr__(self) -> str:
        return (
            f"ProcessingNode(name='{self.name}', node_id='{self.node_id}', tags={self.tags}, "
            f"upstreams={self.upstreams})"
        )


class QueryNode(BaseNode):
    """
    태그 기반 쿼리 노드 (업스트림/stream_settings 강제 없음)
    """

    def __init__(
        self,
        name: str,
        tags: List[str],
        interval: Optional[str] = None,
        period: Optional[str] = None,
        stream_settings: Optional[NodeStreamSettings] = None,
        interval_settings: Optional[Dict[str, Any]] = None,
        result_selector: Optional[QueryNodeResultSelector] = None,
        result_selectors: Optional[List[QueryNodeResultSelector]] = None,
        **kwargs,
    ):
        self.name = name
        self.tags = tags
        self.interval = interval
        self.period = period
        self.stream_settings = stream_settings
        self.interval_settings = interval_settings
        self.result_selectors = result_selectors or (
            [] if result_selector is None else [result_selector]
        )
        if result_selector and not self.result_selectors:
            self.result_selectors = [result_selector]
        elif result_selector and result_selector not in self.result_selectors:
            self.result_selectors.append(result_selector)
        self.query_tags = tags
        self.node_id = name
        self.upstreams = []
        self.key_params = []
        self.kwargs = kwargs
        self.results_cache = {}

    def execute(self, *args, **kwargs):
        raise NotImplementedError(
            "QueryNode는 직접 실행되지 않습니다. Analyzer/파이프라인에서만 사용"
        )

    def to_definition(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "node_id": self.node_id,
            "tags": self.tags,
            "upstreams": self.upstreams,
            "key_params": self.key_params,
            "stream_settings": self.stream_settings.model_dump() if self.stream_settings else {},
            "interval": self.interval,
            "period": self.period,
            "query_tags": self.query_tags,
        }

    def __repr__(self) -> str:
        return (
            f"QueryNode(name='{self.name}', tags={self.tags}, "
            f"interval='{self.interval}', period='{self.period}')"
        )


class SourceProcessor(ABC):
    """
    외부 데이터/원천 데이터/파일/DB 등 다양한 입력 소스를 표준화하는 추상 클래스
    """

    @abstractmethod
    def fetch(self) -> Any:
        pass


class FileSourceProcessor(SourceProcessor):
    def __init__(self, path: str):
        self.path = path

    def fetch(self) -> Any:
        # 실제 파일 읽기 로직은 생략 (예시)
        with open(self.path, "r") as f:
            return f.read()


class SourceNode(BaseNode):
    """
    SourceProcessor를 파이프라인에 노드처럼 추가할 수 있는 클래스 (업스트림 없음)
    """

    def __init__(
        self,
        name: str,
        source: SourceProcessor,
        stream_settings: NodeStreamSettings = None,
        tags=None,
    ):
        self.name = name
        self.fn = lambda: source.fetch()
        self.upstreams = []
        self.tags = tags or []
        self.key_params = []
        self.stream_settings = stream_settings
        self.kwargs = {}
        self.node_id = name
        self.results_cache = {}
        self.source = source

    def execute(self, inputs=None, interval="1d"):
        return self.fn()

    def to_definition(self) -> dict:
        return {
            "name": self.name,
            "node_id": self.node_id,
            "tags": self.tags,
            "upstreams": self.upstreams,
            "key_params": self.key_params,
            "stream_settings": self.stream_settings.model_dump() if self.stream_settings else {},
        }


__all__ = [
    "ProcessingNode",
    "QueryNode",
    "SourceProcessor",
    "SourceNode",
]
