# QMTL Protobuf 스키마 버전 관리/변경 이력 예시 (NG-2-2-2)

## 예시: protos/qmtl_datanode.proto

```proto
syntax = "proto3";
package qmtl;

// DataNode 관련 메시지 (v1.0.0)
// 변경 이력:
//   - v1.0.0 (2025-05-20): 최초 생성, NodeTags/IntervalSettings/DataNode 등 정의
//   - v1.1.0 (2025-06-01): DataNode에 new_field 추가 (backward compatible)
//   - v2.0.0 (2025-07-01): DataNode.type 필드 타입 변경(string→enum, breaking change)

message DataNode {
  string node_id = 1;
  string type = 2;
  // ...
}
```

## 관리 원칙 요약
- 각 .proto 파일 상단에 버전/변경 이력 주석 필수
- breaking change(필드 삭제/타입 변경/필드 번호 변경 등) 시 major 버전 증가
- backward compatible change(필드 추가 등) 시 minor 버전 증가
- patch는 버그/주석/비호환성 없는 수정에만 사용
- 주요 변경점은 CHANGELOG.md에도 기록

---

> NG-2-2-2: protobuf 스키마 버전 관리(major/minor) 및 변경 이력 관리 가이드 예시 추가 (2025-05-20)
