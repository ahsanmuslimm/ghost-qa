import pytest
import uuid
import app.database as db_module
from app.services.healing import HealingService
from app.models import (
    TestCase, TestResult, HealAttempt, PipelineRun,
    FailureType, HealStatus, TestOutcome, TestPriority,
    TestType, RiskLevel, ApprovalStatus, TestCaseStatus,
    Organisation, Repository
)


def _setup_test(db, failure_type=FailureType.selector_broken):
    org = Organisation(id=str(uuid.uuid4()), name="test-org")
    db.add(org); db.commit()
    repo = Repository(id=str(uuid.uuid4()), organisation_id=org.id, full_name="test/test")
    db.add(repo); db.commit()
    pipeline = PipelineRun(id=str(uuid.uuid4()), repository_id=repo.id, github_pr_number=1, commit_sha="abc")
    db.add(pipeline); db.commit()

    tc = TestCase(
        id="TC-001", pipeline_run_id=pipeline.id,
        title="Login test", steps='[{"action": "click", "selector": "#checkout", "value": "", "assertion": ""}]',
        test_type=TestType.functional, priority=TestPriority.p1_high,
        approval_status=ApprovalStatus.approved,
        status=TestCaseStatus.approved,
        generated_by="test"
    )
    db.add(tc); db.commit()
    return pipeline, tc


class _TestSessionWrapper:
    """Wrapper that delegates to a test session but ignores close()."""
    def __init__(self, session):
        self._session = session

    def __getattr__(self, name):
        return getattr(self._session, name)

    def close(self):
        pass


class TestSelfHealing:
    """Test the self-healing service."""

    def test_create_heal_attempt_selector_failure(self, test_db):
        """Heal attempt should be created for selector failures."""
        pipeline, tc = _setup_test(test_db, FailureType.selector_broken)

        original_h = db_module.SessionLocal
        db_module.SessionLocal = lambda: _TestSessionWrapper(test_db)

        service = HealingService()
        heal = service.create_heal_attempt(
            test_case_id="TC-001",
            failure_type=FailureType.selector_broken,
            original_steps="Click #checkout button",
            failure_message="Element not found"
        )
        assert heal is not None
        assert heal.status == HealStatus.proposed
        assert heal.failure_type == FailureType.selector_broken
        assert len(heal.proposed_steps) > 0
        assert len(heal.llm_rationale) > 0

        db_module.SessionLocal = original_h

    def test_create_heal_attempt_api_contract_failure(self, test_db):
        """Heal attempt should be created for API contract failures."""
        pipeline, tc = _setup_test(test_db, FailureType.api_contract)

        original_h = db_module.SessionLocal
        db_module.SessionLocal = lambda: _TestSessionWrapper(test_db)

        service = HealingService()
        heal = service.create_heal_attempt(
            test_case_id="TC-001",
            failure_type=FailureType.api_contract,
            original_steps="Call /api/users",
            failure_message="Response schema mismatch"
        )
        assert heal is not None
        assert heal.status == HealStatus.proposed

        db_module.SessionLocal = original_h

    def test_approve_heal(self, test_db):
        """Heal approval should work."""
        pipeline, tc = _setup_test(test_db)

        original_h = db_module.SessionLocal
        db_module.SessionLocal = lambda: _TestSessionWrapper(test_db)

        service = HealingService()
        heal = service.create_heal_attempt(
            test_case_id="TC-001",
            failure_type=FailureType.selector_broken,
            original_steps="Old steps",
            failure_message="Not found"
        )

        result = service.approve_heal(heal.id)
        assert result["success"] is True
        assert result["status"] == "accepted"

        heals = service.get_heal_attempts("TC-001")
        assert heals[0]["status"] == "accepted"

        db_module.SessionLocal = original_h

    def test_reject_heal(self, test_db):
        """Heal rejection should work."""
        pipeline, tc = _setup_test(test_db)

        original_h = db_module.SessionLocal
        db_module.SessionLocal = lambda: _TestSessionWrapper(test_db)

        service = HealingService()
        heal = service.create_heal_attempt(
            test_case_id="TC-001",
            failure_type=FailureType.selector_broken,
            original_steps="Old steps",
            failure_message="Not found"
        )

        result = service.reject_heal(heal.id)
        assert result["success"] is True
        assert result["status"] == "rejected"

        db_module.SessionLocal = original_h

    def test_verified_heal(self, test_db):
        """Approved heal should be executed and marked as verified."""
        pipeline, tc = _setup_test(test_db)

        original_h = db_module.SessionLocal
        db_module.SessionLocal = lambda: _TestSessionWrapper(test_db)

        service = HealingService()
        heal = service.create_heal_attempt(
            test_case_id="TC-001",
            failure_type=FailureType.selector_broken,
            original_steps="Old steps",
            failure_message="Not found"
        )

        service.approve_heal(heal.id)
        result = service.execute_heal(heal.id)
        assert result["success"] is True
        assert result["outcome"] == "passed"
        assert result["heal_status"] == "verified"

        db_module.SessionLocal = original_h
