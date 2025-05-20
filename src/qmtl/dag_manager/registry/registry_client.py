"""
Registry 클라이언트: Orchestrator에서 Registry 서비스와의 통신을 담당하는 클래스
"""

import logging
from typing import Dict, List, Optional

import httpx
from httpx import Client, Response

from qmtl.common.errors.exceptions import (
    RegistryClientError,
    RegistryConnectionError,
)
from qmtl.models.generated.qmtl_datanode_pb2 import DataNode, DAGEdge
from qmtl.models.generated.qmtl_common_pb2 import IntervalSettings
from qmtl.models.generated.qmtl_strategy_pb2 import (
    StrategySnapshot,
    NodeSnapshot,
    StrategyMetadata,
    StrategyVersion,
)

logger = logging.getLogger(__name__)


class RegistryClient:
    """
    Registry API와 통신하는 클라이언트 클래스
    """

    def __init__(self, base_url: str, timeout: int = 10):
        """
        Args:
            base_url: Registry API의 기본 URL (예: "http://localhost:8000")
            timeout: API 요청 타임아웃 (초)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = Client(timeout=timeout, verify=False)
        # API 경로
        self.nodes_path = f"{self.base_url}/v1/registry/nodes"
        self.strategies_path = f"{self.base_url}/v1/registry/strategies"
        self.health_path = f"{self.base_url}/"

    def __del__(self):
        """클라이언트 리소스 정리"""
        if hasattr(self, "client"):
            self.client.close()

    def _handle_response(self, response: Response, expected_status_code: int = 200) -> Dict:
        """응답 처리 공통 로직

        Args:
            response: httpx 응답 객체
            expected_status_code: 기대하는 상태 코드

        Returns:
            응답 JSON 데이터

        Raises:
            RegistryClientError: 응답 상태 코드가 기대와 다른 경우
        """
        try:
            if response.status_code != expected_status_code:
                error_detail = ""
                try:
                    error_detail = response.json().get("detail", "")
                except Exception:
                    error_detail = response.text[:100]

                raise RegistryClientError(
                    f"Registry API 오류 (상태 코드: {response.status_code}): {error_detail}"
                )
            return response.json()
        except httpx.HTTPError as e:
            raise RegistryConnectionError(f"Registry API 연결 오류: {str(e)}")

    def health_check(self) -> Dict:
        """Registry API 헬스 체크

        Returns:
            헬스 상태 정보

        Raises:
            RegistryConnectionError: API 연결 실패 시
        """
        try:
            response = self.client.get(self.health_path)
            return self._handle_response(response)
        except httpx.HTTPError as e:
            raise RegistryConnectionError(f"Registry API 연결 실패: {str(e)}")

    def register_node(self, node: DataNode) -> str:
        """Registry에 노드 등록

        Args:
            node: 등록할 DataNode 객체

        Returns:
            등록된 노드 ID

        Raises:
            RegistryClientError: 노드 등록 실패 시
        """
        try:
            payload = {"node": node.model_dump()}
            response = self.client.post(self.nodes_path, json=payload)
            result = self._handle_response(response, expected_status_code=201)
            return result.get("node_id")
        except httpx.HTTPError as e:
            raise RegistryClientError(f"노드 등록 실패: {str(e)}")

    def get_node(self, node_id: str) -> Optional[DataNode]:
        """노드 ID로 노드 조회

        Args:
            node_id: 조회할 노드 ID

        Returns:
            DataNode 객체 또는 None (존재하지 않는 경우)

        Raises:
            RegistryClientError: API 오류 시
        """
        try:
            url = f"{self.nodes_path}/{node_id}"
            response = self.client.get(url)

            if response.status_code == 404:
                return None

            result = self._handle_response(response)
            if not result or "node" not in result:
                return None

            return DataNode.model_validate(result["node"])
        except httpx.HTTPError as e:
            raise RegistryClientError(f"노드 조회 실패: {str(e)}")
        except Exception as e:
            logger.error(f"노드 데이터 파싱 실패: {str(e)}")
            return None

    def delete_node(self, node_id: str) -> bool:
        """노드 ID로 노드 삭제

        Args:
            node_id: 삭제할 노드 ID

        Returns:
            삭제 성공 여부

        Raises:
            RegistryClientError: API 오류 시
        """
        try:
            url = f"{self.nodes_path}/{node_id}"
            response = self.client.delete(url)

            if response.status_code == 404:
                return False

            result = self._handle_response(response)
            return result.get("success", False)
        except httpx.HTTPError as e:
            raise RegistryClientError(f"노드 삭제 실패: {str(e)}")

    def register_strategy(self, metadata: StrategyMetadata) -> str:
        """Registry에 전략 등록

        Args:
            metadata: 등록할 전략 메타데이터

        Returns:
            등록된, 전략 버전 ID

        Raises:
            RegistryClientError: 전략 등록 실패 시
        """
        try:
            # protobuf 객체면 dict로 변환
            if hasattr(metadata, "DESCRIPTOR"):
                from google.protobuf.json_format import MessageToDict

                payload = {"metadata": MessageToDict(metadata)}
            elif hasattr(metadata, "model_dump"):
                payload = {"metadata": metadata.model_dump()}
            else:
                payload = {"metadata": dict(metadata)}
            response = self.client.post(self.strategies_path, json=payload)
            result = self._handle_response(response, expected_status_code=201)
            return result.get("version_id")
        except httpx.HTTPError as e:
            raise RegistryClientError(f"전략 등록 실패: {str(e)}")

    def get_strategy(self, version_id: str) -> Optional[StrategyVersion]:
        """전략 버전 ID로 전략 조회

        Args:
            version_id: 조회할 전략 버전 ID

        Returns:
            StrategyVersion 객체 또는 None (존재하지 않는 경우)

        Raises:
            RegistryClientError: API 오류 시
        """
        try:
            url = f"{self.strategies_path}/{version_id}"
            response = self.client.get(url)

            if response.status_code == 404:
                return None

            result = self._handle_response(response)
            if not result or "strategy" not in result:
                return None

            return StrategyVersion.model_validate(result["strategy"])
        except httpx.HTTPError as e:
            raise RegistryClientError(f"전략 조회 실패: {str(e)}")
        except Exception as e:
            logger.error(f"전략 데이터 파싱 실패: {str(e)}")
            return None

    def add_contains_relationship(self, strategy_version_id: str, node_id: str) -> bool:
        """전략과 노드 간 CONTAINS 관계 생성

        Args:
            strategy_version_id: 전략 버전 ID
            node_id: 노드 ID

        Returns:
            성공 여부

        Raises:
            RegistryClientError: API 오류 시
        """
        try:
            url = f"{self.strategies_path}/{strategy_version_id}/nodes/{node_id}"
            response = self.client.post(url)

            if response.status_code not in (200, 201):
                return False

            return True
        except httpx.HTTPError as e:
            raise RegistryClientError(f"CONTAINS 관계 생성 실패: {str(e)}")

    def remove_contains_relationship(self, strategy_version_id: str, node_id: str) -> bool:
        """전략과 노드 간 CONTAINS 관계 삭제

        Args:
            strategy_version_id: 전략 버전 ID
            node_id: 노드 ID

        Returns:
            성공 여부

        Raises:
            RegistryClientError: API 오류 시
        """
        try:
            url = f"{self.strategies_path}/{strategy_version_id}/nodes/{node_id}"
            response = self.client.delete(url)

            if response.status_code == 404:
                return False

            return True
        except httpx.HTTPError as e:
            raise RegistryClientError(f"CONTAINS 관계 삭제 실패: {str(e)}")

    def get_node_ref_count(self, node_id: str) -> int:
        """노드의 참조 카운트 조회

        Args:
            node_id: 노드 ID

        Returns:
            노드를 참조하는 전략 수

        Raises:
            RegistryClientError: API 오류 시
        """
        try:
            url = f"{self.nodes_path}/{node_id}/ref-count"
            response = self.client.get(url)

            if response.status_code == 404:
                return 0

            result = self._handle_response(response)
            return result.get("ref_count", 0)
        except httpx.HTTPError as e:
            raise RegistryClientError(f"노드 참조 카운트 조회 실패: {str(e)}")

    def get_node_ref_strategies(self, node_id: str) -> List[str]:
        """노드를 참조하는 전략 ID 목록 조회

        Args:
            node_id: 노드 ID

        Returns:
            노드를 참조하는 전략 버전 ID 목록

        Raises:
            RegistryClientError: API 오류 시
        """
        try:
            url = f"{self.nodes_path}/{node_id}/ref-strategies"
            response = self.client.get(url)

            if response.status_code == 404:
                return []

            result = self._handle_response(response)
            return result.get("strategy_version_ids", [])
        except httpx.HTTPError as e:
            raise RegistryClientError(f"노드 참조 전략 목록 조회 실패: {str(e)}")

    def get_strategy_nodes(self, strategy_version_id: str) -> List[DataNode]:
        """전략에 포함된 노드 목록 조회

        Args:
            strategy_version_id: 전략 버전 ID

        Returns:
            전략에 포함된 DataNode 객체 목록

        Raises:
            RegistryClientError: API 오류 시
        """
        try:
            url = f"{self.strategies_path}/{strategy_version_id}/nodes"
            response = self.client.get(url)

            if response.status_code == 404:
                return []

            result = self._handle_response(response)
            nodes = []

            for node_data in result.get("nodes", []):
                try:
                    nodes.append(DataNode.model_validate(node_data))
                except Exception as e:
                    logger.error(f"노드 데이터 파싱 실패: {str(e)}")

            return nodes
        except httpx.HTTPError as e:
            raise RegistryClientError(f"전략 노드 목록 조회 실패: {str(e)}")
