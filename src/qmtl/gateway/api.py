from fastapi import FastAPI, Response
from qmtl.protobuf.qmtl import work_pb2

app = FastAPI(title="QMTL Gateway")

@app.get("/v1/gateway/work/{work_id}")
def get_work(work_id: str):
    work = work_pb2.WorkItem(
        id=work_id,
        type=work_pb2.WorkType.STRATEGY_EXECUTION,
        status=work_pb2.WorkStatus.PENDING,
    )
    return Response(content=work.SerializeToString(), media_type="application/x-protobuf")
