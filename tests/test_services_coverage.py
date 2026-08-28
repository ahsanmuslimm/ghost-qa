"""
Phase 3 (Task 3.1): Coverage tests for previously untested services and utils.

Targets: SlackService, ActionCenterService, AuthService, retry util, datetime util.
"""
import time
import pytest
import requests
from datetime import datetime, timezone
from fastapi import HTTPException

from app.services.slack import SlackService
from app.services.action_center import ActionCenterService
from app.services.auth import AuthService
from app.utils.retry import with_retry
from app.utils.datetime_utils import utcnow
from app.models import PipelineRun, TestCase, RiskLevel


class TestSlackService:
    def test_demo_mode_notification(self):
        """Demo mode returns a stub instead of calling Slack."""
        service = SlackService()
        service.enabled = False
        result = service.send_notification("Title", "Message")
        assert result == {"demo": True, "title": "Title", "message": "Message"}

    def test_demo_mode_run_summary(self):
        """Run summary formats risk and routes through send_notification."""
        service = SlackService()
        service.enabled = False
        result = service.send_run_summary({
            "repository": "org/repo",
            "pr_number": 12,
            "total_tests": 5,
            "passed": 4,
            "failed": 1,
            "risk_level": "high",
            "recommendation": "Manual review required"
        })
        assert result["demo"] is True
        assert "org/repo" in result["message"]
        assert "HIGH" in result["message"]

    def test_enabled_success(self, monkeypatch):
        """Enabled service posts to Slack and returns the API response."""
        captured = {}

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {"ok": True}

        def fake_post(url, headers=None, json=None, timeout=None):
            captured["url"] = url
            captured["payload"] = json
            return FakeResponse()

        monkeypatch.setattr(requests, "post", fake_post)
        service = SlackService()
        service.enabled = True
        result = service.send_notification("Title", "Message")
        assert result == {"ok": True}
        assert captured["url"] == "https://slack.com/api/chat.postMessage"
        assert captured["payload"]["blocks"][0]["text"]["text"] == "👻 Title"

    def test_enabled_failure_returns_none(self, monkeypatch):
        """Network failures are swallowed and return None."""
        def fake_post(*args, **kwargs):
            raise requests.exceptions.ConnectionError("boom")

        monkeypatch.setattr(requests, "post", fake_post)
        service = SlackService()
        service.enabled = True
        assert service.send_notification("Title", "Message") is None


class TestActionCenterService:
    def _make_pipeline(self):
        return PipelineRun(
            id="run-ac-1", repository_id="repo-1", trigger_type="github_pr",
            github_pr_number=77, status="queued"
        )

    def _make_test(self):
        tc = TestCase(id="tc-ac-1", pipeline_run_id="run-ac-1", title="AC test")
        tc.risk_level = RiskLevel.high
        return tc

    def test_disabled_create_task_returns_none(self):
        service = ActionCenterService()
        service.enabled = False
        assert service.create_task(self._make_pipeline(), [self._make_test()]) is None

    def test_disabled_poll_returns_unknown(self):
        service = ActionCenterService()
        service.enabled = False
        assert service.poll_task("task-1") == {"Status": "Unknown"}

    def test_disabled_cancel_is_noop(self):
        service = ActionCenterService()
        service.enabled = False
        service.cancel_task("task-1")  # must not raise

    def test_enabled_create_task_success(self, monkeypatch):
        captured = {}

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {"Id": "task-42"}

        def fake_post(url, headers=None, json=None, timeout=None):
            captured["payload"] = json
            return FakeResponse()

        service = ActionCenterService()
        service.enabled = True
        monkeypatch.setattr(service, "_get_access_token", lambda: "tok")
        monkeypatch.setattr(requests, "post", fake_post)

        task_id = service.create_task(self._make_pipeline(), [self._make_test()])
        assert task_id == "task-42"
        assert captured["payload"]["Data"]["pipelineRunId"] == "run-ac-1"
        assert captured["payload"]["Data"]["tests"][0]["risk"] == "high"

    def test_enabled_create_task_failure_returns_none(self, monkeypatch):
        def fake_post(*args, **kwargs):
            raise requests.exceptions.Timeout("timeout")

        service = ActionCenterService()
        service.enabled = True
        monkeypatch.setattr(service, "_get_access_token", lambda: "tok")
        monkeypatch.setattr(requests, "post", fake_post)
        assert service.create_task(self._make_pipeline(), [self._make_test()]) is None

    def test_enabled_poll_extracts_decisions(self, monkeypatch):
        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "Status": "Completed",
                    "Data": {"ApprovedTestIds": ["t1"], "RejectedTestIds": ["t2"]}
                }

        def fake_get(url, headers=None, timeout=None):
            return FakeResponse()

        service = ActionCenterService()
        service.enabled = True
        monkeypatch.setattr(service, "_get_access_token", lambda: "tok")
        monkeypatch.setattr(requests, "get", fake_get)

        result = service.poll_task("task-1")
        assert result["Status"] == "Completed"
        assert result["ApprovedTestIds"] == ["t1"]
        assert result["RejectedTestIds"] == ["t2"]


