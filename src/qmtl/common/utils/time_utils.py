from datetime import datetime, timedelta, timezone
from typing import Union

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def now_utc() -> datetime:
    """UTC now 반환 (timezone aware)"""
    return datetime.now(timezone.utc)


def to_iso(dt: datetime) -> str:
    """datetime을 ISO8601 문자열로 변환"""
    return dt.astimezone(timezone.utc).isoformat()


def from_iso(s: str) -> datetime:
    """ISO8601 문자열을 datetime으로 변환"""
    return datetime.fromisoformat(s)


def to_timestamp(dt: datetime) -> float:
    """datetime을 POSIX timestamp(float)로 변환"""
    return dt.timestamp()


def from_timestamp(ts: Union[int, float]) -> datetime:
    """POSIX timestamp를 datetime(UTC)로 변환"""
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def add_seconds(dt: datetime, seconds: int) -> datetime:
    """datetime에 초 단위 덧셈"""
    return dt + timedelta(seconds=seconds)


def diff_seconds(dt1: datetime, dt2: datetime) -> int:
    """두 datetime의 차이를 초 단위로 반환"""
    return int((dt1 - dt2).total_seconds())
