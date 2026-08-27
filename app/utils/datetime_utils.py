"""Datetime helpers for Ghost QA.

`datetime.utcnow()` is deprecated since Python 3.12. All existing database
columns store naive UTC datetimes, so this helper produces naive UTC values
via the non-deprecated timezone-aware API, keeping behaviour identical while
silencing the deprecation.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC time as a naive datetime."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
