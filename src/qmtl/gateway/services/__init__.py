"""Gateway 서비스 패키지.

이 패키지는 Gateway 서비스의 비즈니스 로직을 구현하는 클래스를 포함합니다:
- WorkQueueService: 작업 큐 관리 및 처리
- CallbackService: SDK에 대한 콜백/이벤트 처리
- DagSyncService: DAG Manager와 SDK 간 동기화 처리
- StateTrackingService: 전략 및 노드 상태 추적/제공
- QueryNodeResolver: TAG 기반 QueryNode 메타데이터 해석/제공
"""
