import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from qmtl.common.db.connection_pool import Neo4jConnectionPool
from qmtl.common.errors.exceptions import DatabaseError


class GCService(ABC):
    @abstractmethod
    def run_gc(self) -> Any:
        pass

    @abstractmethod
    def get_status(self) -> dict:
        pass


class Neo4jGCService(GCService):
    def __init__(self, database: str = None, interval_sec: int = 600):
        self.pool = Neo4jConnectionPool()
        self.database = database
        self.interval_sec = interval_sec
        self._last_status = {}
        self._daemon_thread = None
        self._stop_event = threading.Event()

    def collect_ttl_expired(self) -> int:
        now = int(time.time())
        cypher = """
        MATCH (n:DataNode)
        WHERE n.ttl IS NOT NULL AND n.ttl > 0 AND n.created_at IS NOT NULL AND (n.created_at + n.ttl) < $now
        WITH n
        DETACH DELETE n
        RETURN count(n) AS deleted_count
        """
        with self.pool.client() as client:
            try:
                result = client.execute_query(cypher, {"now": now}, self.database)
                return result[0]["deleted_count"] if result else 0
            except DatabaseError:
                return 0

    def collect_zero_deps(self) -> int:
        cypher = """
        MATCH (n:DataNode)
        WHERE NOT (n)<-[:DEPENDS_ON]-(:DataNode)
        WITH n
        DETACH DELETE n
        RETURN count(n) AS deleted_count
        """
        with self.pool.client() as client:
            try:
                result = client.execute_query(cypher, {}, self.database)
                return result[0]["deleted_count"] if result else 0
            except DatabaseError:
                return 0

    def run_gc(self) -> dict:
        ttl_deleted = self.collect_ttl_expired()
        zero_dep_deleted = self.collect_zero_deps()
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "ttl_deleted": ttl_deleted,
            "zero_dep_deleted": zero_dep_deleted,
        }
        self._last_status = status
        return status

    def get_status(self) -> dict:
        return self._last_status

    def start_daemon(self):
        if self._daemon_thread and self._daemon_thread.is_alive():
            return
        self._stop_event.clear()

        def loop():
            while not self._stop_event.is_set():
                self.run_gc()
                self._stop_event.wait(self.interval_sec)

        self._daemon_thread = threading.Thread(target=loop, daemon=True)
        self._daemon_thread.start()

    def stop_daemon(self):
        self._stop_event.set()
        if self._daemon_thread:
            self._daemon_thread.join()
