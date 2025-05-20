"""
Gateway Golden 테스트 템플릿

이 모듈은 Gateway 서비스에서 사용할 수 있는 Golden 테스트 템플릿을 제공합니다.
"""

import pytest
import json
import os
import base64
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar
from google.protobuf.message import Message
from google.protobuf import json_format

# 타입 정의
T = TypeVar("T", bound=Message)


class GoldenFileHandler:
    """Golden 파일 처리 핸들러 클래스"""

    def __init__(self, base_dir: Optional[Path] = None, service_name: str = "gateway"):
        """
        Golden 파일 핸들러 초기화

        Args:
            base_dir: Golden 파일 기본 디렉토리 (기본값: tests/golden_files)
            service_name: 서비스 이름 (기본값: gateway)
        """
        if base_dir is None:
            self.base_dir = Path(__file__).parent.parent / "golden_files" / service_name
        else:
            self.base_dir = base_dir / service_name

        # 디렉토리 생성
        os.makedirs(self.base_dir, exist_ok=True)

    def save_golden_file(self, name: str, data: Any, binary: bool = False) -> None:
        """
        Golden 파일 저장

        Args:
            name: 파일 이름 (확장자 제외)
            data: 저장할 데이터
            binary: 바이너리 데이터 여부
        """
        if binary:
            # 바이너리 파일 저장
            with open(self.base_dir / f"{name}.bin", "wb") as f:
                f.write(data)

            # 디버깅용 JSON 파일도 저장
            try:
                if isinstance(data, bytes):
                    json_data = {"binary_base64": base64.b64encode(data).decode("utf-8")}
                    with open(self.base_dir / f"{name}.json", "w") as f:
                        json.dump(json_data, f, indent=2)
            except Exception:
                pass  # JSON 변환 실패 시 무시
        else:
            # JSON 파일 저장
            with open(self.base_dir / f"{name}.json", "w") as f:
                json.dump(data, f, indent=2)

    def load_golden_file(self, name: str, binary: bool = False) -> Any:
        """
        Golden 파일 로드

        Args:
            name: 파일 이름 (확장자 제외)
            binary: 바이너리 데이터 여부

        Returns:
            로드된 데이터
        """
        if binary:
            with open(self.base_dir / f"{name}.bin", "rb") as f:
                return f.read()
        else:
            with open(self.base_dir / f"{name}.json", "r") as f:
                return json.load(f)


def proto_to_json(proto_obj: Message) -> Dict[str, Any]:
    """
    Protobuf 객체를 JSON으로 변환

    Args:
        proto_obj: 변환할 Protobuf 메시지 객체

    Returns:
        JSON 형식의 딕셔너리
    """
    return json.loads(json_format.MessageToJson(proto_obj, preserving_proto_field_name=True))


def verify_golden_file(
    proto_obj: Message,
    name: str,
    golden_handler: GoldenFileHandler,
    update_mode: bool = False,
    exclude_fields: Optional[list] = None,
) -> bool:
    """
    Protobuf 객체와 Golden 파일 비교

    Args:
        proto_obj: 비교할 Protobuf 메시지 객체
        name: Golden 파일 이름 (확장자 제외)
        golden_handler: Golden 파일 핸들러
        update_mode: Golden 파일 업데이트 모드 여부
        exclude_fields: 비교에서 제외할 필드 목록

    Returns:
        비교 결과 (일치하면 True, 불일치하면 False)
    """
    # JSON 형식으로 직렬화
    current_json = proto_to_json(proto_obj)

    # 제외할 필드 처리
    if exclude_fields:
        for field in exclude_fields:
            if field in current_json:
                del current_json[field]

    # 업데이트 모드인 경우 Golden 파일 저장
    if update_mode:
        golden_handler.save_golden_file(name, current_json)
        return True

    # Golden 파일과 비교
    try:
        golden_json = golden_handler.load_golden_file(name)

        # 제외할 필드 처리
        if exclude_fields:
            for field in exclude_fields:
                if field in golden_json:
                    del golden_json[field]

        # 비교
        return current_json == golden_json
    except FileNotFoundError:
        if update_mode:
            golden_handler.save_golden_file(name, current_json)
            return True
        else:
            return False


# 템플릿 테스트 예시
class TemplateGoldenTests:
    """Golden 테스트 템플릿 클래스"""

    @pytest.mark.template
    def test_golden_template(self):
        """Golden 테스트 템플릿"""
        # 이 테스트는 실행되지 않음, 단지 템플릿으로만 사용
        pytest.skip("This is just a template test")

        # Golden 파일 핸들러 생성
        golden_handler = GoldenFileHandler()

        # 테스트할 Protobuf 객체 생성
        from qmtl.models.generated import qmtl_strategy_pb2 as strategy_pb2

        proto_obj = strategy_pb2.StrategyMetadata(
            strategy_name="template_test",
            description="Golden template test",
            version="1.0.0",
        )

        # Golden 파일 업데이트 모드 확인
        update_mode = os.environ.get("UPDATE_GOLDEN_FILES") == "1"

        # Golden 파일 비교 또는 생성
        if update_mode:
            # Golden 파일 저장
            golden_handler.save_golden_file("template_strategy", proto_to_json(proto_obj))
            golden_handler.save_golden_file(
                "template_strategy_binary", proto_obj.SerializeToString(), binary=True
            )
            pytest.skip("Golden 파일 업데이트 모드")
        else:
            # Golden 파일과 비교
            try:
                is_match = verify_golden_file(
                    proto_obj=proto_obj,
                    name="template_strategy",
                    golden_handler=golden_handler,
                    exclude_fields=["created_at", "updated_at"],
                )
                assert is_match, "Golden 파일과 일치하지 않음"
            except FileNotFoundError:
                pytest.skip(
                    "Golden 파일이 없습니다. UPDATE_GOLDEN_FILES=1 환경 변수로 테스트를 실행하여 생성하세요."
                )
