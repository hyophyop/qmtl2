"""
Unit tests for src/qmtl/sdk/models.py
커버리지 80% 달성을 위한 smoke/엣지케이스 테스트 템플릿
"""
from collections import defaultdict
from unittest.mock import patch, MagicMock
import pytest
import src.qmtl.sdk.models as models

def test_interval_enum():
    assert models.IntervalEnum.MINUTE == "1m"
    assert models.IntervalEnum.HOUR.value == "1h"

@patch("src.qmtl.sdk.models.qmtl_common_pb2")
def test_create_interval_settings(mock_pb2):
    mock_pb2.IntervalEnum.MINUTE = 1
    mock_pb2.IntervalSettings = MagicMock(return_value=MagicMock())
    result = models.create_interval_settings(models.IntervalEnum.MINUTE, 7, max_history=3)
    assert result is not None

@patch("src.qmtl.sdk.models.qmtl_datanode_pb2")
@patch("src.qmtl.sdk.models.create_interval_settings")
def test_create_node_stream_settings(mock_create_interval_settings, mock_pb2):
    # defaultdict로 KeyError 방지
    mock_intervals = defaultdict(MagicMock)
    mock_pb2.NodeStreamSettings.return_value = MagicMock(intervals=mock_intervals)
    mock_create_interval_settings.return_value = MagicMock()
    intervals = {models.IntervalEnum.MINUTE: MagicMock(interval="1m", period=1)}
    result = models.create_node_stream_settings(intervals)
    assert result is not None

@patch("src.qmtl.sdk.models.qmtl_pipeline_pb2")
def test_create_node_definition(mock_pb2):
    # key_params 등 속성 추가
    mock_node_def = MagicMock(tags=[], params={}, upstreams=[], key_params=[], stream_settings={})
    mock_pb2.NodeDefinition.return_value = mock_node_def
    result = models.create_node_definition("n", tags=["t"], params={"a":1}, upstreams=["u"], key_params=["k"], stream_settings={})
    assert result is not None

@patch("src.qmtl.sdk.models.qmtl_pipeline_pb2")
def test_create_query_node_definition(mock_pb2):
    mock_query_node_def = MagicMock(query_tags=[], tags=[], params={}, upstreams=[], key_params=[], stream_settings={})
    mock_pb2.QueryNodeDefinition.return_value = mock_query_node_def
    result = models.create_query_node_definition("n", ["q"], tags=["t"], params={"a":1}, upstreams=["u"], key_params=["k"], stream_settings={}, interval="1d", period=7)
    assert result is not None

# --- 주요 래퍼 클래스 생성/메서드/round-trip ---
@patch("src.qmtl.sdk.models.create_interval_settings")
def test_intervalsettings(mock_create):
    mock_create.return_value = MagicMock()
    s = models.IntervalSettings("1d", 7, 100)
    assert s.interval == "1d"
    assert s.period == 7
    assert s.to_proto() is not None

@patch("src.qmtl.sdk.models.create_node_stream_settings")
def test_nodestreamsettings(mock_create):
    mock_create.return_value = MagicMock()
    s = models.NodeStreamSettings({"1d": MagicMock(interval="1d", period=1)})
    assert s.to_proto() is not None
    d = s.to_dict()
    assert "1d" in d

@patch("src.qmtl.sdk.models.create_node_definition")
def test_nodedefinition(mock_create):
    mock_create.return_value = MagicMock()
    n = models.NodeDefinition("n", tags=["t"], params={"a":1}, upstreams=["u"], key_params=["k"], stream_settings={})
    assert n.to_proto() is not None
    # from_definition
    n2 = models.NodeDefinition.from_definition({"name":"n","tags":["t"],"params":{"a":1},"upstreams":["u"],"key_params":["k"],"stream_settings":{}})
    assert n2.name == "n"

@patch("src.qmtl.sdk.models.create_query_node_definition")
@patch("src.qmtl.sdk.models.create_node_definition")
def test_querynodedefinition(mock_create_node, mock_create_query):
    mock_create_node.return_value = MagicMock()
    mock_create_query.return_value = MagicMock()
    q = models.QueryNodeDefinition("n", ["q"], tags=["t"], params={"a":1}, upstreams=["u"], key_params=["k"], stream_settings={}, interval="1d", period=7)
    assert q.to_proto() is not None
    # from_definition (period str)
    q2 = models.QueryNodeDefinition.from_definition({"name":"n","query_tags":["q"],"tags":["t"],"params":{"a":1},"upstreams":["u"],"key_params":["k"],"stream_settings":{},"interval":"1d","period":"7"})
    assert q2.name == "n"

@patch("src.qmtl.sdk.models.create_pipeline_definition")
def test_pipelinedefinition(mock_create):
    mock_proto = MagicMock(nodes=[1,2], query_nodes=[3], metadata={"a":1})
    mock_create.return_value = mock_proto
    p = models.PipelineDefinition("p", nodes=[1,2], query_nodes=[3], metadata={"a":1})
    assert p.nodes == [1,2]
    assert p.query_nodes == [3]
    assert p.metadata["a"] == 1
    # from_definition
    p2 = models.PipelineDefinition.from_definition({"name":"p","nodes":[1,2],"query_nodes":[3],"metadata":{"a":1}})
    assert p2.name == "p"

@patch("src.qmtl.sdk.models.create_analyzer_definition")
def test_analyzerdefinition(mock_create):
    mock_proto = MagicMock(analyzer_type="custom")
    mock_create.return_value = mock_proto
    a = models.AnalyzerDefinition("a", analyzer_type="custom")
    assert a.analyzer_type == "custom"
    a.analyzer_type = "other"
    # from_definition
    a2 = models.AnalyzerDefinition.from_definition({"name":"a","analyzer_type":"custom"})
    assert a2.name == "a"

@patch("src.qmtl.sdk.models.create_query_node_result_selector")
def test_querynoderesultselector(mock_create):
    mock_create.return_value = MagicMock()
    s = models.QueryNodeResultSelector(mode="list", batch_size=10, sample_size=5, filter_meta={"x":1})
    assert s.to_proto() is not None

# TODO: 각 모델별 생성/유효성검사/엣지케이스 테스트 추가
