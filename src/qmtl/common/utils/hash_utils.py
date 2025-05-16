import hashlib
from typing import Union


def sha256_hex(data: Union[str, bytes]) -> str:
    """sha256 해시 hex 반환"""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def md5_hex(data: Union[str, bytes]) -> str:
    """md5 해시 hex 반환"""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.md5(data).hexdigest()
