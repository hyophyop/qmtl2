import os
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()


def get_env_vars(prefix: str = "") -> Dict[str, Any]:
    """환경 변수 딕셔너리 반환 (prefix 필터 지원)"""
    env = dict(os.environ)
    if prefix:
        env = {k: v for k, v in env.items() if k.startswith(prefix)}
    return env
