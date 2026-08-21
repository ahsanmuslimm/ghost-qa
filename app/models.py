from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    Enum as SQLEnum, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class OrganisationPlan(str, enum.Enum):
    free = "free"
    starter = "starter"
    team = "team"


class RepositoryTier(str, enum.Enum):
    free = "free"
    starter = "starter"
    team = "team"


class PipelineStatus(str, enum.Enum):
    queued = "queued"
    extracting = "extracting"
    generating = "generating"
    awaiting_approval = "awaiting_approval"
    running = "running"
    completed = "completed"
    failed = "failed"


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TestType(str, enum.Enum):
    functional = "functional"
    regression = "regression"
    edge_case = "edge_case"
    integration = "integration"


class TestPriority(str, enum.Enum):
    p0_critical = "p0_critical"
    p1_high = "p1_high"
    p2_medium = "p2_medium"
    p3_low = "p3_low"


class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class TestCaseStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    running = "running"
    passed = "passed"
    failed = "failed"
    healed = "healed"


class TestOutcome(str, enum.Enum):
    passed = "passed"
    failed = "failed"
    skipped = "skipped"
    timed_out = "timed_out"


class FailureType(str, enum.Enum):
    selector_broken = "selector_broken"
    api_contract = "api_contract"
    assertion_stale = "assertion_stale"
    assertion_failed = "assertion_failed"
    timeout = "timeout"
    network = "network"
    unknown = "unknown"


class HealStatus(str, enum.Enum):
    proposed = "proposed"
    accepted = "accepted"
    rejected = "rejected"
    verified = "verified"


class Organisation(Base):
    __tablename__ = "organisations"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    github_org_id = Column(String, unique=True, nullable=True)
    billing_email = Column(String, nullable=True)
    plan = Column(SQLEnum(OrganisationPlan), default=OrganisationPlan.free)
    stripe_customer_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    repositories = relationship("Repository", back_populates="organisation")


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String, primary_key=True, index=True)
    organisation_id = Column(String, ForeignKey("organisations.id"), nullable=False)
    github_repo_id = Column(String, unique=True, nullable=True)
    full_name = Column(String, nullable=False, index=True)
    default_branch = Column(String, default="main")
    webhook_secret = Column(String, nullable=True)
    tier = Column(SQLEnum(RepositoryTier), default=RepositoryTier.free)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organisation = relationship("Organisation", back_populates="repositories")
    pipeline_runs = relationship("PipelineRun", back_populates="repository")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(String, primary_key=True, index=True)
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    trigger_type = Column(String, default="github_pr")
    github_pr_number = Column(Integer, nullable=True, index=True)
    commit_sha = Column(String, nullable=True)
    diff_url = Column(String, nullable=True)
    linked_issue_id = Column(String, nullable=True)
    status = Column(SQLEnum(PipelineStatus), default=PipelineStatus.queued, index=True)
    risk_level = Column(SQLEnum(RiskLevel), nullable=True, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    repository = relationship("Repository", back_populates="pipeline_runs")
    test_cases = relationship("TestCase", back_populates="pipeline_run", cascade="all, delete-orphan")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(String, primary_key=True, index=True)
    pipeline_run_id = Column(String, ForeignKey("pipeline_runs.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    test_type = Column(SQLEnum(TestType), default=TestType.functional)
    priority = Column(SQLEnum(TestPriority), default=TestPriority.p2_medium)
    steps = Column(Text, nullable=False)
    expected_result = Column(Text, nullable=True)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.medium)
    risk_rationale = Column(Text, nullable=True)
    generated_by = Column(String, default="claude")
    status = Column(SQLEnum(TestCaseStatus), default=TestCaseStatus.pending, index=True)
    approval_status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.pending, index=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    uipath_test_id = Column(String, nullable=True)
    outcome = Column(SQLEnum(TestOutcome), nullable=True, index=True)
    failure_step = Column(String, nullable=True)
    failure_message = Column(Text, nullable=True)
    failure_type = Column(SQLEnum(FailureType), nullable=True)
    screenshot_url = Column(String, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    robot_id = Column(String, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    pipeline_run = relationship("PipelineRun", back_populates="test_cases")
    test_results = relationship("TestResult", back_populates="test_case", cascade="all, delete-orphan")
    heal_attempts = relationship("HealAttempt", back_populates="test_case", cascade="all, delete-orphan")

    @property
    def status_display(self):
        """Return display status combining approval and outcome."""
        if self.outcome:
            return self.outcome.value
        return self.approval_status.value


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(String, primary_key=True, index=True)
    test_case_id = Column(String, ForeignKey("test_cases.id"), nullable=False, index=True)
    outcome = Column(SQLEnum(TestOutcome), nullable=False, index=True)
    failure_step = Column(String, nullable=True)
    failure_message = Column(Text, nullable=True)
    failure_type = Column(SQLEnum(FailureType), nullable=True)
    screenshot_url = Column(String, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    robot_id = Column(String, nullable=True)
    heal_attempt_id = Column(String, ForeignKey("heal_attempts.id"), nullable=True, index=True)
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)

    test_case = relationship("TestCase", back_populates="test_results")
    heal_attempt = relationship("HealAttempt", back_populates="test_results")


class HealAttempt(Base):
    __tablename__ = "heal_attempts"

    id = Column(String, primary_key=True, index=True)
    test_case_id = Column(String, ForeignKey("test_cases.id"), nullable=False, index=True)
    failure_type = Column(SQLEnum(FailureType), nullable=False)
    original_steps = Column(Text, nullable=False)
    proposed_steps = Column(Text, nullable=False)
    llm_rationale = Column(Text, nullable=True)
    status = Column(SQLEnum(HealStatus), default=HealStatus.proposed, index=True)
    proposed_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)

    test_case = relationship("TestCase", back_populates="heal_attempts")
    test_results = relationship("TestResult", back_populates="heal_attempt", cascade="all, delete-orphan")


# Indexes for common queries
Index("ix_pipeline_runs_repo_status", PipelineRun.repository_id, PipelineRun.status)
Index("ix_pipeline_runs_commit_sha", PipelineRun.commit_sha)
Index("ix_test_cases_run_priority", TestCase.pipeline_run_id, TestCase.priority)
Index("ix_test_results_test_outcome", TestResult.test_case_id, TestResult.outcome)
Index("ix_heal_attempts_test_status", HealAttempt.test_case_id, HealAttempt.status)
