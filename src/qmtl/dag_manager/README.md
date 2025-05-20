# QMTL DAG Manager

이 디렉토리는 글로벌 DAG, 노드, 의존성, 메타데이터, 이벤트, 토픽 관리의 단일 책임 서비스를 위한 코드가 위치합니다.

## 서비스별 책임 및 구조

- **Registry**: 메타데이터(노드/전략/DAG/의존성/이력) 관리의 진입점 서비스. 정책 Node ID, Pipeline ID만 사용하며, Neo4j 기반으로 모든 엔티티/관계를 관리합니다.
- **Strategy**: DataNode DAG 파싱/구성/검증/탐색/위상정렬 등 전략 및 DAG 관련 핵심 로직을 담당합니다.
- **Execution**: 파이프라인 및 노드의 상태 관리(초기화/업데이트/조회/정리 등)를 담당하며, 실제 운영에서는 Redis 등 외부 저장소 연동을 염두에 둔 구조입니다.
- **Event**: Redis Pub/Sub 기반 이벤트 구독/알림 연동, 대시보드/알림 시스템 연동 예시를 제공합니다.

> 모든 데이터 구조는 **protobuf contract 기반**으로 관리되며, 향후 Pydantic 모델은 완전히 제거될 예정입니다. (자세한 책임 분류 및 정책은 architecture.md 참고)

---

## 빌드
uv pip install -r requirements.txt

## 도커 빌드
DOCKER_BUILDKIT=1 docker build -t qmtl-dag-manager .

## 실행
python3 -m qmtl.dag_manager

## 독립 실행/테스트 환경 안내

### 로컬 가상환경 실행
```sh
make run
```

### 단위 테스트
```sh
make test
```

### 도커/컨테이너 실행 (smoke test)
```sh
docker-compose up --build -d
docker-compose down
```
