"""Centralized service singletons for Ghost QA.

All API routers and background workers should import service instances from
this module instead of instantiating services locally, so every request
shares one configured instance of each service.
"""
from app.services.github import GitHubService
from app.services.ai_brain import AIBrainService
from app.services.approval import ApprovalService
from app.services.executor import ExecutorService
from app.services.risk import RiskEngine
from app.services.healing import HealingService
from app.services.slack import SlackService
from app.services.rbac import RBACService

github_service = GitHubService()
ai_service = AIBrainService()
approval_service = ApprovalService()
executor_service = ExecutorService()
risk_engine = RiskEngine()
healing_service = HealingService()
slack_service = SlackService()
rbac_service = RBACService()

__all__ = [
    "github_service",
    "ai_service",
    "approval_service",
    "executor_service",
    "risk_engine",
    "healing_service",
    "slack_service",
    "rbac_service",
]
