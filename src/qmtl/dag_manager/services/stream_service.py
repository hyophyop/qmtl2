"""Placeholder Stream service for DAG Manager."""

from typing import List


class StreamService:
    """Service for stream topic operations."""

    def list_streams(self) -> List[dict]:
        """Return list of streams."""
        raise NotImplementedError
