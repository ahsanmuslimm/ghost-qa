"""
Phase 2 (Task 2.7): Service integration tests.

Covers end-to-end data flow between services in DEMO_MODE:
- Webhook → GitHub → AI Brain → Executor → Risk → Slack/GitHub notify
- Healing: AI proposal → approval → execution → verification
- AI Brain response caching
"""
import json
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import (
    PipelineRun, PipelineStatus, TestCase, TestResult, HealAttempt,
    ApprovalStatus, TestCaseStatus, TestOutcome, FailureType,
    TestType, TestPriority, RiskLevel,
    Organisation, Repository
)
from app.services import ai_service, healing_service, github_service


@pytest.fixture(autouse=True)
def github_demo_mode():
    """Force GitHub service demo stubs on (conftest sets a fake token)."""
    original = github_service.demo_mode
    github_service.demo_mode = True
    yield
    github_service.demo_mode = original


@pytest.fixture
def client():
    from app.database import init_db, Base
    init_db()

    # Clear all data from tables
    session = SessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()

    with TestClient(app) as c:
        yield c


def _make_webhook_payload(pr_number: int):
    return {
        "action": "opened",
        "repository": {
            "id": 123456789,
            "name": "demo-app",
            "full_name": "demo-org/demo-app",
            "owner": {"login": "demo-org"},
            "default_branch": "main"
        },
        "pull_request": {
            "number": pr_number,
            "title": "Add login endpoint",
            "body": "Implements JWT login. Fixes #41",
            "state": "open",
            "diff_url": f"https://github.com/demo-org/demo-app/pull/{pr_number}.diff",
            "html_url": f"https://github.com/demo-org/demo-app/pull/{pr_number}",
            "user": {"login": "developer"},
            "head": {"ref": "feature/login", "sha": f"sha-{pr_number}"},
            "base": {"ref": "main", "sha": "base456"},
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z"
        }
    }


