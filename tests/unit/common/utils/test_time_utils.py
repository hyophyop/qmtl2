from qmtl.common.utils.time_utils import (
    add_seconds,
    diff_seconds,
    from_iso,
    from_timestamp,
    now_utc,
    to_iso,
    to_timestamp,
)


def test_now_utc_and_iso():
    dt = now_utc()
    s = to_iso(dt)
    dt2 = from_iso(s)
    assert dt2.tzinfo is not None
    assert abs((dt2 - dt).total_seconds()) < 2


def test_timestamp_conversion():
    dt = now_utc()
    ts = to_timestamp(dt)
    dt2 = from_timestamp(ts)
    assert abs((dt2 - dt).total_seconds()) < 2


def test_add_seconds_and_diff():
    dt = now_utc()
    dt2 = add_seconds(dt, 10)
    assert diff_seconds(dt2, dt) == 10
