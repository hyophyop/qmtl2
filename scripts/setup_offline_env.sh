#!/bin/bash
# QMTL2 개발용 Docker 구환경 세팅 스크립트 (외부 네트워크 차단 환경)
# - uv는 사전 설치되어 있다고 가정
# - 필요한 wheel/tar.gz 패키지는 미리 준비되어 있어야 함 (예: /wheels 디렉토리)
# - pyproject.toml 기반으로 Python 3.12 venv 생성 및 패키지 설치

set -e

# 1. Python 3.12 venv 생성 (이미 있으면 skip)
if [ ! -d "3.12" ]; then
  uv venv 3.12
fi

# 2. venv 활성화
source 3.12/bin/activate

# 3. wheel/tar.gz 패키지 캐시 경로 지정 (예: /wheels)
WHEEL_DIR="/wheels"

# 4. uv pip install --find-links 옵션으로 오프라인 설치
uv pip install --find-links "$WHEEL_DIR" .

# 5. 개발 편의를 위한 안내
cat <<EOF
[QMTL2 개발 환경 세팅 완료]
- Python 3.12 venv: 3.12/
- 패키지 캐시 경로: $WHEEL_DIR
- venv 활성화: source 3.12/bin/activate
- 테스트: pytest
EOF
