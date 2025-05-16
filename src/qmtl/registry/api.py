# ------------------ QMTL Registry API ------------------

# Imports (no duplicates, all at top)
import logging
from typing import Dict, List, Optional, Any
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, status, Body
from fastapi.middleware.cors import CORSMiddleware
from qmtl.common.config.settings import get_settings
from qmtl.common.db.connection_pool import get_neo4j_pool
from qmtl.common.errors.handlers import add_exception_handlers
from qmtl.common.errors.exceptions import (
    RegistryServiceError,
    ValidationError,
)
from qmtl.models.datanode import DataNode
from qmtl.models.template import NodeTemplate, StrategyTemplate, DAGTemplate, TemplatePermission
from qmtl.models.strategy import StrategyMetadata, StrategySnapshot
from qmtl.models.status import NodeStatus
from qmtl.models.event import NodeStatusEvent, PipelineStatusEvent, AlertEvent
from qmtl.registry.services.node.management import Neo4jNodeManagementService, NodeManagementService
from qmtl.registry.services.strategy.management import (
    Neo4jStrategyManagementService,
    StrategyManagementService,
)
from qmtl.registry.services.strategy import StrategySnapshotService
from qmtl.registry.services.event import EventPublisher
from qmtl.registry.services.metadata_service import MetadataService

# FastAPI app declaration (only once, right after imports)
app = FastAPI(
    title="QMTL Registry API",
    description="노드, 전략, 관계를 관리하는 Registry API",
    version="0.1.0",
)

# CORS middleware and exception handlers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_exception_handlers(app)

# Logger
logger = logging.getLogger(__name__)

# Dependency injection functions
def get_node_service() -> NodeManagementService:
    pool = get_neo4j_pool()
    settings = get_settings()
    return Neo4jNodeManagementService(pool.get_client(), settings.env.neo4j_database)

def get_strategy_service() -> StrategyManagementService:
    pool = get_neo4j_pool()
    settings = get_settings()
    return Neo4jStrategyManagementService(pool.get_client(), settings.env.neo4j_database)

def get_snapshot_service() -> StrategySnapshotService:
    pool = get_neo4j_pool()
    settings = get_settings()
    return StrategySnapshotService(pool.get_client(), settings.env.neo4j_database)

def get_metadata_service() -> MetadataService:
    pool = get_neo4j_pool()
    settings = get_settings()
    node_service = Neo4jNodeManagementService(pool.get_client(), settings.env.neo4j_database)
    strategy_service = Neo4jStrategyManagementService(pool.get_client(), settings.env.neo4j_database)
    snapshot_service = StrategySnapshotService(pool.get_client(), settings.env.neo4j_database)
    return MetadataService(node_service, strategy_service, snapshot_service)

# ------------------ API Endpoints ------------------

# 헬스 체크
@app.get("/")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "registry"}

# ------------------ MULTI-8: 노드/전략 Partial Update(수정) API ------------------
@app.patch("/v1/registry/nodes/{node_id}")
async def update_node_partial(
    node_id: str,
    update_fields: Dict[str, Any] = Body(..., description="수정할 필드와 값의 딕셔너리"),
    node_service: NodeManagementService = Depends(get_node_service),
):
    """노드 Partial Update(일부 필드만 수정) API (스켈레톤)"""
    # TODO: 서비스 계층에서 검증/적용 구현
    # 예시: node_service.update_node_partial(node_id, update_fields)
    return {"node_id": node_id, "updated_fields": update_fields}

@app.patch("/v1/registry/strategies/{strategy_version_id}")
async def update_strategy_partial(
    strategy_version_id: str,
    update_fields: Dict[str, Any] = Body(..., description="수정할 필드와 값의 딕셔너리"),
    strategy_service: StrategyManagementService = Depends(get_strategy_service),
):
    """전략 Partial Update(일부 필드만 수정) API (스켈레톤)"""
    # TODO: 서비스 계층에서 검증/적용 구현
    # 예시: strategy_service.update_strategy_partial(strategy_version_id, update_fields)
    return {"strategy_version_id": strategy_version_id, "updated_fields": update_fields}
