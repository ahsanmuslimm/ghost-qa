from fastapi import APIRouter, Depends, HTTPException
from app.services.healing import HealingService

router = APIRouter()


@router.post("/{heal_id}/approve")
def approve_heal(heal_id: str):
    service = HealingService()
    result = service.approve_heal(heal_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Approval failed"))
    return result


@router.post("/{heal_id}/reject")
def reject_heal(heal_id: str):
    service = HealingService()
    result = service.reject_heal(heal_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Rejection failed"))
    return result


@router.post("/{heal_id}/execute")
def execute_heal(heal_id: str):
    service = HealingService()
    result = service.execute_heal(heal_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Execution failed"))
    return result
