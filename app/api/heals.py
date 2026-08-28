from fastapi import APIRouter, Depends, HTTPException
from app.services import healing_service
from app.dependencies import require_permission

router = APIRouter()


@router.post("/{heal_id}/approve")
def approve_heal(heal_id: str, user: dict = Depends(require_permission("heal:approve"))):
    result = healing_service.approve_heal(heal_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Approval failed"))
    return result


@router.post("/{heal_id}/reject")
def reject_heal(heal_id: str, user: dict = Depends(require_permission("heal:approve"))):
    result = healing_service.reject_heal(heal_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Rejection failed"))
    return result


@router.post("/{heal_id}/execute")
def execute_heal(heal_id: str, user: dict = Depends(require_permission("heal:execute"))):
    result = healing_service.execute_heal(heal_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Execution failed"))
    return result
