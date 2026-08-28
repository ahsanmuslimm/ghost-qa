from fastapi import Request, HTTPException


def get_current_user(request: Request) -> dict:
    """Read `request.state.user`; raise 401 if missing."""
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_permission(*permissions: str):
    """Dependency factory: allow only users holding any of the permissions."""
    def dependency(request: Request) -> dict:
        from app.services import rbac_service
        user = get_current_user(request)
        if not rbac_service.has_any_permission(user, list(permissions)):
            raise HTTPException(
                status_code=403,
                detail=f"One of these permissions required: {', '.join(permissions)}"
            )
        return user
    return dependency
