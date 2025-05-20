import os

from qmtl.sdk import container


def test_generate_dockerfile_template_txt():
    dockerfile = container.generate_dockerfile_template("requirements.txt")
    assert "pip install --no-cache-dir -r requirements.txt" in dockerfile


def test_generate_dockerfile_template_toml():
    dockerfile = container.generate_dockerfile_template("pyproject.toml")
    assert "uv pip install -r requirements.txt" in dockerfile


def test_write_dockerfile(tmp_path):
    path = container.write_dockerfile(str(tmp_path), "requirements.txt")
    assert os.path.exists(path)
    with open(path) as f:
        content = f.read()
    assert "FROM python:3.11-slim" in content


def test_extract_dependencies(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("pytest\n")
    assert container.extract_dependencies(str(tmp_path)).endswith("requirements.txt")
    req.unlink()
    pyproj = tmp_path / "pyproject.toml"
    pyproj.write_text("[build-system]\n")
    assert container.extract_dependencies(str(tmp_path)).endswith("pyproject.toml")


def test_build_and_push_docker_image(monkeypatch):
    calls = []

    def fake_run(cmd, check):
        calls.append(cmd)
        return 0

    monkeypatch.setattr("subprocess.run", fake_run)
    container.build_docker_image(".", "test:latest")
    container.push_docker_image("test:latest", "myregistry")
    assert any("docker" in c for c in calls[0])
    assert any("push" in c for c in calls[-1])
