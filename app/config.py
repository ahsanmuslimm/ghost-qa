from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Application
    APP_NAME: str = "Ghost QA"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_PORT: int = 8000
    APP_HOST: str = "0.0.0.0"  # nosec B104 -- bind inside the container; exposure is controlled by the orchestrator
    DEMO_MODE: bool = False
    AUTO_APPROVE: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./ghost_qa.db"
    DATABASE_URL_SQLITE: str = "sqlite:///./ghost_qa.db"

    # Connection pooling — applied to non-SQLite engines (PostgreSQL in prod)
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_POOL_PRE_PING: bool = True

    # GitHub
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    GITHUB_API_BASE: str = "https://api.github.com"

    # AI providers — Gemini is primary (free tier), Anthropic/XAI are fallbacks.
    # AI_PROVIDER: "auto" | "gemini" | "anthropic" | "xai" | "demo"
    AI_PROVIDER: str = "auto"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Anthropic Claude (optional fallback)
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20240620"

    # XAI (Grok) — optional fallback
    XAI_API_KEY: Optional[str] = None
    GROK_MODEL: str = "grok-4-1-fast-reasoning"

    # UiPath
    UIPATH_CLIENT_ID: Optional[str] = None
    UIPATH_CLIENT_SECRET: Optional[str] = None
    UIPATH_TENANT_NAME: Optional[str] = None
    UIPATH_ORG_ID: Optional[str] = None
    UIPATH_ENVIRONMENT_ID: Optional[str] = None
    UIPATH_TEST_FOLDER: str = "GhostQA"
    UIPATH_EXECUTION_TIMEOUT_SECONDS: int = 300
    UIPATH_TEST_MANAGER_BASE: str = "https://cloud.uipath.com"
    UIPATH_AUTH_URL: str = "https://cloud.uipath.com/identity/connect/token"

    # Slack (optional)
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_CHANNEL: str = "ghost-qa-alerts"

    # Security
    SECRET_KEY: str = "change-me-in-production"

    # Auth & JWT
    JWT_EXPIRY_MINUTES: int = Field(default=60, ge=15, le=1440)
    AUTH_USERS: str = '{"admin@ghost.qa": {"password_hash": "changeme", "role": "approver"}}'

    # RBAC — bootstrap admin password used when seeding the users table
    ADMIN_DEFAULT_PASSWORD: str = "Admin123!"

    # CORS — comma-separated origins; "*" allows everything (dev default)
    CORS_ORIGINS: str = "*"

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True

    # Approval SLA
    APPROVAL_SLA_WARN_HOURS: int = 4
    APPROVAL_SLA_REJECT_HOURS: int = 24

    # UiPath Action Center
    UIPATH_ACTION_CENTER_BASE: str = "https://cloud.uipath.com"


settings = Settings()
