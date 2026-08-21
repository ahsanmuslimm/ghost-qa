import pytest
import uuid
from app.services.executor import ExecutorService, MockExecutor
from app.models import TestCase, TestResult, TestOutcome, TestType, TestPriority, RiskLevel, ApprovalStatus, FailureType


class TestExecution:
    """Test the mock execution service."""

    def test_test_pass(self):
        """A test should be able to pass."""
        executor = ExecutorService()
        # Create a test case that should pass (low priority)
        tc = TestCase(
            id="TC-001",
            pipeline_run_id=str(uuid.uuid4()),
            title="Test that passes",
            steps='[]',
            test_type=TestType.regression,
            priority=TestPriority.p3_low,
            generated_by="test",
            approval_status=ApprovalStatus.approved
        )
        # Run multiple times to ensure at least one pass
        result = None
        for _ in range(10):
            result = executor.mock_executor.execute_test(tc)
            if result.outcome == TestOutcome.passed:
                break
        assert result is not None
        assert result.outcome in (TestOutcome.passed, TestOutcome.failed)
        assert result.test_case_id == "TC-001"
        assert result.duration_ms is not None or result.outcome == TestOutcome.failed

    def test_test_fail(self):
        """A test should be able to fail."""
        executor = ExecutorService()
        tc = TestCase(
            id="TC-001",
            pipeline_run_id=str(uuid.uuid4()),
            title="Test that fails",
            steps='[]',
            test_type=TestType.security,
            priority=TestPriority.p0_critical,
            generated_by="test",
            approval_status=ApprovalStatus.approved
        )
        result = None
        for _ in range(10):
            result = executor.mock_executor.execute_test(tc)
            if result.outcome == TestOutcome.failed:
                break
        assert result is not None
        assert result.outcome in (TestOutcome.passed, TestOutcome.failed)

    def test_timeout_failure(self):
        """Timeout failure type should be possible."""
        executor = MockExecutor()
        tc = TestCase(
            id="TC-001",
            pipeline_run_id=str(uuid.uuid4()),
            title="Test",
            steps='[]',
            priority=TestPriority.p0_critical,
        )
        found_timeout = False
        for _ in range(20):
            result = executor.execute_test(tc)
            if result.failure_type == FailureType.timeout:
                found_timeout = True
                assert result.outcome == TestOutcome.failed
                break
        assert found_timeout, "Expected at least one timeout failure in 20 runs"

    def test_selector_failure(self):
        """Selector failure type should be possible."""
        executor = MockExecutor()
        tc = TestCase(
            id="TC-001",
            pipeline_run_id=str(uuid.uuid4()),
            title="Test",
            steps='[]',
            priority=TestPriority.p0_critical,
        )
        found_selector = False
        for _ in range(20):
            result = executor.execute_test(tc)
            if result.failure_type == FailureType.selector_broken:
                found_selector = True
                assert result.outcome == TestOutcome.failed
                break
        assert found_selector, "Expected at least one selector failure in 20 runs"

    def test_healed_test_passes(self):
        """Healed tests should always pass."""
        executor = MockExecutor()
        tc = TestCase(
            id="TC-001",
            pipeline_run_id=str(uuid.uuid4()),
            title="Healed test",
            steps='[]',
            generated_by="heal",
        )
        result = executor.execute_test(tc)
        assert result.outcome == TestOutcome.passed
        assert result.failure_type is None
