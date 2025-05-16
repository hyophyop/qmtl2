from src.qmtl.sdk.execution.parallel_engine import ParallelExecutionEngine


def test_parallel_engine_init(redpanda_session, redis_session):
    """
    [FIXTURE-3] redpanda_session/redis_session fixture를 사용하여 docker-compose 기반 브로커/Redis 주소로 테스트
    """
    engine = ParallelExecutionEngine(
        brokers=redpanda_session,
        redis_uri=f"redis://{redis_session.connection_pool.connection_kwargs['host']}:{redis_session.connection_pool.connection_kwargs['port']}/{redis_session.connection_pool.connection_kwargs['db']}",
    )
    assert engine.brokers == redpanda_session
    assert engine.redis_uri.startswith("redis://")
    assert engine.max_workers == 10


def test_prepare_pipeline_topic_creation(monkeypatch):
    # 더미 파이프라인/노드 구조
    class DummyNode:
        def __init__(self, name):
            self.name = name
            self.upstreams = []

    class DummyPipeline:
        def __init__(self, name, node_names):
            self.name = name
            self.nodes = {n: DummyNode(n) for n in node_names}
            self.execution_order = []

        def _topological_sort(self):
            return list(self.nodes.keys())

    called = []

    def fake_create_topic(brokers, topic, **kwargs):
        called.append(topic)
        return True

    import src.qmtl.sdk.execution.parallel_engine as pe_mod
    import src.qmtl.sdk.topic as topic_mod

    monkeypatch.setattr(pe_mod.topic, "create_topic", fake_create_topic)

    engine = ParallelExecutionEngine(brokers="dummy:9092")
    pipeline = DummyPipeline("testpipe", ["A", "B"])
    engine.prepare_pipeline(pipeline)
    # 각 노드별 input/output 토픽이 모두 생성 시도됨
    expected = [
        topic_mod.get_input_topic("testpipe", "A"),
        topic_mod.get_output_topic("testpipe", "A"),
        topic_mod.get_input_topic("testpipe", "B"),
        topic_mod.get_output_topic("testpipe", "B"),
    ]
    for t in expected:
        assert t in called
