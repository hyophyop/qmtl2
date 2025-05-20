from datetime import datetime
from typing import Any, Dict, Optional

from .service import GCService


class InMemoryGCService(GCService):
    """Simple in-memory GC service implementation for testing."""

    def __init__(self):
        self._last_status: Dict[str, Any] = {}

    def run_gc(self) -> Dict[str, Any]:
        """Run garbage collection and return results."""
        # Simplified GC implementation for tests
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "ttl_deleted": 0,
            "zero_dep_deleted": 0,
        }
        self._last_status = status
        return status

    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get the status of the last GC run."""
        return self._last_status
