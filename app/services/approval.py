import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.config import settings
from app.models import TestCase, ApprovalStatus, TestCaseStatus
from app.schemas.test_schemas import TestCaseSchema

logger = logging.getLogger(__name__)


class ApprovalService:
    def __init__(self):
        self.demo_mode = settings.DEMO_MODE

    def get_pending_tests(self, pipeline_run_id: str) -> List[Dict[str, Any]]:
        """Get tests awaiting approval for a pipeline run."""
        from app.database import SessionLocal
        from app.models import TestCase as TCModel
        db = SessionLocal()
        try:
            tests = db.query(TCModel).filter(
                TCModel.pipeline_run_id == pipeline_run_id,
                TCModel.approval_status == ApprovalStatus.pending
            ).all()
            return [
                {
                    "id": t.id,
                    "title": t.title,
                    "priority": t.priority.value,
                    "steps": json.loads(t.steps) if t.steps else [],
                    "expected_result": t.expected_result,
                    "risk_level": t.risk_level.value if t.risk_level else "medium",
                    "risk_rationale": t.risk_rationale
                }
                for t in tests
            ]
        finally:
            db.close()

    def approve_test(self, test_id: str, approved_by: str = "system") -> Dict[str, Any]:
        from app.database import SessionLocal
        from app.models import TestCase as TCModel
        db = SessionLocal()
        try:
            test = db.query(TCModel).filter(TCModel.id == test_id).first()
            if not test:
                return {"success": False, "error": "Test not found"}
            test.approval_status = ApprovalStatus.approved
            test.status = TestCaseStatus.approved
            test.approved_by = approved_by
            test.approved_at = datetime.utcnow()
            db.commit()
            return {"success": True, "test_id": test_id, "status": "approved"}
        finally:
            db.close()

    def reject_test(self, test_id: str, reason: str = "") -> Dict[str, Any]:
        from app.database import SessionLocal
        from app.models import TestCase as TCModel
        db = SessionLocal()
        try:
            test = db.query(TCModel).filter(TCModel.id == test_id).first()
            if not test:
                return {"success": False, "error": "Test not found"}
            test.approval_status = ApprovalStatus.rejected
            test.status = TestCaseStatus.rejected
            db.commit()
            return {"success": True, "test_id": test_id, "status": "rejected"}
        finally:
            db.close()

    def approve_all(self, pipeline_run_id: str, approved_by: str = "system") -> Dict[str, Any]:
        from app.database import SessionLocal
        from app.models import TestCase as TCModel
        db = SessionLocal()
        try:
            tests = db.query(TCModel).filter(
                TCModel.pipeline_run_id == pipeline_run_id,
                TCModel.approval_status == ApprovalStatus.pending
            ).all()
            count = 0
            for test in tests:
                test.approval_status = ApprovalStatus.approved
                test.status = TestCaseStatus.approved
                test.approved_by = approved_by
                test.approved_at = datetime.utcnow()
                count += 1
            db.commit()
            return {"success": True, "approved_count": count}
        finally:
            db.close()

    def get_approval_summary(self, pipeline_run_id: str) -> Dict[str, Any]:
        from app.database import SessionLocal
        from app.models import TestCase as TCModel
        db = SessionLocal()
        try:
            total = db.query(TCModel).filter(TCModel.pipeline_run_id == pipeline_run_id).count()
            pending = db.query(TCModel).filter(
                TCModel.pipeline_run_id == pipeline_run_id,
                TCModel.approval_status == ApprovalStatus.pending
            ).count()
            approved = db.query(TCModel).filter(
                TCModel.pipeline_run_id == pipeline_run_id,
                TCModel.approval_status == ApprovalStatus.approved
            ).count()
            rejected = db.query(TCModel).filter(
                TCModel.pipeline_run_id == pipeline_run_id,
                TCModel.approval_status == ApprovalStatus.rejected
            ).count()
            return {
                "total": total,
                "pending": pending,
                "approved": approved,
                "rejected": rejected
            }
        finally:
            db.close()
