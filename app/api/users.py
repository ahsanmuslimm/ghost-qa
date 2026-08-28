"""Admin endpoints for RBAC user management (user:* permissions)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.services import rbac_service
from app.dependencies import require_permission

router = APIRouter()


class CreateUserRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    roles: Optional[List[str]] = None


class SetRolesRequest(BaseModel):
    roles: List[str]


@router.get("/")
def list_users(user: dict = Depends(require_permission("user:view"))):
    return [rbac_service.user_payload(u) for u in rbac_service.list_users()]


@router.post("/", status_code=201)
def create_user(body: CreateUserRequest, user: dict = Depends(require_permission("user:create"))):
    try:
        created = rbac_service.create_user(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            role_names=body.roles
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return rbac_service.user_payload(created)


@router.put("/{user_id}/roles")
def set_user_roles(user_id: str, body: SetRolesRequest, user: dict = Depends(require_permission("user:edit"))):
    try:
        updated = rbac_service.set_user_roles(user_id, body.roles)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return rbac_service.user_payload(updated)


@router.delete("/{user_id}", status_code=204)
def deactivate_user(user_id: str, user: dict = Depends(require_permission("user:delete"))):
    if not rbac_service.deactivate_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return None
