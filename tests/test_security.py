"""
Phase 3 (Task 3.3): Security tests.

Covers webhook signature enforcement at the HTTP layer, payload validation,
JWT middleware behaviour and endpoint rate limiting.
"""
import json
import time
import hmac
import hashlib
import pytest
import jwt as pyjwt
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import SessionLocal
from app.services import github_service
from app.services.auth import AuthService


@pytest.fixture
def client():
    from app.database import init_db, Base
    init_db()

    session = SessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()

    original = github_service.demo_mode
    github_service.demo_mode = True
    with TestClient(app) as c:
        yield c
    github_service.demo_mode = original


def _payload(pr_number: int):
    return {
        "action": "opened",
        "repository": {
            "id": 987654321,
            "name": "sec-app",
            "full_name": "sec-org/sec-app",
            "owner": {"login": "sec-org"},
            "default_branch": "main"
        },
        "pull_request": {
            "number": pr_number,
            "title": "Security PR",
            "body": "Security test",
            "state": "open",
            "diff_url": f"https://github.com/sec-org/sec-app/pull/{pr_number}.diff",
            "html_url": f"https://github.com/sec-org/sec-app/pull/{pr_number}",
            "user": {"login": "sec-user"},
            "head": {"ref": "feature/sec", "sha": f"sec-{pr_number}"},
            "base": {"ref": "main", "sha": "secbase"},
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z"
        }
    }


def _signed_post(client, body_str, signature_header, pr_number):
    return client.post(
        "/api/webhooks/github",
        content=body_str,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": signature_header
        }
    )


class TestWebhookSignatureEnforcement:
    """Signature verification enforced end-to-end at the HTTP layer."""

    SECRET = "sec-test-secret"

    def _sign(self, body_str: str) -> str:
        digest = hmac.new(
            self.SECRET.encode("utf-8"), body_str.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return f"sha256={digest}"

    def test_wrong_signature_rejected(self, client, monkeypatch):
        monkeypatch.setattr(github_service, "webhook_secret", self.SECRET)
        body = json.dumps(_payload(7001))
        response = _signed_post(client, body, "sha256=deadbeef", 7001)
        assert response.status_code == 401
        assert response.json()["status"] == "invalid_signature"

    def test_wrong_algorithm_rejected(self, client, monkeypatch):
        monkeypatch.setattr(github_service, "webhook_secret", self.SECRET)
        body = json.dumps(_payload(7002))
        sig = self._sign(body).split("=", 1)[1]
        response = _signed_post(client, body, f"sha1={sig}", 7002)
        assert response.status_code == 401
        assert response.json()["status"] == "invalid_signature"

    def test_valid_signature_accepted(self, client, monkeypatch):
        monkeypatch.setattr(github_service, "webhook_secret", self.SECRET)
        body = json.dumps(_payload(7003))
        response = _signed_post(client, body, self._sign(body), 7003)
        assert response.status_code == 200
        assert response.json()["status"] == "pipeline_started"

    def test_missing_signature_accepted_when_no_secret(self, client, monkeypatch):
        monkeypatch.setattr(github_service, "webhook_secret", "")
        response = client.post(
            "/api/webhooks/github",
            json=_payload(7004),
            headers={"X-GitHub-Event": "pull_request"}
        )
        assert response.status_code == 200


class TestPayloadValidation:
    def test_malformed_payload_rejected(self, client):
        # pull_request.number violates ge=1 -> schema validation fails
        response = client.post(
            "/api/webhooks/github",
            json={"action": "opened", "pull_request": {"number": -5}},
            headers={"X-GitHub-Event": "pull_request"}
        )
        assert response.status_code == 400
        assert response.json()["status"] == "invalid_payload"

    def test_oversized_payload_rejected(self, client, monkeypatch):
        import app.api.webhooks as webhooks_module
        monkeypatch.setattr(webhooks_module, "MAX_WEBHOOK_PAYLOAD_BYTES", 500)
        payload = _payload(7005)
        payload["pull_request"]["body"] = "x" * 1000
        response = client.post(
            "/api/webhooks/github",
            json=payload,
            headers={"X-GitHub-Event": "pull_request"}
        )
        assert response.status_code == 413
        assert response.json()["status"] == "payload_too_large"


class TestJWTMiddleware:
    def _token(self):
        service = AuthService()
        return service.create_token("admin@ghost.qa", "approver")["token"]

    def test_protected_endpoint_requires_token(self, client):
        response = client.get("/api/runs")
        assert response.status_code == 401

    def test_missing_bearer_prefix_rejected(self, client):
        response = client.get(
            "/api/runs", headers={"Authorization": self._token()}
        )
        assert response.status_code == 401

    def test_garbage_token_rejected(self, client):
        response = client.get(
            "/api/runs", headers={"Authorization": "Bearer not-a-jwt"}
        )
        assert response.status_code == 401

    def test_wrong_secret_token_rejected(self, client):
        forged = pyjwt.encode(
            {"sub": "admin@ghost.qa", "role": "approver",
             "exp": int(time.time()) + 3600, "iat": int(time.time())},
            "wrong-secret", algorithm="HS256"
        )
        response = client.get(
            "/api/runs", headers={"Authorization": f"Bearer {forged}"}
        )
        assert response.status_code == 401

    def test_expired_token_rejected(self, client):
        expired = pyjwt.encode(
            {"sub": "admin@ghost.qa", "role": "approver",
             "exp": int(time.time()) - 100, "iat": int(time.time()) - 200},
            settings.SECRET_KEY, algorithm="HS256"
        )
        response = client.get(
            "/api/runs", headers={"Authorization": f"Bearer {expired}"}
        )
        assert response.status_code == 401

    def test_valid_token_accepted(self, client):
        response = client.get(
            "/api/runs", headers={"Authorization": f"Bearer {self._token()}"}
        )
        assert response.status_code == 200

    def test_public_paths_bypass_jwt(self, client):
        # Health endpoint — not under /api/
        assert client.get("/").status_code == 200
        # Webhook path is public; GET is not allowed, so 405 proves the
        # request passed the middleware (a JWT block would return 401).
        assert client.get("/api/webhooks/github").status_code == 405


class TestRateLimiting:
    def test_login_rate_limited(self, client):
        """Login endpoint allows 10 attempts per minute, then returns 429."""
        for i in range(10):
            response = client.post(
                "/auth/login",
                json={"email": "admin@ghost.qa", "password": "wrong"}
            )
            assert response.status_code == 401, f"attempt {i + 1} unexpected"

        response = client.post(
            "/auth/login",
            json={"email": "admin@ghost.qa", "password": "wrong"}
        )
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert "Rate limit exceeded" in response.json()["error"]

    def test_webhook_endpoint_has_rate_limit(self):
        """Webhook endpoint is registered with a 60/minute limit."""
        from app.rate_limit import limiter
        limits = limiter._route_limits.get("app.api.webhooks.handle_github_webhook", [])
        assert limits, "no rate limit registered on the webhook endpoint"
        assert str(limits[0].limit) == "60 per 1 minute"

    def test_login_endpoint_has_rate_limit(self):
        from app.rate_limit import limiter
        limits = limiter._route_limits.get("app.api.auth.login", [])
        assert limits, "no rate limit registered on the login endpoint"
        assert str(limits[0].limit) == "10 per 1 minute"
