"""Placeholder Node service for DAG Manager."""

from typing import List


class NodeService:
    """Service for node metadata operations."""

    def list_nodes(self) -> List[dict]:
        """Return list of nodes."""
        raise NotImplementedError

    def list_by_tags(self, tags: List[str]) -> List[dict]:
        """Return nodes filtered by tags."""
        raise NotImplementedError

    def list_callbacks(self, node_id: str) -> List[dict]:
        """Return callbacks associated with a node."""
        raise NotImplementedError
