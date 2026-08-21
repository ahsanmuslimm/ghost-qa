import logging
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models import TestCase, TestResult, RiskLevel, TestPriority, TestOutcome
from app.schemas.test_schemas import TestDebtFinding, RiskReportSchema
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class RiskEngine:
    def calculate_risk(
        self,
        pipeline_run_id: str,
        test_results: List[TestResult],
        test_cases: List[TestCase],
        test_debt: Optional[List[TestDebtFinding]] = None
    ) -> RiskReportSchema:
        total = len(test_results)
        passed = sum(1 for r in test_results if r.outcome == TestOutcome.passed)
        failed = sum(1 for r in test_results if r.outcome == TestOutcome.failed)
        skipped = sum(1 for r in test_results if r.outcome == TestOutcome.skipped)
        timed_out = sum(1 for r in test_results if r.outcome == TestOutcome.timed_out)

        # Map test cases to results
        results_by_test = {r.test_case_id: r for r in test_results}
        cases_by_id = {tc.id: tc for tc in test_cases}

        critical_failures = []
        high_risk_tests = []
        recommendations = []

        for tc in test_cases:
            result = results_by_test.get(tc.id)
            if result and result.outcome == TestOutcome.failed:
                if tc.priority in (TestPriority.p0_critical, TestPriority.p1_high):
                    critical_failures.append(tc.title)
                if tc.risk_level in (RiskLevel.high, RiskLevel.critical):
                    high_risk_tests.append(tc.title)

        # Determine risk level
        risk_level = RiskLevel.low
        if failed == 0:
            risk_level = RiskLevel.low
            recommendations.append("All tests passed. Safe to merge.")
        else:
            # Check for critical/P0 failures
            has_critical_failure = any(
                cases_by_id.get(r.test_case_id, TestCase()).priority == TestPriority.p0_critical
                for r in test_results if r.outcome == TestOutcome.failed
            )
            has_p1_failure = any(
                cases_by_id.get(r.test_case_id, TestCase()).priority == TestPriority.p1_high
                for r in test_results if r.outcome == TestOutcome.failed
            )

            if has_critical_failure:
                risk_level = RiskLevel.critical
                recommendations.append("DO NOT MERGE: Critical P0 test failure detected.")
            elif has_p1_failure:
                risk_level = RiskLevel.high
                recommendations.append("DO NOT MERGE: High-priority P1 test failure detected.")
            elif failed > 0:
                risk_level = RiskLevel.medium
                recommendations.append("Review failures before merging.")

        # Add test debt recommendations
        if test_debt:
            for debt in test_debt:
                if debt.risk in (RiskLevel.high, RiskLevel.critical):
                    recommendations.append(f"Test debt: {debt.recommendation}")

        # Final recommendation
        final_recommendation = "MERGE"
        if risk_level in (RiskLevel.high, RiskLevel.critical):
            final_recommendation = "DO NOT MERGE"
        elif risk_level == RiskLevel.medium and failed > 0:
            final_recommendation = "REVIEW REQUIRED"

        # Get pipeline run info for report
        from app.models import PipelineRun
        db = SessionLocal()
        try:
            pipeline = db.query(PipelineRun).filter(PipelineRun.id == pipeline_run_id).first()
            repo_name = pipeline.repository.full_name if pipeline and pipeline.repository else "unknown"
            pr_number = pipeline.github_pr_number if pipeline else None
            commit_sha = pipeline.commit_sha if pipeline else None
            execution_time = None
            if pipeline and pipeline.started_at and pipeline.completed_at:
                execution_time = int((pipeline.completed_at - pipeline.started_at).total_seconds() * 1000)
        finally:
            db.close()

        return RiskReportSchema(
            pipeline_run_id=pipeline_run_id,
            repository=repo_name,
            pr_number=pr_number,
            commit_sha=commit_sha,
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            timed_out=timed_out,
            risk_level=risk_level,
            critical_failures=critical_failures,
            high_risk_tests=high_risk_tests,
            test_debt_findings=test_debt or [],
            recommendations=recommendations,
            execution_time_ms=execution_time,
            recommendation=final_recommendation
        )

    def get_risk_level(self, report: RiskReportSchema) -> str:
        return report.risk_level.value
