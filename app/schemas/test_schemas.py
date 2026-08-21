from pydantic import BaseModel, Field
from typing import Optional, List, Any
from enum import Enum
from app.models import (
    TestType, TestPriority, ApprovalStatus, TestCaseStatus, TestOutcome,
    FailureType, HealStatus, RiskLevel
)


class TestStepSchema(BaseModel):
    action: str
    selector: Optional[str] = None
    value: Optional[str] = None
    assertion: Optional[str] = None


class TestCaseSchema(BaseModel):
    id: str
    title: str
    type: TestType = TestType.functional
    priority: TestPriority = TestPriority.p2_medium
    steps: List[TestStepSchema]
    expected_result: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.medium
    risk_rationale: Optional[str] = None


class AITestResponse(BaseModel):
    tests: List[TestCaseSchema]


class TestDebtFinding(BaseModel):
    affected_file: str
    finding: str
    reason: str
    risk: RiskLevel
    recommendation: str


class TestDebtReport(BaseModel):
    findings: List[TestDebtFinding]


class HealProposalSchema(BaseModel):
    original_steps: str
    proposed_steps: str
    rationale: str
    failure_type: FailureType


class RiskReportSchema(BaseModel):
    pipeline_run_id: str
    repository: str
    pr_number: Optional[int]
    commit_sha: Optional[str]
    total_tests: int
    passed: int
    failed: int
    skipped: int
    timed_out: int
    risk_level: RiskLevel
    critical_failures: List[str]
    high_risk_tests: List[str]
    test_debt_findings: List[TestDebtFinding]
    recommendations: List[str]
    execution_time_ms: Optional[int] = None
    recommendation: str = "MERGE"


class TestResultSchema(BaseModel):
    test_case_id: str
    outcome: TestOutcome
    failure_step: Optional[str] = None
    failure_message: Optional[str] = None
    failure_type: Optional[FailureType] = None
    screenshot_url: Optional[str] = None
    duration_ms: Optional[int] = None
    robot_id: Optional[str] = None
    executed_at: Optional[str] = None
