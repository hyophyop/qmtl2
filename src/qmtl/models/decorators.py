import inspect
from typing import Callable, List, Optional

from qmtl.common.utils.hash_utils import sha256_hex


def _get_function_source(f):
    try:
        src = inspect.getsource(f)
        return src
    except Exception:
        return f.__name__


def _make_node_id(f, params: dict):
    src = _get_function_source(f)
    key_params = getattr(f, "_key_params", [])
    param_str = "|".join(f"{k}={params.get(k)}" for k in key_params)
    base = f"{src}|{param_str}|{f._node_type}|{','.join(f._tags)}"
    return sha256_hex(base)[:32]


def node(
    fn: Callable = None, *, key_params: Optional[List[str]] = None, tags: Optional[List[str]] = None
):
    def decorator(f):
        f._is_node = True
        f._node_type = "NODE"
        f._key_params = key_params or []
        f._tags = tags or []

        def get_node_id(params: dict):
            return _make_node_id(f, params)

        f.get_node_id = get_node_id
        return f

    if fn is not None:
        return decorator(fn)
    return decorator


def signal(
    fn: Callable = None, *, key_params: Optional[List[str]] = None, tags: Optional[List[str]] = None
):
    def decorator(f):
        f._is_node = True
        f._node_type = "SIGNAL"
        f._key_params = key_params or []
        f._tags = tags or []

        def get_node_id(params: dict):
            return _make_node_id(f, params)

        f.get_node_id = get_node_id
        return f

    if fn is not None:
        return decorator(fn)
    return decorator