# 실시간 상태 이벤트 발행 API (MULTI-7)
@app.post("/v1/registry/events/node-status")
async def publish_node_status_event(event: NodeStatusEvent):
    try:
        EventPublisher().publish_node_status(event)
        return {"result": "ok"}
    except HTTPException:
        # 이미 HTTPException인 경우 그대로 raise
        raise
    except Exception as e:
        logger.exception("이벤트 발행 실패")
        raise HTTPException(status_code=500, detail="이벤트 발행 처리 중 내부 서버 오류가 발생했습니다")

@app.post("/v1/registry/events/pipeline-status")
async def publish_pipeline_status_event(event: PipelineStatusEvent):
    try:
        EventPublisher().publish_pipeline_status(event)
        return {"result": "ok"}
    except HTTPException:
        # 이미 HTTPException인 경우 그대로 raise
        raise
    except Exception as e:
        logger.exception("파이프라인 이벤트 발행 실패")
        raise HTTPException(status_code=500, detail="이벤트 발행 처리 중 내부 서버 오류가 발생했습니다")

@app.post("/v1/registry/events/alert")
async def publish_alert_event(event: AlertEvent):
    try:
        EventPublisher().publish_alert(event)
        return {"result": "ok"}
    except HTTPException:
        # 이미 HTTPException인 경우 그대로 raise
        raise
    except Exception as e:
        logger.exception("알림 이벤트 발행 실패")
        raise HTTPException(status_code=500, detail="이벤트 발행 처리 중 내부 서버 오류가 발생했습니다")


# 템플릿 등록 (노드/전략/DAG)
@app.post("/v1/registry/templates/node", status_code=status.HTTP_201_CREATED)
async def create_node_template(
    template: NodeTemplate = Body(...),
):
    return {"template_id": template.template_id}

@app.post("/v1/registry/templates/strategy", status_code=status.HTTP_201_CREATED)
async def create_strategy_template(
    template: StrategyTemplate = Body(...),
):
    return {"template_id": template.template_id}

@app.post("/v1/registry/templates/dag", status_code=status.HTTP_201_CREATED)
async def create_dag_template(
    template: DAGTemplate = Body(...),
):
    return {"template_id": template.template_id}

@app.get("/v1/registry/templates/{template_id}")
async def get_template(template_id: str):
    return {"template_id": template_id, "template": None}

@app.delete("/v1/registry/templates/{template_id}")
async def delete_template(template_id: str):
    return {"success": True}

@app.get("/v1/registry/templates")
async def list_templates(template_type: str = Query(None)):
    return {"templates": []}

@app.post("/v1/registry/templates/{template_id}/permissions")
async def grant_template_permission(
    template_id: str,
    permission: TemplatePermission = Body(...),
):
    return {"success": True}

@app.get("/v1/registry/templates/{template_id}/permissions")
async def list_template_permissions(template_id: str):
    return {"permissions": []}

@app.delete("/v1/registry/templates/{template_id}/permissions/{user_id}")
async def revoke_template_permission(template_id: str, user_id: str):
    return {"success": True}
import logging
from typing import Dict, List, Optional
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from qmtl.common.config.settings import get_settings
from qmtl.common.db.connection_pool import get_neo4j_pool
from qmtl.common.errors.handlers import add_exception_handlers
from qmtl.common.errors.exceptions import (
    RegistryServiceError,
    ValidationError,
)
from qmtl.models.strategy import StrategyMetadata, StrategySnapshot
from qmtl.models.status import NodeStatus
from qmtl.registry.services.node.management import Neo4jNodeManagementService, NodeManagementService
from qmtl.registry.services.strategy.management import (
    Neo4jStrategyManagementService,
    StrategyManagementService,
)
from qmtl.registry.services.strategy import StrategySnapshotService



# MULTI-4: DAG/ready node 조회 API
@app.get("/v1/registry/pipelines/{pipeline_id}/dag")
async def get_pipeline_dag(
    pipeline_id: str,
    metadata_service: MetadataService = Depends(get_metadata_service),
):
    dag = metadata_service.get_dag(pipeline_id)
    if not dag:
        raise HTTPException(status_code=404, detail=f"파이프라인 스냅샷 없음: {pipeline_id}")
    return {"nodes": dag.nodes, "edges": dag.edges, "metadata": dag.metadata}

@app.get("/v1/registry/pipelines/{pipeline_id}/ready-nodes")
async def get_ready_nodes(
    pipeline_id: str,
    metadata_service: MetadataService = Depends(get_metadata_service),
):
    dag = metadata_service.get_dag(pipeline_id)
    if not dag:
        raise HTTPException(status_code=404, detail=f"파이프라인 스냅샷 없음: {pipeline_id}")
    # 기존 ready_nodes 로직은 MetadataService에 위임 필요(추후 확장)
    return {"nodes": dag.nodes}

