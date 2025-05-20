# QMTL Protobuf 스키마 버전 관리 가이드 (NG-2-2)

## 1. 파일 구조 및 네이밍
- 모든 .proto 파일은 `protos/` 디렉토리에 위치
- 파일명은 도메인별로 구분: `qmtl_datanode.proto`, `qmtl_strategy.proto` 등
- package는 `qmtl`로 통일

## 2. 버전 관리 원칙
- 각 .proto 파일 상단에 버전(major.minor.patch) 및 변경 이력 주석 필수
- breaking change(필드 삭제/타입 변경/필드 번호 변경 등) 시 major 버전 증가
- backward compatible change(필드 추가 등) 시 minor 버전 증가
- patch는 버그/주석/비호환성 없는 수정에만 사용
- 메시지/필드 이름, 번호는 절대 재사용 금지

## 3. 변경 이력 관리
- 각 .proto 파일 내 주석에 변경 이력(날짜, 변경자, 주요 변경점) 기록
- 주요 변경 시 CHANGELOG.md에도 반영

## 4. 필드 정의 규칙
- 필수/선택 필드 명확히 구분 (proto3: optional 키워드 사용)
- map/repeated/enum 등 복합 타입은 실제 사용 예시와 일치하도록 설계
- 중첩 메시지/타입은 별도 메시지로 분리 권장

## 5. 스키마 변경 프로세스
1. 변경 필요성 논의 및 이슈 등록
2. .proto 파일 수정 및 변경 이력 주석 추가
3. 관련 코드/테스트/문서 일괄 수정
4. 코드 리뷰 및 main 브랜치 반영
5. 버전/변경점 CHANGELOG.md에 기록

---

> NG-2-2: protobuf .proto 스키마 설계 및 버전 관리 체계 도입 완료 (2025-05-20)
