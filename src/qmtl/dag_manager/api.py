from fastapi import FastAPI, Response
from qmtl.protobuf.qmtl import nodes_pb2

app = FastAPI(title="QMTL DAG Manager")

@app.get("/v1/dag-manager/nodes/{node_id}")
def get_node(node_id: str):
    node = nodes_pb2.DataNode(
        node_id=node_id,
        type=nodes_pb2.NodeType.FEATURE,
        data_format={"type": "csv"},
        dependencies=[],
    )
    return Response(content=node.SerializeToString(), media_type="application/x-protobuf")