class TestFullPipelineIntegration:
    """Webhook → AI generation → execution → risk → completion."""

    def test_full_pipeline_flow(self, client):
        """Complete pipeline from webhook to completed run with results."""
        payload = _make_webhook_payload(pr_number=501)
        response = client.post(
            "/api/webhooks/github",
            json=payload,
            headers={"X-GitHub-Event": "pull_request"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pipeline_started"
        run_id = data["pipeline_run_id"]

        db = SessionLocal()
        try:
            run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
            assert run is not None
            # DEMO_MODE auto-approves and runs synchronously
            assert run.status == PipelineStatus.completed
            assert run.risk_level is not None
            assert run.completed_at is not None

            test_cases = db.query(TestCase).filter(TestCase.pipeline_run_id == run_id).all()
            assert len(test_cases) == 5
            # All tests were auto-approved and executed
            assert all(tc.approval_status == ApprovalStatus.approved for tc in test_cases)
            assert all(tc.outcome is not None for tc in test_cases)

            results = db.query(TestResult).filter(
                TestResult.test_case_id.in_([tc.id for tc in test_cases])
            ).all()
            assert len(results) == len(test_cases)
        finally:
            db.close()

    def test_pipeline_notifies_github(self, client, monkeypatch):
        """Completed pipeline posts a PR comment and updates commit status."""
        calls = {"comment": [], "status": []}
        monkeypatch.setattr(
            github_service, "post_pr_comment",
            lambda **kw: calls["comment"].append(kw) or {"id": 1}
        )
        monkeypatch.setattr(
            github_service, "update_commit_status",
            lambda **kw: calls["status"].append(kw) or {"state": kw["state"]}
        )

        response = client.post(
            "/api/webhooks/github",
            json=_make_webhook_payload(pr_number=502),
            headers={"X-GitHub-Event": "pull_request"}
        )
        assert response.status_code == 200

        assert len(calls["comment"]) == 1
        assert calls["comment"][0]["pr_number"] == 502
        assert "Ghost QA Report" in calls["comment"][0]["body"]
        assert len(calls["status"]) == 1
        assert calls["status"][0]["state"] in ("success", "failure")

    def test_heals_created_for_healable_failures(self, client):
        """Failed tests with healable failure types trigger heal attempts."""
        response = client.post(
            "/api/webhooks/github",
            json=_make_webhook_payload(pr_number=503),
            headers={"X-GitHub-Event": "pull_request"}
        )
        run_id = response.json()["pipeline_run_id"]

        db = SessionLocal()
        try:
            test_ids = [
                tc.id for tc in
                db.query(TestCase).filter(TestCase.pipeline_run_id == run_id).all()
            ]
            failed_healable = db.query(TestResult).filter(
                TestResult.test_case_id.in_(test_ids),
                TestResult.outcome == TestOutcome.failed,
                TestResult.failure_type.in_([
                    FailureType.selector_broken, FailureType.api_contract,
                    FailureType.assertion_stale
                ])
            ).count()
            heals = db.query(HealAttempt).filter(
                HealAttempt.test_case_id.in_(test_ids)
            ).count()
            # Every healable failure must have produced a heal attempt
            # (0 == 0 is valid when the random execution had no healable failures)
            assert heals == failed_healable
        finally:
            db.close()


class TestHealingFlowIntegration:
    """Healing: AI proposal → approval → execution → verification."""

    def _seed_failed_test(self) -> str:
        """Insert a minimal pipeline run + failed test case, return test id."""
        db = SessionLocal()
        try:
            org = Organisation(id=str(uuid.uuid4()), name="heal-org")
            db.add(org)
            db.commit()
            repo = Repository(
                id=str(uuid.uuid4()), organisation_id=org.id,
                full_name="heal-org/heal-app"
            )
            db.add(repo)
            db.commit()

            run_id = str(uuid.uuid4())
            db.add(PipelineRun(
                id=run_id, repository_id=repo.id, trigger_type="github_pr",
                github_pr_number=601, commit_sha="heal-sha",
                status=PipelineStatus.completed
            ))
            test_id = f"{run_id[:8]}-TC-001"
            db.add(TestCase(
                id=test_id,
                pipeline_run_id=run_id,
                title="Checkout flow",
                test_type=TestType.functional,
                priority=TestPriority.p1_high,
                steps=json.dumps([{"action": "Click checkout", "selector": "#checkout", "value": "", "assertion": ""}]),
                expected_result="Order placed",
                approval_status=ApprovalStatus.approved,
                status=TestCaseStatus.failed,
                outcome=TestOutcome.failed,
                failure_type=FailureType.selector_broken,
                failure_message="Element not found: #checkout"
            ))
            db.commit()
            return test_id
        finally:
            db.close()

    def test_heal_lifecycle(self):
        """Propose → approve → execute heals a test and verifies it passes."""
        test_id = self._seed_failed_test()

        # Propose (AI Brain integration)
        heal = healing_service.create_heal_attempt(
            test_case_id=test_id,
            failure_type=FailureType.selector_broken,
            original_steps='[{"action": "Click checkout", "selector": "#checkout"}]',
            failure_message="Element not found: #checkout"
        )
        assert heal.proposed_steps
        assert heal.llm_rationale

        # Approve
        approve_resp = healing_service.approve_heal(heal.id)
        assert approve_resp["success"] is True

        # Execute (Executor integration; mock executor always passes healed tests)
        exec_resp = healing_service.execute_heal(heal.id)
        assert exec_resp["success"] is True
        assert exec_resp["outcome"] == "passed"
        assert exec_resp["heal_status"] == "verified"

        # Verify persisted state
        db = SessionLocal()
        try:
            stored_heal = db.query(HealAttempt).filter(HealAttempt.id == heal.id).first()
            assert stored_heal.verified_at is not None

            # Healed result is linked to the heal attempt
            heal_result = db.query(TestResult).filter(
                TestResult.heal_attempt_id == heal.id
            ).first()
            assert heal_result is not None
            assert heal_result.outcome == TestOutcome.passed

            # Heal history is queryable
            history = healing_service.get_heal_attempts(test_id)
            assert len(history) == 1
            assert history[0]["status"] == "verified"
        finally:
            db.close()


class TestAIBrainCachingIntegration:
    def test_generate_tests_cache_hit(self):
        """Identical generation requests are served from cache."""
        args = dict(
            pr_title="Cache test PR",
            pr_body="Testing response caching",
            diff="+ added line",
            changed_files=["src/cache.py"]
        )
        first = ai_service.generate_tests(**args)
        second = ai_service.generate_tests(**args)
        assert len(first.tests) > 0
        # Cache returns the same response object
        assert second is first

    def test_cache_miss_on_different_input(self):
        """Different inputs produce independent cache entries."""
        base = dict(pr_body="b", diff="d", changed_files=["f.py"])
        first = ai_service.generate_tests(pr_title="Cache A", **base)
        second = ai_service.generate_tests(pr_title="Cache B", **base)
        assert second is not first


class TestGitHubPagination:
    def test_next_page_url_parsing(self):
        """Link header rel=next extraction works."""
        link = '<https://api.github.com/repo/files?page=2>; rel="next", <https://api.github.com/repo/files?page=5>; rel="last"'
        assert github_service._next_page_url(link) == "https://api.github.com/repo/files?page=2"
        assert github_service._next_page_url('<https://x>; rel="last"') is None
        assert github_service._next_page_url(None) is None
