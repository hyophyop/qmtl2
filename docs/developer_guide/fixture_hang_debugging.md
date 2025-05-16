# Docker 기반 테스트 픽스처 hang/halt 디버깅 및 방지 가이드

## 1. docker_compose_up_down 픽스처 자체에서의 블로킹
- 컨테이너 기동(docker-compose up) 시 healthcheck 완료까지 무한 wait 루프가 hang의 주 원인
- busy-wait, 포트 바인드 실패, 이미지 pull 지연 등도 원인
- **해결:** healthcheck에 타임아웃, busy-wait에 sleep 삽입, pytest-timeout 등 상위 한도 설정

## 2. Event loop 충돌 (pytest-asyncio + FastAPI TestClient)
- async def 픽스처와 TestClient의 anyio 루프가 충돌하면 RuntimeError 또는 hang 발생
- **해결:** anyio_backend 파라미터 사용, 동기/비동기 혼용 피하기

## 3. 네트워크 포트 충돌 및 미정리
- 이전 테스트 실패로 포트가 TIME_WAIT 등으로 남아 있으면 docker compose up이 무한 재시도
- **해결:** cleanup에서 --remove-orphans, netstat로 포트 상태 확인, sleep 삽입

## 4. FastAPI 라우트 내부의 외부 DB 연결 재시도
- DB가 준비되지 않은 상태에서 무한 재시도 루프가 hang 유발
- **해결:** Neo4j 드라이버의 재시도/타임아웃 옵션 조정, 라우트에서 적절히 실패 처리

## 5. 픽스처-레벨 로그 및 타임아웃
- pytest-timeout 플러그인, --log-cli-level, -s 옵션으로 hang 위치 추적

---

## 실전 디버깅/방지 순서
1. **단독 실행**: pytest tests/integration/test_registry.py::test_node_dependency_management -vv -s --maxfail=1
2. **픽스처 비활성화 후 재실행**: @pytest.mark.skip(reason="fixture bypass")
3. **픽스처 내부 단계별 print()/logger.info 삽입**
4. **pytest-timeout 등으로 단계별 소요 시간 기록**
5. **컨테이너 health, 포트 상태, 이벤트 루프 충돌 여부 개별 확인**

---

## TL;DR
- 도커-기반 픽스처가 컨테이너 기동·health check·event-loop 충돌 어느 단계에서든 블로킹을 일으킬 수 있음
- 방지: (1) health check 타임아웃, (2) pytest-timeout, (3) anyio 루프 하나만 사용, (4) 포트 충돌 정리, (5) yield 뒤 cleanup 로깅 필수
- hang 발생 시: 픽스처 제거 후 테스트 → 통과하면 픽스처 문제, 단계별 로깅/타임아웃으로 원인 추적