# 노드 관련 API
@app.post("/v1/registry/nodes", status_code=status.HTTP_201_CREATED)
async def create_node(
    node_data: Dict[str, DataNode], node_service: NodeManagementService = Depends(get_node_service)
):
    """노드 등록 API"""
    try:
        node = node_data.get("node")
        if not node:
            # 커스텀 ValidationError 대신 FastAPI의 HTTPException을 직접 사용
            raise HTTPException(status_code=422, detail="노드 데이터가 누락되었습니다")

        node_service.validate_node(node)
        node_id = node_service.create_node(node)
        return {"node_id": node_id}
    except ValidationError as e:
        logger.error(f"노드 등록 입력값 오류: {str(e)}", exc_info=True)
        # 커스텀 ValidationError도 HTTPException으로 변환
        raise HTTPException(status_code=422, detail=str(e))
    except RegistryServiceError as e:
        logger.error(f"노드 등록 실패: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        # 이미 HTTPException인 경우 그대로 raise
        raise
    except Exception as e:
        logger.exception("노드 등록 처리 중 알 수 없는 오류")
        raise HTTPException(
            status_code=500, 
            detail="노드 등록 처리 중 내부 서버 오류가 발생했습니다"
        )

@app.get("/v1/registry/nodes/{node_id}")
async def get_node(node_id: str, node_service: NodeManagementService = Depends(get_node_service)):
    """노드 조회 API"""
    node = node_service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"노드를 찾을 수 없습니다: {node_id}")
    return {"node": node}


@app.delete("/v1/registry/nodes/{node_id}")
async def delete_node(
    node_id: str, node_service: NodeManagementService = Depends(get_node_service)
):
    """노드 삭제 API"""
    result = node_service.delete_node(node_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"노드를 찾을 수 없습니다: {node_id}")
    return {"success": True}


@app.get("/v1/registry/nodes/leaf-nodes")
async def get_leaf_nodes(metadata_service: MetadataService = Depends(get_metadata_service)):
    """의존성이 없는 노드 목록 조회 API"""
    nodes = metadata_service.node_service.list_zero_deps()
    return {"nodes": nodes}


@app.get("/v1/registry/nodes/by-tags")
async def get_nodes_by_tags(
    tags: List[str] = Query(..., description="필터링할 태그 목록"),
    interval: Optional[str] = Query(None, description="데이터 수집 인터벌 (예: 1h, 1d)"),
    period: Optional[str] = Query(None, description="데이터 보관 기간 (인터벌 단위)"),
    match_mode: str = Query("AND", description="태그 매칭 모드 (AND 또는 OR)"),
    metadata_service: MetadataService = Depends(get_metadata_service),
):
    """태그/인터벌/피리어드 기반 노드 목록 조회 API"""
    if match_mode not in ("AND", "OR"):
        raise HTTPException(status_code=422, detail="match_mode는 'AND' 또는 'OR'이어야 합니다")

    nodes = metadata_service.node_service.list_by_tags(tags, interval, period, match_mode)
    return {"nodes": nodes}


# 전략 관련 API
@app.get("/v1/registry/strategies/{version_id}")
async def get_strategy(
    version_id: str, metadata_service: MetadataService = Depends(get_metadata_service)
):
    """전략 조회 API"""
    strategy = metadata_service.get_strategy(version_id)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"전략을 찾을 수 없습니다: {version_id}")
    return {"strategy": strategy}


@app.get("/v1/registry/strategies")
async def list_strategies(metadata_service: MetadataService = Depends(get_metadata_service)):
    """전략 목록 조회 API"""
    strategies = metadata_service.strategy_service.list_strategies()
    return {"strategies": strategies}


# 노드-전략 관계 관리 API
@app.post("/v1/registry/strategies/{strategy_version_id}/nodes/{node_id}")
async def add_node_to_strategy(
    strategy_version_id: str,
    node_id: str,
    metadata_service: MetadataService = Depends(get_metadata_service),
):
    """전략에 노드 추가 API (CONTAINS 관계 생성)"""
    # 노드와 전략이 존재하는지 확인
    node = metadata_service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"노드를 찾을 수 없습니다: {node_id}")

    strategy = metadata_service.get_strategy(strategy_version_id)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"전략을 찾을 수 없습니다: {strategy_version_id}")

    # CONTAINS 관계 생성
    metadata_service.node_service.add_contains_relationship(strategy_version_id, node_id)
    return {"success": True}


