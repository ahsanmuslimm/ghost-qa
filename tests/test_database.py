import pytest
import uuid
from app.models import (
    Organisation, Repository, PipelineRun, TestCase, TestResult, HealAttempt,
    PipelineStatus, RiskLevel, TestType, TestPriority, ApprovalStatus,
    TestOutcome, FailureType, HealStatus
)


class TestDatabaseModels:
    """Test database model creation, relationships, and constraints."""

    def test_organisation_creation(self, test_db):
        """Organisation should be created with correct fields."""
        org = Organisation(
            id=str(uuid.uuid4()), name="Test Org", github_org_id="12345"
        )
        test_db.add(org)
        test_db.commit()
        assert org.id is not None
        assert org.name == "Test Org"
        assert org.github_org_id == "12345"
        assert org.plan.value == "free"
        assert org.created_at is not None

    def test_repository_creation(self, test_db):
        """Repository should be created with correct fields."""
        org = Organisation(id=str(uuid.uuid4()), name="Test Org")
        test_db.add(org)
        test_db.commit()

        repo = Repository(
            id=str(uuid.uuid4()),
            organisation_id=org.id,
            github_repo_id="67890",
            full_name="test-org/test-repo",
            default_branch="main"
        )
        test_db.add(repo)
        test_db.commit()
        assert repo.id is not None
        assert repo.organisation_id == org.id
        assert repo.full_name == "test-org/test-repo"
        assert repo.is_active is True

    def test_pipeline_run_creation(self, test_db, org_repo_pipeline):
        """PipelineRun should be created with correct fields."""
        pipeline = org_repo_pipeline["pipeline"]
        assert pipeline.id is not None
        assert pipeline.github_pr_number == 42
        assert pipeline.commit_sha == "abc123"
        assert pipeline.status == PipelineStatus.queued
        assert pipeline.created_at is not None

    def test_test_case_creation(self, test_db, org_repo_pipeline):
        """TestCase should be created with correct fields."""
        pipeline = org_repo_pipeline["pipeline"]
        tc = TestCase(
            id="TC-001",
            pipeline_run_id=pipeline.id,
            title="Test login",
            test_type=TestType.functional,
            priority=TestPriority.p0_critical,
            steps='[{"action": "login", "selector": "", "value": "", "assertion": ""}]',
            expected_result="Login succeeds",
            risk_level=RiskLevel.high,
            risk_rationale="Auth is critical",
            generated_by="claude",
            approval_status=ApprovalStatus.pending
        )
        test_db.add(tc)
        test_db.commit()
        assert tc.id == "TC-001"
        assert tc.pipeline_run_id == pipeline.id
        assert tc.approval_status == ApprovalStatus.pending

    def test_test_result_creation(self, test_db, org_repo_pipeline):
        """TestResult should be created with correct fields."""
        pipeline = org_repo_pipeline["pipeline"]
        tc = TestCase(
            id="TC-001",
            pipeline_run_id=pipeline.id,
            title="Test",
            steps='[]',
            approval_status=ApprovalStatus.approved
        )
        test_db.add(tc)
        test_db.commit()

        result = TestResult(
            id=str(uuid.uuid4()),
            test_case_id=tc.id,
            outcome=TestOutcome.passed,
            duration_ms=1500
        )
        test_db.add(result)
        test_db.commit()
        assert result.test_case_id == tc.id
        assert result.outcome == TestOutcome.passed

    def test_heal_attempt_creation(self, test_db, org_repo_pipeline):
        """HealAttempt should be created with correct fields."""
        pipeline = org_repo_pipeline["pipeline"]
        tc = TestCase(
            id="TC-001",
            pipeline_run_id=pipeline.id,
            title="Test",
            steps='[]',
            approval_status=ApprovalStatus.approved
        )
        test_db.add(tc)
        test_db.commit()

        heal = HealAttempt(
            id=str(uuid.uuid4()),
            test_case_id=tc.id,
            failure_type=FailureType.selector_broken,
            original_steps="Original steps",
            proposed_steps="Healed steps",
            llm_rationale="Element was renamed",
            status=HealStatus.proposed
        )
        test_db.add(heal)
        test_db.commit()
        assert heal.test_case_id == tc.id
        assert heal.status == HealStatus.proposed

    def test_relationships(self, test_db, org_repo_pipeline):
        """Models should have proper relationships."""
        pipeline = org_repo_pipeline["pipeline"]
        repo = org_repo_pipeline["repo"]

        tc = TestCase(
            id="TC-001",
            pipeline_run_id=pipeline.id,
            title="Test",
            steps='[]',
        )
        test_db.add(tc)
        test_db.commit()

        result = TestResult(
            id=str(uuid.uuid4()),
            test_case_id=tc.id,
            outcome=TestOutcome.passed
        )
        test_db.add(result)
        test_db.commit()

        assert tc in pipeline.test_cases
        assert result in tc.test_results
        assert pipeline.repository.full_name == repo.full_name
