from qmtl.protobuf.qmtl import nodes_pb2

def test_protobuf_round_trip():
    node = nodes_pb2.DataNode(node_id="a" * 32, data_format={"type": "csv"})
    raw = node.SerializeToString()
    node2 = nodes_pb2.DataNode.FromString(raw)
    assert node == node2