@app.delete("/v1/registry/strategies/{strategy_version_id}/nodes/{node_id}")
async def remove_node_from_strategy(
    strategy_version_id: str,
    node_id: str,
    metadata_service: MetadataService = Depends(get_metadata_service),
):
    """전략에서 노드 제거 API (CONTAINS 관계 삭제)"""
    # CONTAINS 관계 삭제
    metadata_service.node_service.remove_contains_relationship(strategy_version_id, node_id)
    return {"success": True}


@app.get("/v1/registry/nodes/{node_id}/ref-count")
async def get_node_reference_count(
    node_id: str, metadata_service: MetadataService = Depends(get_metadata_service)
):
    """노드 참조 카운트 조회 API"""
    # 노드가 존재하는지 확인
    node = metadata_service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"노드를 찾을 수 없습니다: {node_id}")

    # 참조 카운트 조회
    ref_count = metadata_service.node_service.get_node_ref_count(node_id)
    return {"ref_count": ref_count}


@app.get("/v1/registry/nodes/{node_id}/ref-strategies")
async def get_node_reference_strategies(
    node_id: str, metadata_service: MetadataService = Depends(get_metadata_service)
):
    """노드를 참조하는 전략 목록 조회 API"""
    # 노드가 존재하는지 확인
    node = metadata_service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"노드를 찾을 수 없습니다: {node_id}")

    # 참조하는 전략 목록 조회
    ref_strategies = metadata_service.node_service.get_node_ref_strategies(node_id)
    return {"strategy_version_ids": ref_strategies}


@app.get("/v1/registry/strategies/{strategy_version_id}/nodes")
async def get_strategy_nodes(
    strategy_version_id: str,
    metadata_service: MetadataService = Depends(get_metadata_service),
):
    """전략에 포함된 노드 목록 조회 API"""
    # 전략이 존재하는지 확인
    strategy = metadata_service.get_strategy(strategy_version_id)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"전략을 찾을 수 없습니다: {strategy_version_id}")

    # 전략에 포함된 노드 목록 조회
    nodes = metadata_service.node_service.get_strategy_nodes(strategy_version_id)
    return {"nodes": nodes}


# 노드 상태/메타데이터 API
@app.get("/v1/registry/nodes/{node_id}/status", response_model=NodeStatus)
async def get_node_status(
    node_id: str, metadata_service: MetadataService = Depends(get_metadata_service)
):
    """
    노드 상태/메타데이터 조회 API
    - Args: node_id (노드 ID)
    - Returns: NodeStatus 모델
    - 404: 노드 상태 없음
    """
    status = metadata_service.node_service.get_node_status(node_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"노드 상태를 찾을 수 없습니다: {node_id}")
    return status


@app.post("/v1/registry/nodes/{node_id}/status", response_model=NodeStatus)
async def update_node_status(
    node_id: str,
    status: NodeStatus,
    metadata_service: MetadataService = Depends(get_metadata_service),
):
    """
    노드 상태/메타데이터 저장/갱신 API
    - Args: node_id (노드 ID), status (NodeStatus 모델)
    - Returns: 저장된 NodeStatus
    - 422: 입력값 오류
    - 500: 저장 실패
    """
    try:
        metadata_service.node_service.update_node_status(node_id, status)
        return status
    except HTTPException:
        # 이미 HTTPException인 경우 그대로 raise
        raise
    except Exception as e:
        logger.exception(f"노드 상태 저장 실패")
        raise HTTPException(status_code=500, detail="노드 상태 저장 중 내부 서버 오류가 발생했습니다")


@app.post("/v1/registry/strategies/{version_id}/snapshots", status_code=status.HTTP_201_CREATED)
async def create_strategy_snapshot(
    version_id: str,
    snapshot: StrategySnapshot,
    metadata_service: MetadataService = Depends(get_metadata_service),
):
    """전략 스냅샷 저장 API"""
    try:
        snapshot_id = metadata_service.snapshot_service.create_snapshot(snapshot)
        return {"snapshot_id": snapshot_id}
    except HTTPException:
        # 이미 HTTPException인 경우 그대로 raise
        raise
    except Exception as e:
        logger.exception("스냅샷 저장 실패")
        raise HTTPException(status_code=500, detail="스냅샷 저장 중 내부 서버 오류가 발생했습니다")


