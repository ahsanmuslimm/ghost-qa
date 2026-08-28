"""
Phase 3 (Task 3.4): End-to-end tests over the HTTP API.

Flow A: GitHub webhook → full pipeline → run/tests/results/report queries.
Flow B: heal proposal → approve → execute, including authorisation checks.
"""
import json
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.services import github_service, healing_service
from app.services.auth import AuthService
from app.models import (
    PipelineRun, PipelineStatus, TestCase, TestCaseStatus, TestResult,
    TestOutcome, TestType, TestPriority, ApprovalStatus, FailureType,
    HealAttempt, Organisation, Repository
)

pytestmark = pytest.mark.e2e


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


def _headers(role: str):
    service = AuthService()
    email = f"{role}@ghost.qa"
    token = service.create_token(email, role)["token"]
    return {"Authorization": f"Bearer {token}"}


def _payload(pr_number: int, sha_suffix: str = ""):
    return {
        "action": "opened",
        "repository": {
            "id": 555000111,
            "name": "e2e-app",
            "full_name": "e2e-org/e2e-app",
            "owner": {"login": "e2e-org"},
            "default_branch": "main"
        },
        "pull_request": {
            "number": pr_number,
            "title": "E2E PR",
            "body": "End to end test",
            "state": "open",
            "diff_url": f"https://github.com/e2e-org/e2e-app/pull/{pr_number}.diff",
            "html_url": f"https://github.com/e2e-org/e2e-app/pull/{pr_number}",
            "user": {"login": "e2e-user"},
            "head": {"ref": "feature/e2e", "sha": f"e2e-{pr_number}{sha_suffix}"},
            "base": {"ref": "main", "sha": "e2ebase"},
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z"
        }
    }


