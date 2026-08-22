from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import PipelineRun, TestCase, TestResult, Repository
from typing import Dict, Any

router = APIRouter()


@router.get("/overview")
def get_dashboard_overview(db: Session = Depends(get_db)):
    total_repos = db.query(Repository).count()
    total_runs = db.query(PipelineRun).count()
    recent_runs = db.query(PipelineRun).order_by(PipelineRun.created_at.desc()).limit(10).all()

    status_counts = {}
    for run in recent_runs:
        status_counts[run.status.value] = status_counts.get(run.status.value, 0) + 1

    risk_counts = {}
    for run in recent_runs:
        if run.risk_level:
            risk_counts[run.risk_level.value] = risk_counts.get(run.risk_level.value, 0) + 1

    return {
        "total_repositories": total_repos,
        "total_pipeline_runs": total_runs,
        "recent_runs": [
            {
                "id": r.id,
                "repository": r.repository.full_name if r.repository else "unknown",
                "pr_number": r.github_pr_number,
                "status": r.status.value,
                "risk_level": r.risk_level.value if r.risk_level else None,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in recent_runs
        ],
        "status_breakdown": status_counts,
        "risk_breakdown": risk_counts
    }


@router.get("/runs/{run_id}/details")
def get_run_details(run_id: str, db: Session = Depends(get_db)):
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    tests = db.query(TestCase).filter(TestCase.pipeline_run_id == run_id).all()
    test_ids = [t.id for t in tests]
    results = db.query(TestResult).filter(TestResult.test_case_id.in_(test_ids)).all()

    return {
        "run": {
            "id": run.id,
            "repository": run.repository.full_name if run.repository else "unknown",
            "pr_number": run.github_pr_number,
            "commit_sha": run.commit_sha,
            "status": run.status.value,
            "risk_level": run.risk_level.value if run.risk_level else None,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None
        },
        "tests": [
            {
                "id": t.id,
                "title": t.title,
                "priority": t.priority.value if t.priority else None,
                "approval_status": t.approval_status.value if t.approval_status else None,
                "outcome": t.outcome.value if t.outcome else None,
                "failure_message": t.failure_message,
                "failure_type": t.failure_type.value if t.failure_type else None
            }
            for t in tests
        ],
        "results": [
            {
                "id": r.id,
                "test_case_id": r.test_case_id,
                "outcome": r.outcome.value,
                "failure_step": r.failure_step,
                "failure_message": r.failure_message,
                "duration_ms": r.duration_ms
            }
            for r in results
        ]
    }
