"""Facade service wrapping individual DAG Manager services."""

from typing import List

from .node_service import NodeService
from .stream_service import StreamService
from .dependency_service import DependencyService


class MetadataService:
    """Facade entry point for DAG Manager domain operations."""

    def __init__(
        self,
        node_service: NodeService,
        stream_service: StreamService,
        dependency_service: DependencyService,
    ):
        self.node_service = node_service
        self.stream_service = stream_service
        self.dependency_service = dependency_service

    def list_nodes(self) -> List[dict]:
        return self.node_service.list_nodes()

    def get_node_dependencies(self, node_id: str) -> List[str]:
        return self.dependency_service.get_dependencies(node_id)

    def list_nodes_by_tags(self, tags: List[str]) -> List[dict]:
        return self.node_service.list_by_tags(tags)

    def list_streams(self) -> List[dict]:
        return self.stream_service.list_streams()

    def list_callbacks(self, node_id: str) -> List[dict]:
        return self.node_service.list_callbacks(node_id)