class TestPipelineE2E:
    """Webhook in → completed pipeline queryable through every read API."""

    def test_webhook_to_completed_pipeline(self, client):
        response = client.post(
            "/api/webhooks/github",
            json=_payload(8001),
            headers={"X-GitHub-Event": "pull_request"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "pipeline_started"
        run_id = body["pipeline_run_id"]

        auth = _headers("approver")

        # Run detail
        run = client.get(f"/api/runs/{run_id}", headers=auth)
        assert run.status_code == 200
        assert run.json()["status"] == "completed"
        assert run.json()["repository"] == "e2e-org/e2e-app"

        # Generated + executed tests
        tests = client.get(f"/api/runs/{run_id}/tests", headers=auth)
        assert tests.status_code == 200
        test_list = tests.json()
        assert len(test_list) == 5
        assert all(t["approval_status"] == "approved" for t in test_list)
        assert all(t["outcome"] in ("passed", "failed") for t in test_list)

        # Execution results
        results = client.get(f"/api/runs/{run_id}/results", headers=auth)
        assert results.status_code == 200
        assert len(results.json()) == 5

        # Risk report
        report = client.get(f"/api/runs/{run_id}/report", headers=auth)
        assert report.status_code == 200
        assert report.json()["risk_level"] in (
            "low", "medium", "high", "critical"
        )

    def test_run_appears_in_list(self, client):
        response = client.post(
            "/api/webhooks/github",
            json=_payload(8002),
            headers={"X-GitHub-Event": "pull_request"}
        )
        run_id = response.json()["pipeline_run_id"]

        listing = client.get("/api/runs", headers=_headers("viewer"))
        assert listing.status_code == 200
        run_ids = [r["id"] for r in listing.json()["runs"]]
        assert run_id in run_ids

    def test_duplicate_webhook_ignored(self, client):
        first = client.post(
            "/api/webhooks/github",
            json=_payload(8003),
            headers={"X-GitHub-Event": "pull_request"}
        )
        assert first.json()["status"] == "pipeline_started"

        second = client.post(
            "/api/webhooks/github",
            json=_payload(8003),
            headers={"X-GitHub-Event": "pull_request"}
        )
        assert second.status_code == 200
        assert second.json()["status"] == "duplicate_ignored"
        assert second.json()["pipeline_run_id"] == first.json()["pipeline_run_id"]


class TestHealWorkflowE2E:
    """Heal lifecycle driven through the /api/heals endpoints."""

    def _seed_failed_test(self, pr_number: int):
        db = SessionLocal()
        try:
            org = Organisation(id=str(uuid.uuid4()), name="e2e-heal-org")
            db.add(org)
            db.commit()
            repo = Repository(
                id=str(uuid.uuid4()), organisation_id=org.id,
                full_name="e2e-heal-org/e2e-heal-app"
            )
            db.add(repo)
            db.commit()

            run_id = str(uuid.uuid4())
            db.add(PipelineRun(
                id=run_id, repository_id=repo.id, trigger_type="github_pr",
                github_pr_number=pr_number, commit_sha=f"e2e-heal-{pr_number}",
                status=PipelineStatus.completed
            ))
            test_id = f"{run_id[:8]}-TC-E2E"
            db.add(TestCase(
                id=test_id,
                pipeline_run_id=run_id,
                title="E2E checkout flow",
                test_type=TestType.functional,
                priority=TestPriority.p1_high,
                steps=json.dumps([
                    {"action": "Click checkout", "selector": "#checkout",
                     "value": "", "assertion": ""}
                ]),
                expected_result="Order placed",
                approval_status=ApprovalStatus.approved,
                status=TestCaseStatus.failed,
                outcome=TestOutcome.failed,
                failure_type=FailureType.selector_broken,
                failure_message="Element not found: #checkout"
            ))
            db.commit()
            return run_id, test_id
        finally:
            db.close()

    def _propose_heal(self, test_id: str) -> str:
        heal = healing_service.create_heal_attempt(
            test_case_id=test_id,
            failure_type=FailureType.selector_broken,
            original_steps='[{"action": "Click checkout", "selector": "#checkout"}]',
            failure_message="Element not found: #checkout"
        )
        return heal.id

    def test_heal_approve_and_execute_via_api(self, client):
        run_id, test_id = self._seed_failed_test(8101)
        heal_id = self._propose_heal(test_id)
        approver = _headers("approver")

        # Approve
        approve = client.post(f"/api/heals/{heal_id}/approve", headers=approver)
        assert approve.status_code == 200
        assert approve.json()["success"] is True

        # Execute (mock executor passes healed tests in demo mode)
        execute = client.post(f"/api/heals/{heal_id}/execute", headers=approver)
        assert execute.status_code == 200
        body = execute.json()
        assert body["success"] is True
        assert body["outcome"] == "passed"

        # Persisted state: heal verified, healed result linked, test healed
        db = SessionLocal()
        try:
            heal = db.query(HealAttempt).filter(HealAttempt.id == heal_id).first()
            assert heal.verified_at is not None

            healed_result = db.query(TestResult).filter(
                TestResult.heal_attempt_id == heal_id
            ).first()
            assert healed_result is not None
            assert healed_result.outcome == TestOutcome.passed
        finally:
            db.close()

        # The healed clone executed and passed; the original keeps its
        # failure history. Both are visible through the read API.
        tests = client.get(f"/api/runs/{run_id}/tests", headers=approver)
        test_list = tests.json()
        original = [t for t in test_list if t["id"] == test_id][0]
        assert original["outcome"] == "failed"
        healed = [t for t in test_list if t["id"].startswith(f"{test_id}-healed-")]
        assert len(healed) == 1
        assert healed[0]["outcome"] == "passed"

    def test_heal_reject_via_api(self, client):
        _, test_id = self._seed_failed_test(8102)
        heal_id = self._propose_heal(test_id)
        approver = _headers("approver")

        reject = client.post(f"/api/heals/{heal_id}/reject", headers=approver)
        assert reject.status_code == 200
        assert reject.json()["success"] is True

        # A rejected heal cannot be approved afterwards
        approve = client.post(f"/api/heals/{heal_id}/approve", headers=approver)
        assert approve.status_code == 400

    def test_heal_endpoints_require_approver(self, client):
        _, test_id = self._seed_failed_test(8103)
        heal_id = self._propose_heal(test_id)

        # No JWT at all
        anon = client.post(f"/api/heals/{heal_id}/approve")
        assert anon.status_code == 401

        # Viewer role is not enough
        viewer = client.post(
            f"/api/heals/{heal_id}/approve", headers=_headers("viewer")
        )
        assert viewer.status_code == 403

        # Approver works
        approver = client.post(
            f"/api/heals/{heal_id}/approve", headers=_headers("approver")
        )
        assert approver.status_code == 200
