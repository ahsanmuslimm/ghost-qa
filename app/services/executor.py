import json
import random
import logging
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models import TestCase, TestResult, TestOutcome, FailureType
from app.database import SessionLocal
from app.schemas.test_schemas import TestResultSchema

logger = logging.getLogger(__name__)


class MockExecutor:
    """Mock executor for demo mode when UiPath is not available."""

    def execute_test(self, test_case: TestCase) -> TestResult:
        steps = json.loads(test_case.steps) if test_case.steps else []
        duration = random.randint(500, 5000)

        # Healed tests should pass after the fix
        if getattr(test_case, 'generated_by', '') == 'heal':
            return TestResult(
                id=str(uuid.uuid4()),
                test_case_id=test_case.id,
                outcome=TestOutcome.passed,
                duration_ms=duration,
                executed_at=datetime.utcnow()
            )

        # Simulate realistic failure patterns based on test type and priority
        fail_probability = 0.3
        if test_case.priority.value in ("p0_critical", "p1_high"):
            fail_probability = 0.4
        if "security" in (test_case.test_type.value or ""):
            fail_probability = 0.5

        if random.random() < fail_probability:
            # Determine failure type
            failure_types = [FailureType.selector_broken, FailureType.assertion_failed, FailureType.timeout]
            weights = [0.4, 0.4, 0.2]
            failure_type = random.choices(failure_types, weights=weights, k=1)[0]

            failure_messages = {
                FailureType.selector_broken: "Element not found: selector could not be located on the page",
                FailureType.assertion_failed: "Expected result did not match actual result",
                FailureType.timeout: "Operation timed out after 30 seconds",
                FailureType.api_contract: "API response did not match expected schema",
                FailureType.unknown: "Unknown test failure occurred"
            }

            failure_steps = {
                FailureType.selector_broken: "step_3" if len(steps) > 3 else "step_1",
                FailureType.assertion_failed: steps[-1].get("action", "last_step") if steps else "final_step",
                FailureType.timeout: "step_2" if len(steps) > 2 else "step_1",
                FailureType.api_contract: "step_1" if len(steps) > 1 else "step_1",
                FailureType.unknown: "unknown"
            }

            return TestResult(
                id=str(uuid.uuid4()),
                test_case_id=test_case.id,
                outcome=TestOutcome.failed,
                failure_step=failure_steps.get(failure_type, "unknown"),
                failure_message=failure_messages.get(failure_type, "Test failed"),
                failure_type=failure_type,
                duration_ms=duration,
                executed_at=datetime.utcnow()
            )
        else:
            return TestResult(
                id=str(uuid.uuid4()),
                test_case_id=test_case.id,
                outcome=TestOutcome.passed,
                duration_ms=duration,
                executed_at=datetime.utcnow()
            )

    def execute_batch(self, test_cases: List[TestCase]) -> List[TestResult]:
        results = []
        for test_case in test_cases:
            time.sleep(0.1)  # Simulate execution time
            result = self.execute_test(test_case)
            results.append(result)
        return results


class UiPathExecutor:
    """Real UiPath executor for production."""

    def __init__(self):
        self.client_id = settings.UIPATH_CLIENT_ID
        self.client_secret = settings.UIPATH_CLIENT_SECRET
        self.tenant_name = settings.UIPATH_TENANT_NAME
        self.org_id = settings.UIPATH_ORG_ID
        self.environment_id = settings.UIPATH_ENVIRONMENT_ID
        self.test_folder = settings.UIPATH_TEST_FOLDER
        self.demo_mode = settings.DEMO_MODE
        self.base_url = f"https://cloud.uipath.com/{self.org_id}/{self.tenant_name}"
        self.access_token = None

    def _get_access_token(self) -> str:
        if self.demo_mode or not self.client_id:
            return "mock-token"
        # In production: obtain OAuth token from UiPath
        return self.access_token or "mock-token"

    def execute_test(self, test_case: TestCase) -> TestResult:
        if self.demo_mode:
            mock = MockExecutor()
            return mock.execute_test(test_case)

        # Production UiPath execution
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # 1. Create/upload test
        # 2. Create test set
        # 3. Start execution
        # 4. Poll for results
        # 5. Return TestResult

        # Placeholder for real implementation
        logger.warning("Real UiPath execution not fully implemented")
        mock = MockExecutor()
        return mock.execute_test(test_case)

    def execute_batch(self, test_cases: List[TestCase]) -> List[TestResult]:
        results = []
        for test_case in test_cases:
            result = self.execute_test(test_case)
            results.append(result)
        return results


class ExecutorService:
    def __init__(self):
        self.mock_executor = MockExecutor()
        self.uipath_executor = UiPathExecutor()
        self.demo_mode = settings.DEMO_MODE

    def execute_tests(self, test_cases: List[TestCase]) -> List[TestResult]:
        executor = self.mock_executor if self.demo_mode else self.uipath_executor
        return executor.execute_batch(test_cases)

    def store_results(self, results: List[TestResult]) -> None:
        db = SessionLocal()
        try:
            for result in results:
                stored = TestResult(
                    id=result.id,
                    test_case_id=result.test_case_id,
                    outcome=result.outcome,
                    failure_step=result.failure_step,
                    failure_message=result.failure_message,
                    failure_type=result.failure_type,
                    screenshot_url=result.screenshot_url,
                    duration_ms=result.duration_ms,
                    robot_id=result.robot_id,
                    executed_at=result.executed_at
                )
                db.add(stored)
                test_case = db.query(TestCase).filter(TestCase.id == result.test_case_id).first()
                if test_case:
                    test_case.outcome = result.outcome
                    test_case.failure_step = result.failure_step
                    test_case.failure_message = result.failure_message
                    test_case.failure_type = result.failure_type
                    test_case.duration_ms = result.duration_ms
                    test_case.executed_at = result.executed_at
            db.commit()
        finally:
            db.close()