class TestAuthService:
    def _service_with_user(self):
        service = AuthService()
        service._credentials["user@ghost.qa"] = {
            "password_hash": service._hash_password("s3cret"),
            "role": "approver"
        }
        return service

    def test_token_roundtrip(self):
        service = AuthService()
        token = service.create_token("user@ghost.qa", "approver")["token"]
        payload = service.verify_token(token)
        assert payload["sub"] == "user@ghost.qa"
        assert payload["role"] == "approver"

    def test_invalid_role_rejected(self):
        service = AuthService()
        with pytest.raises(ValueError):
            service.create_token("user@ghost.qa", "superadmin")

    def test_garbage_token_rejected(self):
        service = AuthService()
        with pytest.raises(HTTPException) as exc:
            service.verify_token("not-a-jwt")
        assert exc.value.status_code == 401

    def test_expired_token_rejected(self):
        import jwt as pyjwt
        service = AuthService()
        expired = pyjwt.encode(
            {"sub": "user@ghost.qa", "role": "viewer",
             "exp": int(time.time()) - 100, "iat": int(time.time()) - 200},
            service._secret, algorithm="HS256"
        )
        with pytest.raises(HTTPException) as exc:
            service.verify_token(expired)
        assert exc.value.status_code == 401

    def test_authenticate_success_and_failure(self):
        service = self._service_with_user()
        assert service.authenticate("user@ghost.qa", "s3cret") is not None
        assert service.authenticate("user@ghost.qa", "wrong") is None
        assert service.authenticate("nobody@ghost.qa", "s3cret") is None

    def test_get_user_role(self):
        service = self._service_with_user()
        assert service.get_user_role("user@ghost.qa") == "approver"
        assert service.get_user_role("nobody@ghost.qa") is None


class TestRetryUtil:
    def test_succeeds_after_transient_failures(self):
        calls = {"n": 0}

        @with_retry(attempts=3, backoff=0.01)
        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise ConnectionError("transient")
            return "ok"

        assert flaky() == "ok"
        assert calls["n"] == 3

    def test_raises_after_attempts_exhausted(self):
        calls = {"n": 0}

        @with_retry(attempts=2, backoff=0.01)
        def always_fails():
            calls["n"] += 1
            raise ConnectionError("permanent")

        with pytest.raises(ConnectionError):
            always_fails()
        assert calls["n"] == 2

    def test_non_retryable_error_propagates_immediately(self):
        calls = {"n": 0}

        @with_retry(attempts=3, backoff=0.01, retry_on=(ConnectionError,))
        def value_error():
            calls["n"] += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            value_error()
        assert calls["n"] == 1


class TestDatetimeUtil:
    def test_utcnow_is_naive_utc(self):
        now = utcnow()
        assert now.tzinfo is None
        delta = abs((datetime.now(timezone.utc).replace(tzinfo=None) - now).total_seconds())
        assert delta < 2
