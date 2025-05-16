# QMTL2 테스트 Hanging 디버깅 가이드

## Test Registry Hanging 문제 진단 및 해결

테스트 환경에서 `test_node_dependency_management` 테스트가 hanging되는 문제를 해결하였습니다. 이 문서는 유사한 문제 발생 시 참고할 수 있는 진단 및 해결 가이드입니다.

### 문제 증상

- 테스트가 무한정 진행되며 끝나지 않음 (hanging)
- Registry API의 노드 의존성 관리 관련 테스트에서 주로 발생
- 로그에 404 오류가 표시되거나 타임아웃 없이 대기 상태 지속

### 주요 원인

1. **FastAPI 예외 처리 패턴 오류**
   - `except` 블록에서 직접 `return` 사용
   - HTTP 응답을 리턴하지만 실제로는 전달되지 않는 경우
   - 예외를 제대로 변환하여 전파하지 않는 경우

2. **Neo4j 연결 관련 문제**
   - 기본 타임아웃이 너무 길어 hanging 발생
   - 연결 실패 시 명확한 오류 메시지 없음
   - 트랜잭션 실패 시 무한 재시도

3. **Docker 컨테이너 관련 이슈**
   - 컨테이너 정리가 제대로 되지 않아 포트 충돌
   - 포트 해제 전에 다음 컨테이너 실행 시도

### 해결 방법

#### 1. FastAPI 예외 처리 패턴 수정

```python
# 잘못된 패턴 ❌
try:
    # 로직
    return {"result": result}
except Exception as e:
    return {"error": str(e)}, 500  # FastAPI에서는 동작하지 않음

# 올바른 패턴 ✅
try:
    # 로직
    return {"result": result}
except ValidationError as e:
    raise HTTPException(status_code=422, detail=str(e))
except HTTPException:
    raise  # 이미 HTTPException인 경우 그대로 전파
except Exception as e:
    logger.exception("처리 중 오류")
    raise HTTPException(status_code=500, detail="내부 서버 오류")
```

#### 2. Neo4j 타임아웃 설정 최적화

```python
# 짧은 타임아웃 설정
client = Neo4jClient(
    uri, 
    username, 
    password,
    connection_timeout=3,  # 3초
    max_transaction_retry_time=5000,  # 5초
    connection_acquisition_timeout=5.0  # 5초
)
```

#### 3. Docker 컨테이너 관리 개선

```python
# 컨테이너 정리 명령에 옵션 추가
subprocess.run(
    ["docker-compose", "down", "--remove-orphans", "--timeout", "20"],
    check=False
)

# 포트 정리 대기
time.sleep(2)  # 포트 해제 대기
```

#### 4. 테스트 대기 루프 개선

```python
# 개선된 대기 루프 패턴
for _ in range(30):
    try:
        # 헬스 체크 등
        if success:
            break
    except Exception:
        pass  # 예외 처리 후
    time.sleep(1)  # 항상 실행되는 대기
else:
    # 모든 시도 실패 시
    raise RuntimeError("서비스가 30초 내에 준비되지 않았습니다 (타임아웃)")
```

### 문제 식별 체크리스트

테스트가 hanging되는 경우 다음 체크리스트를 확인하세요:

1. **컨테이너 상태 확인**
   ```bash
   docker ps -a  # 종료된 컨테이너 포함 확인
   docker logs <container_id>  # 로그 확인
   ```

2. **포트 사용 확인**
   ```bash
   lsof -i :7687  # Neo4j 포트
   lsof -i :8000  # Registry API 포트
   ```

3. **상세 로그 확인**
   ```bash
   pytest -vvs test_registry.py::test_node_dependency_management --log-cli-level=DEBUG
   ```

4. **타임아웃 설정으로 테스트**
   ```bash
   # pytest-timeout 활용
   pytest -xvs test_registry.py::test_node_dependency_management --timeout=30
   ```

### 예방 조치

1. **모든 API 엔드포인트 예외 처리 확인**
   - 일관된 예외 처리 패턴 적용
   - `return` 대신 `raise HTTPException` 사용

2. **데이터베이스 연결 타임아웃 설정**
   - 테스트용 짧은 타임아웃 설정
   - 명시적 재시도 로직 구현

3. **테스트 픽스처 안정성 강화**
   - 컨테이너 종료 확인 단계 추가
   - 타임아웃 및 오류 메시지 명확화
