"""
Phase 3 (Task 3.2): Performance tests.

Thresholds are intentionally lenient so the suite also passes on slow CI
runners; they guard against order-of-magnitude regressions, not micro-tuning.
"""
import time
import uuid
import concurrent.futures
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.database import SessionLocal
from app.models import (
    PipelineRun, PipelineStatus, TestCase, TestCaseStatus,
    Organisation, Repository
)
from app.services import github_service

pytestmark = pytest.mark.performance


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
            "id": 123456789,
            "name": "perf-app",
            "full_name": "perf-org/perf-app",
            "owner": {"login": "perf-org"},
            "default_branch": "main"
        },
        "pull_request": {
            "number": pr_number,
            "title": "Perf PR",
            "body": "Performance test",
            "state": "open",
            "diff_url": f"https://github.com/perf-org/perf-app/pull/{pr_number}.diff",
            "html_url": f"https://github.com/perf-org/perf-app/pull/{pr_number}",
            "user": {"login": "perf-user"},
            "head": {"ref": "feature/perf", "sha": f"perf-{pr_number}"},
            "base": {"ref": "main", "sha": "perfbase"},
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z"
        }
    }


class TestEndpointLatency:
    def test_health_response_time(self, client):
        """Health endpoint responds fast (no DB/AI work)."""
        start = time.time()
        response = client.get("/")
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed < 1.0

    def test_webhook_response_time(self, client):
        """Webhook (incl. synchronous demo pipeline) stays under budget."""
        start = time.time()
        response = client.post(
            "/api/webhooks/github",
            json=_payload(9001),
            headers={"X-GitHub-Event": "pull_request"}
        )
        elapsed = time.time() - start
        assert response.status_code == 200
        assert response.json()["status"] == "pipeline_started"
        assert elapsed < 15.0


class TestConcurrency:
    def test_concurrent_webhooks(self, client):
        """Several simultaneous webhooks are all accepted."""
        def post(pr_number):
            return client.post(
                "/api/webhooks/github",
                json=_payload(pr_number),
                headers={"X-GitHub-Event": "pull_request"}
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(post, range(9101, 9106)))

        assert all(r.status_code == 200 for r in results)
        assert all(r.json()["status"] == "pipeline_started" for r in results)


class TestDatabasePerformance:
    def test_query_performance(self):
        """Filtering 100 completed runs stays well under 500ms."""
        db = SessionLocal()
        try:
            org = Organisation(id=str(uuid.uuid4()), name="perf-db-org")
            db.add(org)
            db.commit()
            repo = Repository(
                id=str(uuid.uuid4()), organisation_id=org.id,
                full_name="perf-db-org/perf-db-repo"
            )
            db.add(repo)
            db.commit()

            def _completed_ids():
                return {r.id for r in db.execute(
                    select(PipelineRun).where(PipelineRun.status == PipelineStatus.completed)
                ).scalars().all()}

            # Runs seeded by other tests persist in the shared SQLite file,
            # so measure against this repo's own seeded rows only.
            baseline_ids = _completed_ids()

            for i in range(100):
                run = PipelineRun(
                    id=str(uuid.uuid4()),
                    repository_id=repo.id,
                    trigger_type="github_pr",
                    github_pr_number=i,
                    commit_sha=f"perf-db-{i}",
                    status=PipelineStatus.completed
                )
                db.add(run)
                for j in range(5):
                    db.add(TestCase(
                        id=str(uuid.uuid4()),
                        pipeline_run_id=run.id,
                        title=f"Perf test {j}",
                        steps="[]",
                        status=TestCaseStatus.passed
                    ))
            db.commit()

            start = time.time()
            rows = db.execute(
                select(PipelineRun).where(PipelineRun.status == PipelineStatus.completed)
            ).scalars().all()
            elapsed = time.time() - start

            seeded = [r for r in rows if r.id not in baseline_ids]
            assert len(seeded) == 100
            assert elapsed < 0.5
        finally:
            db.close()
