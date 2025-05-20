# QMTL Pydantic → Protobuf 마이그레이션 가이드 (NG-2-4)

## 1. 코드 치환 체크리스트
- [ ] 모든 Pydantic 모델 import (`from pydantic import ...`) 제거
- [ ] BaseModel 상속 클래스 → protobuf 메시지 import로 대체
- [ ] 모델 생성/검증/직렬화(`model_dump`, `model_validate` 등) → protobuf 메시지 생성/SerializeToString/ParseFromString 등으로 대체
- [ ] API/브로커/테스트 등 데이터 구조 전달부를 protobuf 메시지로 통일
- [ ] 테스트 코드도 protobuf 메시지 기반으로 리팩토링
- [ ] 관련 주석/문서/가이드도 protobuf 기준으로 수정

## 2. 예시: DataNode
- 기존: `from src.qmtl.models.datanode import DataNode`
- 변경: `from src.qmtl.models.generated import qmtl_datanode_pb2 as pb`
- 사용: `node = pb.DataNode(node_id="...", ...)`

## 3. 주의사항
- 필드명/타입/옵셔널 여부가 완전히 일치하는지 확인
- map/repeated/enum 등 protobuf 타입에 맞게 데이터 변환 필요
- 직렬화: `msg.SerializeToString()`, 역직렬화: `pb.DataNode.FromString(data)`
- 테스트는 round-trip(직렬화→역직렬화)로 신뢰성 검증

---

> NG-2-4: 기존 코드에서 Pydantic 모델 사용처를 protobuf 기반으로 일괄 치환 가이드 (2025-05-20)
