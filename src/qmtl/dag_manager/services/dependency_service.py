"""Placeholder Dependency service for DAG Manager."""

from typing import List


class DependencyService:
    """Service for node dependency operations."""

    def get_dependencies(self, node_id: str) -> List[str]:
        """Return upstream dependency node IDs for a node."""
        raise NotImplementedError
