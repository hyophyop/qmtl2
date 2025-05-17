import pytest

from qmtl.gateway.services.work_queue_service import WorkQueueService

pytestmark = pytest.mark.usefixtures("docker_compose_up_down")


def test_work_queue_push_pop(redis_session, redis_clean):
    service = WorkQueueService(redis_client=redis_session)
    service.clear()
    service.push({"id": "w1", "task": "demo"})
    assert service.size() == 1
    item = service.pop()
    assert item == {"id": "w1", "task": "demo"}
    assert service.size() == 0
