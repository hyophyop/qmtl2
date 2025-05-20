# QMTL Gateway

이 디렉토리는 작업 큐, DAG 동기화, 콜백, 상태 추적, QueryNode 해석, 중계 등 Gateway 서비스 책임 코드를 포함합니다.

- 기존 registry/ 코드가 이곳으로 이동되었습니다.
- 자세한 책임 분류는 architecture.md 참고.

## 빌드
uv pip install -r requirements.txt

## 도커 빌드
DOCKER_BUILDKIT=1 docker build -t qmtl-gateway .

## 실행
python3 -m qmtl.gateway

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
