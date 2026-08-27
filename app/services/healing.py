import json
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models import (
    HealAttempt, HealStatus, FailureType, TestCase, TestResult,
    TestOutcome, ApprovalStatus, TestCaseStatus
)
from app.database import SessionLocal
from app.services.ai_brain import AIBrainService
from app.services.executor import ExecutorService
from app.utils.datetime_utils import utcnow

logger = logging.getLogger(__name__)


class HealingService:
    def __init__(self, ai=None, executor=None):
        # Default to the shared singletons; import lazily because
        # app.services.__init__ instantiates this service itself.
        if ai is None or executor is None:
            from app.services import ai_service, executor_service
            self.ai = ai or ai_service
            self.executor = executor or executor_service
        else:
            self.ai = ai
            self.executor = executor
        self.demo_mode = settings.DEMO_MODE

    def create_heal_attempt(
        self,
        test_case_id: str,
        failure_type: FailureType,
        original_steps: str,
        failure_message: str,
        current_ui: Optional[str] = None,
        current_api_spec: Optional[str] = None
    ) -> HealAttempt:
        db = SessionLocal()
        try:
            test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
            if not test_case:
                raise ValueError(f"Test case {test_case_id} not found")

            # Ask AI to propose a fix
            proposal = self.ai.propose_heal(
                test_title=test_case.title,
                original_steps=original_steps,
                failure_type=failure_type.value,
                failure_message=failure_message,
                current_ui=current_ui,
                current_api_spec=current_api_spec
            )

            heal = HealAttempt(
                id=str(uuid.uuid4()),
                test_case_id=test_case_id,
                failure_type=failure_type,
                original_steps=original_steps,
                proposed_steps=proposal["proposed_steps"],
                llm_rationale=proposal["rationale"],
                status=HealStatus.proposed
            )
            db.add(heal)
            db.commit()
            db.refresh(heal)
            return heal
        finally:
            db.close()

    def approve_heal(self, heal_id: str) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            heal = db.query(HealAttempt).filter(HealAttempt.id == heal_id).first()
            if not heal:
                return {"success": False, "error": "Heal attempt not found"}
            heal.status = HealStatus.accepted
            db.commit()
            return {"success": True, "heal_id": heal_id, "status": "accepted"}
        finally:
            db.close()

    def reject_heal(self, heal_id: str) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            heal = db.query(HealAttempt).filter(HealAttempt.id == heal_id).first()
            if not heal:
                return {"success": False, "error": "Heal attempt not found"}
            heal.status = HealStatus.rejected
            db.commit()
            return {"success": True, "heal_id": heal_id, "status": "rejected"}
        finally:
            db.close()

    def execute_heal(self, heal_id: str) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            heal = db.query(HealAttempt).filter(HealAttempt.id == heal_id).first()
            if not heal:
                return {"success": False, "error": "Heal attempt not found"}

            test_case = db.query(TestCase).filter(TestCase.id == heal.test_case_id).first()
            if not test_case:
                return {"success": False, "error": "Test case not found"}

            # Create a temporary test case with proposed steps
            proposed_steps_json = json.dumps(
                [{"action": line.strip(), "selector": "", "value": "", "assertion": ""}
                 for line in heal.proposed_steps.split("\n") if line.strip()]
            )
            healed_test = TestCase(
                id=f"{test_case.id}-healed-{uuid.uuid4().hex[:8]}",
                pipeline_run_id=test_case.pipeline_run_id,
                title=f"{test_case.title} (Healed)",
                test_type=test_case.test_type,
                priority=test_case.priority,
                steps=proposed_steps_json,
                expected_result=test_case.expected_result,
                risk_rationale=test_case.risk_rationale,
                generated_by="heal",
                approval_status=ApprovalStatus.approved,
                status=TestCaseStatus.approved
            )
            db.add(healed_test)
            db.commit()
            db.refresh(healed_test)

            # Execute the healed test
            results = self.executor.execute_tests([healed_test])
            self.executor.store_results(results, heal_attempt_id=heal.id)

            result = results[0]
            heal.status = HealStatus.verified if result.outcome == TestOutcome.passed else HealStatus.rejected
            heal.verified_at = utcnow()
            db.commit()

            return {
                "success": True,
                "heal_id": heal_id,
                "outcome": result.outcome.value,
                "duration_ms": result.duration_ms,
                "heal_status": heal.status.value
            }
        finally:
            db.close()

    def get_heal_attempts(self, test_case_id: str) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            heals = db.query(HealAttempt).filter(HealAttempt.test_case_id == test_case_id).all()
            return [
                {
                    "id": h.id,
                    "failure_type": h.failure_type.value,
                    "original_steps": h.original_steps,
                    "proposed_steps": h.proposed_steps,
                    "rationale": h.llm_rationale,
                    "status": h.status.value,
                    "proposed_at": h.proposed_at.isoformat() if h.proposed_at else None,
                    "verified_at": h.verified_at.isoformat() if h.verified_at else None
                }
                for h in heals
            ]
        finally:
            db.close()
