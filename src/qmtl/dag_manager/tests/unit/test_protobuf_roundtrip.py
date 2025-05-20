# QMTL Protobuf round-trip/golden test 템플릿 (NG-2-5)
import pytest
from qmtl.models.generated import qmtl_datanode_pb2 as pb


def test_datanode_roundtrip():
    # 1. 메시지 생성
    node = pb.DataNode(node_id="abcd1234abcd1234abcd1234abcd1234", type="RAW")
    node.data_format["foo"] = "bar"
    node.dependencies.append("dep1")
    # 2. 직렬화
    data = node.SerializeToString()
    # 3. 역직렬화
    node2 = pb.DataNode()
    node2.ParseFromString(data)
    # 4. 값 비교
    assert node.node_id == node2.node_id
    assert node.type == node2.type
    assert node.data_format == node2.data_format
    assert node.dependencies == node2.dependencies


# golden test 예시: 미리 저장된 바이너리와 비교
# def test_datanode_golden():
#     with open("tests/golden/datanode.bin", "rb") as f:
#         golden = f.read()
#     node = pb.DataNode()
#     node.ParseFromString(golden)
#     assert node.node_id == "..."
