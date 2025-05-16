from typing import Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def model_to_dict(model: BaseModel) -> dict:
    """Pydantic v2 스타일 모델을 dict로 변환"""
    return model.model_dump()


def model_to_json(model: BaseModel, **kwargs) -> str:
    """Pydantic v2 스타일 모델을 JSON 문자열로 변환"""
    return model.model_dump_json(**kwargs)


def dict_to_model(model_class: Type[T], data: dict) -> T:
    """dict를 Pydantic v2 스타일 모델로 변환 및 검증"""
    return model_class.model_validate(data)


def json_to_model(model_class: Type[T], data: str) -> T:
    """JSON 문자열을 Pydantic v2 스타일 모델로 변환 및 검증"""
    return model_class.model_validate_json(data)
