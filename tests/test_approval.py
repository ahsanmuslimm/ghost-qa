import pytest
import uuid
import app.database as db_module
from app.services.approval import ApprovalService
from app.models import (
    TestCase, ApprovalStatus, TestCaseStatus, PipelineRun, PipelineStatus,
    Organisation, Repository
)


class _TestSessionWrapper:
    """Wrapper that delegates to a test session but ignores close()."""
    def __init__(self, session):
        self._session = session

    def __getattr__(self, name):
        return getattr(self._session, name)

    def close(self):
        pass  # Don't close the test session


class TestApproval:
    """Test the human approval service."""

    def test_approve_test(self, test_db):
        """Single test approval should work."""
        service = ApprovalService()
        org = Organisation(id=str(uuid.uuid4()), name="test-org")
        test_db.add(org); test_db.commit()
        repo = Repository(id=str(uuid.uuid4()), organisation_id=org.id, full_name="test/test")
        test_db.add(repo); test_db.commit()
        pipeline = PipelineRun(id=str(uuid.uuid4()), repository_id=repo.id, github_pr_number=1, commit_sha="abc")
        test_db.add(pipeline); test_db.commit()

        tc = TestCase(
            id="TC-001", pipeline_run_id=pipeline.id,
            title="Test", steps='[]', approval_status=ApprovalStatus.pending,
            status=TestCaseStatus.pending
        )
        test_db.add(tc); test_db.commit()

        original = db_module.SessionLocal
        db_module.SessionLocal = lambda: _TestSessionWrapper(test_db)

        result = service.approve_test("TC-001")
        assert result["success"] is True
        assert result["status"] == "approved"

        tc = test_db.query(TestCase).filter(TestCase.id == "TC-001").first()
        assert tc.approval_status == ApprovalStatus.approved
        assert tc.status == TestCaseStatus.approved
        assert tc.approved_by is not None
        assert tc.approved_at is not None

        db_module.SessionLocal = original

    def test_reject_test(self, test_db):
        """Test rejection should work."""
        service = ApprovalService()
        org = Organisation(id=str(uuid.uuid4()), name="test-org")
        test_db.add(org); test_db.commit()
        repo = Repository(id=str(uuid.uuid4()), organisation_id=org.id, full_name="test/test")
        test_db.add(repo); test_db.commit()
        pipeline = PipelineRun(id=str(uuid.uuid4()), repository_id=repo.id, github_pr_number=1, commit_sha="abc")
        test_db.add(pipeline); test_db.commit()

        tc = TestCase(
            id="TC-001", pipeline_run_id=pipeline.id,
            title="Test", steps='[]', approval_status=ApprovalStatus.pending,
            status=TestCaseStatus.pending
        )
        test_db.add(tc); test_db.commit()

        original = db_module.SessionLocal
        db_module.SessionLocal = lambda: _TestSessionWrapper(test_db)

        result = service.reject_test("TC-001", "Bad test")
        assert result["success"] is True
        assert result["status"] == "rejected"

        tc = test_db.query(TestCase).filter(TestCase.id == "TC-001").first()
        assert tc.approval_status == ApprovalStatus.rejected
        assert tc.status == TestCaseStatus.rejected

        db_module.SessionLocal = original

    def test_approve_all(self, test_db):
        """Approve all tests in a pipeline run."""
        service = ApprovalService()
        org = Organisation(id=str(uuid.uuid4()), name="test-org")
        test_db.add(org); test_db.commit()
        repo = Repository(id=str(uuid.uuid4()), organisation_id=org.id, full_name="test/test")
        test_db.add(repo); test_db.commit()
        pipeline = PipelineRun(id=str(uuid.uuid4()), repository_id=repo.id, github_pr_number=1, commit_sha="abc")
        test_db.add(pipeline); test_db.commit()

        for i in range(3):
            tc = TestCase(
                id=f"TC-{i+1}", pipeline_run_id=pipeline.id,
                title=f"Test {i}", steps='[]', approval_status=ApprovalStatus.pending,
                status=TestCaseStatus.pending
            )
            test_db.add(tc)
        test_db.commit()

        original = db_module.SessionLocal
        db_module.SessionLocal = lambda: _TestSessionWrapper(test_db)

        result = service.approve_all(pipeline.id)
        assert result["success"] is True
        assert result["approved_count"] == 3

        approved = test_db.query(TestCase).filter(
            TestCase.pipeline_run_id == pipeline.id,
            TestCase.approval_status == ApprovalStatus.approved
        ).count()
        assert approved == 3

        db_module.SessionLocal = original

    def test_partial_approval(self, test_db):
        """Only pending tests should be approved."""
        service = ApprovalService()
        org = Organisation(id=str(uuid.uuid4()), name="test-org")
        test_db.add(org); test_db.commit()
        repo = Repository(id=str(uuid.uuid4()), organisation_id=org.id, full_name="test/test")
        test_db.add(repo); test_db.commit()
        pipeline = PipelineRun(id=str(uuid.uuid4()), repository_id=repo.id, github_pr_number=1, commit_sha="abc")
        test_db.add(pipeline); test_db.commit()

        tc1 = TestCase(id="TC-001", pipeline_run_id=pipeline.id, title="Test1", steps='[]', approval_status=ApprovalStatus.pending, status=TestCaseStatus.pending)
        tc2 = TestCase(id="TC-002", pipeline_run_id=pipeline.id, title="Test2", steps='[]', approval_status=ApprovalStatus.rejected, status=TestCaseStatus.rejected)
        test_db.add(tc1); test_db.add(tc2); test_db.commit()

        original = db_module.SessionLocal
        db_module.SessionLocal = lambda: _TestSessionWrapper(test_db)

        result = service.approve_all(pipeline.id)
        assert result["approved_count"] == 1  # Only TC-001

        db_module.SessionLocal = original
