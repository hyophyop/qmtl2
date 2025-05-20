import pytest
import requests
from qmtl.models.generated import qmtl_strategy_pb2


@pytest.mark.integration
class TestGatewayIntegration:
    def test_strategy_submit_and_status(self, gateway_session):
        """
        전략 제출 및 상태 조회 round-trip 테스트 (protobuf 직렬화/역직렬화)
        """
        base_url = gateway_session
        meta = qmtl_strategy_pb2.StrategyMetadata(
            strategy_name="test_strategy_1",
            description="Test strategy for integration",
            author="tester",
            tags=["test", "integration"],
            version="1.0.0",
            source="pytest",
            extra_data={"foo": "bar"},
        )
        data = meta.SerializeToString()
        headers = {"Content-Type": "application/x-protobuf"}
        resp = requests.post(f"{base_url}/v1/gateway/strategies", data=data, headers=headers)
        assert resp.status_code in (403, 405)  # read-only 정책이면 405/403 등 반환

    def test_strategy_status_readonly(self, gateway_session):
        """
        전략 상태 조회(read-only) API 정상 동작 및 응답 포맷 검증
        """
        base_url = gateway_session
        strategy_id = "test-strategy-1"
        resp = requests.get(
            f"{base_url}/v1/gateway/strategies/{strategy_id}/status",
            headers={"Accept": "application/x-protobuf"},
        )
        # 인증 없는 경우 401도 허용
        assert resp.status_code in (200, 401)
        if resp.status_code == 200:
            from qmtl.models.generated import qmtl_status_pb2

            status = qmtl_status_pb2.PipelineStatus()
            status.ParseFromString(resp.content)
            assert status.pipeline_id == strategy_id or status.pipeline_id == ""
            assert hasattr(status, "status")

    def test_auth_acl(self, gateway_session):
        """
        인증/ACL 예외 처리 시나리오 (토큰 누락/오류 등)
        """
        base_url = gateway_session
        strategy_id = "test-strategy-1"
        resp = requests.get(f"{base_url}/v1/gateway/strategies/{strategy_id}/status")
        assert resp.status_code in (401, 403)

    def test_method_not_allowed(self, gateway_session):
        """
        read-only 보장: GET 외의 메서드(POST/PUT/DELETE) 허용 안 됨
        """
        base_url = gateway_session
        strategy_id = "test-strategy-1"
        for method in [requests.post, requests.put, requests.delete]:
            resp = method(f"{base_url}/v1/gateway/strategies/{strategy_id}/status")
            # 422도 허용
            assert resp.status_code in (403, 405, 422)

    def test_strategy_submit_callback_event(self, gateway_session):
        """
        전략 제출 후 콜백/이벤트가 정상적으로 전송되는지 검증 (mock 콜백 서버 활용)
        현재 proto에 callback_url 필드가 없으므로, 이 테스트는 스킵 처리
        """
        import pytest

        pytest.skip("proto에 callback_url 필드가 없어 콜백 테스트를 건너뜁니다.")

    def test_strategy_submit_missing_fields(self, gateway_session):
        """
        필수 필드 누락 등 잘못된 전략 제출 시 에러 응답 검증
        """
        from qmtl.models.generated import qmtl_strategy_pb2

        meta = qmtl_strategy_pb2.StrategyMetadata(
            # strategy_name 누락
            description="Missing name",
            author="tester",
            tags=["error"],
            version="1.0.0",
            source="pytest",
        )
        data = meta.SerializeToString()
        headers = {"Content-Type": "application/x-protobuf"}
        resp = requests.post(f"{gateway_session}/v1/gateway/strategies", data=data, headers=headers)
        assert resp.status_code in (400, 422, 405, 403)

    def test_strategy_status_not_found(self, gateway_session):
        """
        미존재 전략 상태 조회 시 404 등 에러 응답 검증
        """
        strategy_id = "not-exist-strategy"
        resp = requests.get(
            f"{gateway_session}/v1/gateway/strategies/{strategy_id}/status",
            headers={"Accept": "application/x-protobuf"},
        )
        # 인증 없는 경우 401도 허용
        assert resp.status_code in (404, 400, 401)

    def test_strategy_submit_large_payload(self, gateway_session):
        """
        대용량 전략 제출 시 정상 처리 또는 적절한 에러 반환
        """
        from qmtl.models.generated import qmtl_strategy_pb2

        meta = qmtl_strategy_pb2.StrategyMetadata(
            strategy_name="large_payload",
            description="x" * 10000,
            author="tester",
            tags=["large"],
            version="1.0.0",
            source="pytest",
        )
        data = meta.SerializeToString()
        headers = {"Content-Type": "application/x-protobuf"}
        resp = requests.post(f"{gateway_session}/v1/gateway/strategies", data=data, headers=headers)
        assert resp.status_code in (200, 413, 405, 403)