@app.get("/v1/registry/strategies/{version_id}/snapshots")
async def list_strategy_snapshots(
    version_id: str,
    metadata_service: MetadataService = Depends(get_metadata_service),
):
    """전략 스냅샷 목록 조회 API"""
    try:
        snapshots = metadata_service.snapshot_service.get_snapshots(version_id)
        return {"snapshots": snapshots}
    except HTTPException:
        # 이미 HTTPException인 경우 그대로 raise
        raise
    except Exception as e:
        logger.exception("스냅샷 조회 실패")
        raise HTTPException(status_code=500, detail="스냅샷 조회 중 내부 서버 오류가 발생했습니다")


@app.post("/v1/registry/strategies/{version_id}/rollback")
async def rollback_strategy_to_snapshot(
    version_id: str,
    snapshot_id: str,
    metadata_service: MetadataService = Depends(get_metadata_service),
):
    """특정 스냅샷으로 전략 롤백 API"""
    try:
        snapshot = metadata_service.snapshot_service.rollback_to_snapshot(version_id, snapshot_id)
        if not snapshot:
            raise HTTPException(status_code=404, detail="스냅샷을 찾을 수 없습니다")
        return {"snapshot": snapshot}
    except HTTPException:
        # 이미 HTTPException인 경우 그대로 raise
        raise
    except Exception as e:
        logger.exception("롤백 실패")
        raise HTTPException(status_code=500, detail="롤백 중 내부 서버 오류가 발생했습니다")


# 콜백 API 라우터 추가 (always at the end)
from qmtl.registry import api_callback
app.include_router(api_callback.router)

if __name__ == "__main__":
    uvicorn.run("qmtl.registry.api:app", host="0.0.0.0", port=8000, reload=True)

@app.get("/v1/registry/nodes/{node_id}/dependencies")
async def get_node_dependencies(
    node_id: str, metadata_service: MetadataService = Depends(get_metadata_service)
):
    """노드가 의존하는 노드 ID 목록 조회 API"""
    node = metadata_service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"노드를 찾을 수 없습니다: {node_id}")
    deps = metadata_service.node_service.get_node_dependencies(node_id)
    return {"dependencies": deps}

@app.post("/v1/registry/nodes/{node_id}/dependencies/{dependency_id}")
async def add_node_dependency(
    node_id: str, dependency_id: str, metadata_service: MetadataService = Depends(get_metadata_service)
):
    """노드 간 의존성(DEPENDS_ON) 추가 API"""
    try:
        node = metadata_service.get_node(node_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"노드를 찾을 수 없습니다: {node_id}")
            
        dep = metadata_service.get_node(dependency_id)
        if not dep:
            raise HTTPException(status_code=404, detail=f"의존성 노드를 찾을 수 없습니다: {dependency_id}")
            
        metadata_service.node_service.add_dependency(node_id, dependency_id)
        return {"success": True}
    except HTTPException:
        # 이미 HTTPException인 경우 그대로 raise
        raise
    except Exception as e:
        logger.exception("노드 의존성 추가 중 오류")
        raise HTTPException(status_code=500, detail="노드 의존성 추가 중 내부 서버 오류가 발생했습니다")

@app.delete("/v1/registry/nodes/{node_id}/dependencies/{dependency_id}")
async def remove_node_dependency(
    node_id: str, dependency_id: str, metadata_service: MetadataService = Depends(get_metadata_service)
):
    """노드 간 의존성(DEPENDS_ON) 삭제 API"""
    try:
        node = metadata_service.get_node(node_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"노드를 찾을 수 없습니다: {node_id}")
            
        dep = metadata_service.get_node(dependency_id)
        if not dep:
            raise HTTPException(status_code=404, detail=f"의존성 노드를 찾을 수 없습니다: {dependency_id}")
            
        metadata_service.node_service.remove_dependency(node_id, dependency_id)
        return {"success": True}
    except HTTPException:
        # 이미 HTTPException인 경우 그대로 raise
        raise
    except Exception as e:
        logger.exception("노드 의존성 삭제 중 오류")
        raise HTTPException(status_code=500, detail="노드 의존성 삭제 중 내부 서버 오류가 발생했습니다")
