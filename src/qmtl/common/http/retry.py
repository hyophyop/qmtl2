import functools
import time


def with_retry(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = kwargs.pop("max_retries", 3)
        backoff = kwargs.pop("backoff", 0.5)
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception:
                if attempt == max_retries - 1:
                    raise
                time.sleep(backoff * (2**attempt))

    return wrapper
