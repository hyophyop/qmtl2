#!/bin/bash
# 테스트 환경 자동 설정 스크립트
# - Docker 컨테이너(Neo4j, Redis, Redpanda) 및 의존성 설치
# - 로컬/CI 환경 모두 지원

set -e

# 1. 의존성 설치 (uv)
if ! command -v uv &> /dev/null; then
  echo "[INFO] uv not found, installing..."
  pip install uv
fi

# 2. 가상환경 및 패키지 설치

# dev/test 환경을 위해 dev extras까지 설치
if [ ! -d ".venv" ]; then
  uv venv .venv
fi
uv pip install -e .[dev]

# 3. Docker 컨테이너 실행
docker-compose -f docker-compose.dev.yml up -d

echo "[INFO] 테스트 환경 준비 완료. (Neo4j/Redis/Redpanda 컨테이너 및 의존성 설치)"
