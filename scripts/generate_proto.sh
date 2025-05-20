#!/bin/bash
# QMTL: 모든 protos/*.proto → Python 코드 자동 생성 스크립트
# 사용법: bash scripts/generate_proto.sh

set -e
PROTO_DIR="$(dirname "$0")/../protos"
OUT_DIR="$(dirname "$0")/../src/qmtl/models/generated"
mkdir -p "$OUT_DIR"

for proto in "$PROTO_DIR"/*.proto; do
  python -m grpc_tools.protoc \
    -I"$PROTO_DIR" \
    --python_out="$OUT_DIR" \
    --grpc_python_out="$OUT_DIR" \
    "$proto"
done

# 기존 src/에 잘못 생성된 *_pb2.py 파일 자동 삭제
find "$(dirname "$0")/../src" -maxdepth 1 -name '*_pb2.py' -exec rm -f {} +

echo "[OK] All .proto files compiled to $OUT_DIR"
