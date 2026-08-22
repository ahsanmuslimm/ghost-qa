import pytest
import uuid
from app.services.risk import RiskEngine
from app.models import (
    TestCase, TestResult, PipelineRun, PipelineStatus, TestOutcome,
    RiskLevel, TestPriority, TestType, FailureType, ApprovalStatus, TestCaseStatus
)
from app.schemas.test_schemas import TestDebtFinding


def _create_test_case(db, pipeline_id, test_id, title, priority, risk_level, outcome=None, failure_type=None):
    tc = TestCase(
        id=test_id,
        pipeline_run_id=pipeline_id,
        title=title,
        test_type=TestType.functional,
        priority=priority,
        steps='[]',
        expected_result="Result",
        risk_level=risk_level,
        risk_rationale="Test",
        approval_status=ApprovalStatus.approved,
        status=TestCaseStatus.passed,
        outcome=outcome,
        failure_type=failure_type
    )
    db.add(tc)
    db.commit()

    if outcome:
        result = TestResult(
            id=str(uuid.uuid4()),
            test_case_id=tc.id,
            outcome=outcome,
            failure_type=failure_type,
            duration_ms=1000
        )
        db.add(result)
        db.commit()
    return tc


class TestRiskEngine:
    """Test the risk calculation engine."""

    def test_all_pass_low_risk(self, test_db, org_repo_pipeline):
        """All tests passing should result in low/LOW risk."""
        pipeline = org_repo_pipeline["pipeline"]
        for i in range(3):
            _create_test_case(
                test_db, pipeline.id, f"TC-{i+1}", f"Test {i}",
                TestPriority.p1_high, RiskLevel.high,
                TestOutcome.passed
            )

        tests = test_db.query(TestCase).filter(TestCase.pipeline_run_id == pipeline.id).all()
        results = test_db.query(TestResult).filter(TestResult.test_case_id.in_([t.id for t in tests])).all()

        engine = RiskEngine()
        report = engine.calculate_risk(pipeline.id, results, tests)
        assert report.risk_level == RiskLevel.low
        assert report.recommendation == "MERGE"
        assert report.failed == 0
        assert report.passed == 3

    def test_p1_failure_high_risk(self, test_db, org_repo_pipeline):
        """P1 test failure should result in HIGH risk."""
        pipeline = org_repo_pipeline["pipeline"]
        _create_test_case(
            test_db, pipeline.id, "TC-001", "Test 1",
            TestPriority.p1_high, RiskLevel.high,
            TestOutcome.failed, FailureType.assertion_failed
        )

        tests = test_db.query(TestCase).filter(TestCase.pipeline_run_id == pipeline.id).all()
        results = test_db.query(TestResult).filter(TestResult.test_case_id.in_([t.id for t in tests])).all()

        engine = RiskEngine()
        report = engine.calculate_risk(pipeline.id, results, tests)
        assert report.risk_level == RiskLevel.high
        assert report.recommendation == "DO NOT MERGE"
        assert report.failed == 1

    def test_p0_failure_critical_risk(self, test_db, org_repo_pipeline):
        """P0 test failure should result in CRITICAL risk."""
        pipeline = org_repo_pipeline["pipeline"]
        _create_test_case(
            test_db, pipeline.id, "TC-001", "Security test",
            TestPriority.p0_critical, RiskLevel.critical,
            TestOutcome.failed, FailureType.selector_broken
        )

        tests = test_db.query(TestCase).filter(TestCase.pipeline_run_id == pipeline.id).all()
        results = test_db.query(TestResult).filter(TestResult.test_case_id.in_([t.id for t in tests])).all()

        engine = RiskEngine()
        report = engine.calculate_risk(pipeline.id, results, tests)
        assert report.risk_level == RiskLevel.critical
        assert "Security test" in report.critical_failures

    def test_mixed_results_medium_risk(self, test_db, org_repo_pipeline):
        """Mixed results with only P2 failures should be medium risk."""
        pipeline = org_repo_pipeline["pipeline"]
        _create_test_case(
            test_db, pipeline.id, "TC-001", "Test 1",
            TestPriority.p1_high, RiskLevel.high,
            TestOutcome.passed
        )
        _create_test_case(
            test_db, pipeline.id, "TC-002", "Test 2",
            TestPriority.p2_medium, RiskLevel.medium,
            TestOutcome.failed, FailureType.timeout
        )

        tests = test_db.query(TestCase).filter(TestCase.pipeline_run_id == pipeline.id).all()
        results = test_db.query(TestResult).filter(TestResult.test_case_id.in_([t.id for t in tests])).all()

        engine = RiskEngine()
        report = engine.calculate_risk(pipeline.id, results, tests)
        assert report.risk_level == RiskLevel.medium
        assert report.passed == 1
        assert report.failed == 1

    def test_risk_deterministic(self, test_db, org_repo_pipeline):
        """Risk calculation should be deterministic."""
        pipeline = org_repo_pipeline["pipeline"]
        _create_test_case(
            test_db, pipeline.id, "TC-001", "Test",
            TestPriority.p0_critical, RiskLevel.critical,
            TestOutcome.failed, FailureType.assertion_failed
        )

        tests = test_db.query(TestCase).filter(TestCase.pipeline_run_id == pipeline.id).all()
        results = test_db.query(TestResult).filter(TestResult.test_case_id.in_([t.id for t in tests])).all()

        engine = RiskEngine()
        report1 = engine.calculate_risk(pipeline.id, results, tests)
        report2 = engine.calculate_risk(pipeline.id, results, tests)

        assert report1.risk_level == report2.risk_level
        assert report1.recommendation == report2.recommendation
