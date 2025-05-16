"""
병렬 실행 엔진
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from qmtl.sdk import topic
from qmtl.sdk.models import IntervalEnum

from .state_manager import StateManager
from .stream_processor import StreamProcessor


class ParallelExecutionEngine:
    def __init__(
        self,
        brokers: str = "localhost:9092",
        redis_uri: str = "redis://localhost:6379/0",
        max_workers: int = 10,
    ):
        self.brokers = brokers
        self.redis_uri = redis_uri
        self.max_workers = max_workers
        self.stream = StreamProcessor(brokers=brokers)
        self.state = StateManager(redis_uri=redis_uri)
        self.node_topics = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = False
        self.tasks = []

    def register_node(self, node_name: str, pipeline_name: str = None):
        # 파이프라인 이름을 명명 규칙에 반영
        pipeline_name = pipeline_name or "default"
        input_topic = topic.get_input_topic(pipeline_name, node_name)
        output_topic = topic.get_output_topic(pipeline_name, node_name)
        self.node_topics[node_name] = (input_topic, output_topic)
        # 토픽 자동 생성 (실패시 로깅)
        for t in [input_topic, output_topic]:
            try:
                topic.create_topic(self.brokers, t)
            except Exception as e:
                logging.warning(f"토픽 자동 생성 실패: {t} ({e})")
        return input_topic, output_topic

    def prepare_pipeline(self, pipeline):
        if not pipeline.execution_order:
            pipeline.execution_order = pipeline._topological_sort()
        for node_name in pipeline.nodes:
            self.register_node(node_name, pipeline_name=getattr(pipeline, "name", "default"))

    async def _execute_node_async(self, node, pipeline):
        node_name = node.name
        input_topic, output_topic = self.node_topics[node_name]
        stream = StreamProcessor(
            brokers=self.brokers, group_id=f"qmtl-{node_name}", client_id=f"qmtl-{node_name}"
        )
        upstream_topics = []
        for upstream in node.upstreams:
            _, upstream_output = self.node_topics[upstream]
            upstream_topics.append(upstream_output)
        if upstream_topics:
            stream.subscribe(upstream_topics)
        while self.running:
            try:
                if not node.upstreams:
                    result = node.execute({})
                    stream.publish(output_topic, result)
                    if hasattr(node, "interval_settings") and node.interval_settings:
                        for interval, settings in node.interval_settings.items():
                            ttl = None
                            max_history = 100
                            if isinstance(settings, dict) and "period" in settings:
                                period = settings.get("period")
                                if period and isinstance(period, str):
                                    unit = period[-1]
                                    try:
                                        value = int(period[:-1])
                                        if unit == "d":
                                            ttl = value * 24 * 60 * 60
                                        elif unit == "h":
                                            ttl = value * 60 * 60
                                        elif unit == "m":
                                            ttl = value * 60
                                    except (ValueError, IndexError):
                                        pass
                            if isinstance(settings, dict) and "max_history" in settings:
                                max_history = settings.get("max_history", 100)
                            self.state.save_history(
                                node.node_id, interval, result, max_items=max_history, ttl=ttl
                            )
                    elif hasattr(node, "stream_settings") and hasattr(
                        node.stream_settings, "intervals"
                    ):
                        for interval, interval_obj in node.stream_settings.intervals.items():
                            ttl = None
                            max_history = 100
                            if hasattr(interval_obj, "period") and interval_obj.period:
                                period = interval_obj.period
                                if isinstance(period, str):
                                    unit = period[-1]
                                    try:
                                        value = int(period[:-1])
                                        if unit == "d":
                                            ttl = value * 24 * 60 * 60
                                        elif unit == "h":
                                            ttl = value * 60 * 60
                                        elif unit == "m":
                                            ttl = value * 60
                                    except (ValueError, IndexError):
                                        pass
                            if hasattr(interval_obj, "max_history"):
                                max_history = interval_obj.max_history or 100
                            self.state.save_history(
                                node.node_id, interval, result, max_items=max_history, ttl=ttl
                            )
                    await asyncio.sleep(1)
                else:
                    message = stream.consume(timeout=0.1)
                    if message:
                        inputs = {}
                        upstream_topic = message["topic"]
                        for upstream in node.upstreams:
                            _, upstream_output = self.node_topics[upstream]
                            if upstream_output == upstream_topic:
                                inputs[upstream] = message["value"]
                                break
                        if len(inputs) == len(node.upstreams):
                            result = node.execute(inputs)
                            stream.publish(output_topic, result)
                            if hasattr(node, "interval_settings") and node.interval_settings:
                                for interval, settings in node.interval_settings.items():
                                    ttl = None
                                    max_history = 100
                                    if isinstance(settings, dict) and "period" in settings:
                                        period = settings.get("period")
                                        if period and isinstance(period, str):
                                            unit = period[-1]
                                            try:
                                                value = int(period[:-1])
                                                if unit == "d":
                                                    ttl = value * 24 * 60 * 60
                                                elif unit == "h":
                                                    ttl = value * 60 * 60
                                                elif unit == "m":
                                                    ttl = value * 60
                                            except (ValueError, IndexError):
                                                pass
                                    if isinstance(settings, dict) and "max_history" in settings:
                                        max_history = settings.get("max_history", 100)
                                    self.state.save_history(
                                        node.node_id,
                                        interval,
                                        result,
                                        max_items=max_history,
                                        ttl=ttl,
                                    )
                            elif hasattr(node, "stream_settings") and hasattr(
                                node.stream_settings, "intervals"
                            ):
                                for (
                                    interval,
                                    interval_obj,
                                ) in node.stream_settings.intervals.items():
                                    ttl = None
                                    max_history = 100
                                    if hasattr(interval_obj, "period") and interval_obj.period:
                                        period = interval_obj.period
                                        if isinstance(period, str):
                                            unit = period[-1]
                                            try:
                                                value = int(period[:-1])
                                                if unit == "d":
                                                    ttl = value * 24 * 60 * 60
                                                elif unit == "h":
                                                    ttl = value * 60 * 60
                                                elif unit == "m":
                                                    ttl = value * 60
                                            except (ValueError, IndexError):
                                                pass
                                    if hasattr(interval_obj, "max_history"):
                                        max_history = interval_obj.max_history or 100
                                    self.state.save_history(
                                        node.node_id,
                                        interval,
                                        result,
                                        max_items=max_history,
                                        ttl=ttl,
                                    )
                    else:
                        await asyncio.sleep(0.01)
            except Exception as e:
                logging.error(f"노드 '{node_name}' 실행 중 오류 발생: {e}")
                await asyncio.sleep(1)

    def execute_pipeline(self, pipeline, timeout: Optional[float] = None):
        self.prepare_pipeline(pipeline)

        async def run_pipeline():
            self.running = True
            tasks = []
            for node_name in pipeline.nodes:
                node = pipeline.nodes[node_name]
                task = asyncio.create_task(self._execute_node_async(node, pipeline))
                tasks.append(task)
            if timeout:
                try:
                    await asyncio.wait_for(asyncio.gather(*tasks), timeout=timeout)
                except asyncio.TimeoutError:
                    pass
                finally:
                    self.running = False
            else:
                try:
                    await asyncio.gather(*tasks)
                except KeyboardInterrupt:
                    pass
                finally:
                    self.running = False
            results = {}
            for node_name in pipeline.nodes:
                node = pipeline.nodes[node_name]
                if node.interval_settings:
                    interval = next(iter(node.interval_settings.keys()), "1d")
                    history = self.state.get_history(node.node_id, interval, count=1)
                    if history:
                        results[node_name] = history[0]["value"]
            return results

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(run_pipeline())

    def stop(self):
        self.running = False
