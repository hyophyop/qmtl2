from qmtl.common.config.env import get_env_vars


def test_get_env_vars_all(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    monkeypatch.setenv("BAR", "baz")
    env = get_env_vars()
    assert env["FOO"] == "bar"
    assert env["BAR"] == "baz"


def test_get_env_vars_prefix(monkeypatch):
    monkeypatch.setenv("QMTL_FOO", "1")
    monkeypatch.setenv("QMTL_BAR", "2")
    monkeypatch.setenv("OTHER", "3")
    env = get_env_vars(prefix="QMTL_")
    assert env == {"QMTL_FOO": "1", "QMTL_BAR": "2"}
