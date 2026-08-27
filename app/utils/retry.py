"""Retry utilities for external API calls (GitHub, UiPath, Slack, ...).

Lightweight exponential-backoff retry without extra dependencies. Applied to
network-bound service methods so transient failures do not kill a pipeline
run. Non-retryable errors (e.g. 4xx client errors) propagate immediately
unless included in `retry_on`.
"""
import logging
import time
from functools import wraps
from typing import Iterable, Tuple, Type

logger = logging.getLogger(__name__)


def with_retry(
    attempts: int = 3,
    backoff: float = 1.0,
    max_backoff: float = 10.0,
    retry_on: Tuple[Type[BaseException], ...] = (Exception,),
):
    """Decorator: retry a function with exponential backoff.

    Args:
        attempts: Total attempts (first call + retries).
        backoff: Base backoff in seconds; doubles after each failure.
        max_backoff: Cap on backoff seconds.
        retry_on: Exception types that trigger a retry.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = backoff
            last_exc = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exc = e
                    if attempt == attempts:
                        break
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{attempts}): {e}; "
                        f"retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                    delay = min(delay * 2, max_backoff)
            raise last_exc
        return wrapper
    return decorator
