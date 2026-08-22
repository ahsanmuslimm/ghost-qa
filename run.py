#!/usr/bin/env python3
"""Ghost QA - Entry point"""
from app.main import app
from app.config import settings
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
        log_level="debug" if settings.APP_DEBUG else "info"
    )
