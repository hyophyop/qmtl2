import time

import pytest

from src.qmtl.sdk.execution.state_manager import StateManager


@pytest.mark.skipif("redis" not in globals(), reason="redis 미설치 시 스킵")
def test_state_manager_set_get(tmp_path):
    sm = StateManager(redis_uri="redis://localhost:6379/0")
    key = f"test:{int(time.time())}"
    value = {"foo": "bar"}
    assert sm.set(key, value)
    assert sm.get(key) == value
    assert sm.delete(key)


# 실제 Redis 서버가 없으면 save_history/get_history 등은 생략
