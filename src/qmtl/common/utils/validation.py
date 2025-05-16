from typing import Type, TypeVar

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

T = TypeVar("T", bound=BaseModel)


def validate_model(model_class: Type[T], data: dict) -> T:
    """Pydantic v2 스타일 모델 유효성 검증 및 인스턴스 반환"""
    return model_class.model_validate(data)


def is_valid_model(model_class: Type[T], data: dict) -> bool:
    """유효성 검증 결과를 bool로 반환 (예외 발생 X)"""
    try:
        model_class.model_validate(data)
        return True
    except PydanticValidationError:
        return False


def assert_valid_model(model_class: Type[T], data: dict) -> None:
    """유효하지 않으면 AssertionError 발생"""
    model_class.model_validate(data)
