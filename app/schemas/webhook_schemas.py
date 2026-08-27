"""Pydantic validation schemas for GitHub webhook payloads.

Models are intentionally permissive (`extra="allow"`) because GitHub's
pull_request payload carries many optional fields that evolve over time.
Validation guarantees the fields the pipeline relies on (PR number, head SHA,
repository identity) are present and well-typed, and rejects garbage input.
"""
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

# GitHub allows up to 25 MB webhook deliveries; cap lower for safety.
MAX_WEBHOOK_PAYLOAD_BYTES = 10 * 1024 * 1024


class PullRequestPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    number: int = Field(..., ge=1)
    title: str = ""
    body: Optional[str] = None
    state: Optional[str] = None
    diff_url: Optional[str] = None
    html_url: Optional[str] = None
    head: Dict[str, Any] = Field(default_factory=dict)
    base: Dict[str, Any] = Field(default_factory=dict)


class RepositoryPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    full_name: str = ""
    name: str = ""
    owner: Dict[str, Any] = Field(default_factory=dict)


class GitHubPRWebhookPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    action: Optional[str] = None
    repository: RepositoryPayload = Field(default_factory=RepositoryPayload)
    pull_request: Optional[PullRequestPayload] = None
