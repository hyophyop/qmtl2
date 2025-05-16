"""
QMTL SDK: Container build utility
- Dockerfile 템플릿 자동 생성
- 의존성 파일 추출
- 이미지 빌드/푸시 유틸리티 (초안)
"""

from pathlib import Path

DOCKERFILE_TEMPLATE = """
FROM python:3.9-slim
WORKDIR /app
COPY . /app
{dependency_install}
CMD ["python", "main.py"]
"""


def generate_dockerfile_template(dependency_file: str = "requirements.txt") -> str:
    """
    Dockerfile 템플릿 문자열 생성 (의존성 설치 명령 포함)
    """
    if dependency_file.endswith(".txt"):
        dep_cmd = f"RUN pip install --no-cache-dir -r {dependency_file}"
    elif dependency_file.endswith(".toml"):
        dep_cmd = f"RUN pip install --no-cache-dir uv && uv pip install -r requirements.txt"
    else:
        dep_cmd = ""
    return DOCKERFILE_TEMPLATE.format(dependency_install=dep_cmd)


def write_dockerfile(target_dir: str = ".", dependency_file: str = "requirements.txt") -> str:
    """
    Dockerfile을 target_dir에 생성
    """
    dockerfile_content = generate_dockerfile_template(dependency_file)
    dockerfile_path = Path(target_dir) / "Dockerfile"
    with open(dockerfile_path, "w") as f:
        f.write(dockerfile_content)
    return str(dockerfile_path)


def extract_dependencies(project_dir: str = ".") -> str:
    """
    pyproject.toml 또는 requirements.txt 등 의존성 파일 경로 반환
    """
    for fname in ["requirements.txt", "pyproject.toml"]:
        fpath = Path(project_dir) / fname
        if fpath.exists():
            return str(fpath)
    raise FileNotFoundError("No dependency file found (requirements.txt or pyproject.toml)")


def build_docker_image(context_dir: str = ".", tag: str = "qmtl-strategy:latest") -> None:
    """
    Docker 이미지를 빌드한다.
    """
    import subprocess

    cmd = ["docker", "build", "-t", tag, context_dir]
    subprocess.run(cmd, check=True)


def push_docker_image(tag: str, registry: str = None) -> None:
    """
    Docker 이미지를 레지스트리에 푸시한다.
    """
    import subprocess

    image = tag
    if registry:
        image = f"{registry}/{tag}"
        subprocess.run(["docker", "tag", tag, image], check=True)
    subprocess.run(["docker", "push", image], check=True)
