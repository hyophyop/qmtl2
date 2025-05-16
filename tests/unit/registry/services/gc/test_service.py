import time
from unittest.mock import MagicMock, patch

import pytest

from qmtl.registry.services.gc.service import Neo4jGCService


@pytest.fixture
def gc_service():
    return Neo4jGCService(database=None, interval_sec=1)


def test_collect_ttl_expired(gc_service):
    with patch.object(gc_service.pool, "client") as mock_client_ctx:
        mock_client = MagicMock()
        mock_client.execute_query.return_value = [{"deleted_count": 2}]
        mock_client_ctx.return_value.__enter__.return_value = mock_client
        count = gc_service.collect_ttl_expired()
        assert count == 2


def test_collect_zero_deps(gc_service):
    with patch.object(gc_service.pool, "client") as mock_client_ctx:
        mock_client = MagicMock()
        mock_client.execute_query.return_value = [{"deleted_count": 1}]
        mock_client_ctx.return_value.__enter__.return_value = mock_client
        count = gc_service.collect_zero_deps()
        assert count == 1


def test_run_gc_and_status(gc_service):
    with (
        patch.object(gc_service, "collect_ttl_expired", return_value=3),
        patch.object(gc_service, "collect_zero_deps", return_value=4),
    ):
        status = gc_service.run_gc()
        assert status["ttl_deleted"] == 3
        assert status["zero_dep_deleted"] == 4
        assert "timestamp" in status
        assert gc_service.get_status() == status


def test_daemon_start_stop(gc_service):
    with patch.object(gc_service, "run_gc") as mock_run_gc:
        gc_service.start_daemon()
        time.sleep(1.5)
        gc_service.stop_daemon()
        assert mock_run_gc.called
