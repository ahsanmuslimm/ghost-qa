"""Shared rate limiter instance.

Lives in its own module so API routers can apply limits without importing
app.main (which would create a circular import).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings

limiter = Limiter(key_func=get_remote_address, enabled=settings.RATE_LIMIT_ENABLED)
