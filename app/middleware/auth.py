from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from app.services.auth import AuthService


def build_user_context(payload: dict):
    """Turn a verified JWT payload into a request-scoped user context.

    Database users get roles/permissions from RBAC; JWT-only users (e.g.
    legacy AUTH_USERS tokens) fall back to the role-claim permission map.
    Returns None when the user exists in the database but is deactivated.
    """
    from app.services import rbac_service
    from app.services.rbac import ROLE_PERMISSIONS_FALLBACK

    email = payload.get("sub")
    db_user = rbac_service.get_user_by_email(email) if email else None
    if db_user:
        if not db_user.is_active:
            return None
        return {
            "id": db_user.id,
            "email": db_user.email,
            "roles": [r.name for r in db_user.roles],
            "permissions": db_user.permissions,
            "is_admin": db_user.is_admin,
            "sub": email,
        }

    role = payload.get("role", "viewer")
    permissions = ROLE_PERMISSIONS_FALLBACK.get(role, ROLE_PERMISSIONS_FALLBACK["viewer"])
    return {
        "id": None,
        "email": email,
        "roles": [role],
        "permissions": permissions,
        "is_admin": role == "admin",
        "sub": email,
    }


class JWTMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.auth_service = AuthService()

    # Routes that do not require a JWT token
    PUBLIC_PREFIXES = (
        "/auth/",
        "/api/webhooks/",
    )

    async def dispatch(self, request: Request, call_next):
        # Skip public routes
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        for prefix in self.PUBLIC_PREFIXES:
            if request.url.path.startswith(prefix):
                return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"detail": "Missing or invalid Authorization header"},
                status_code=401
            )

        token = auth_header[7:]  # Remove "Bearer " prefix

        try:
            payload = self.auth_service.verify_token(token)
            user = build_user_context(payload)
            if user is None:
                return JSONResponse(
                    {"detail": "User account is deactivated"},
                    status_code=401
                )
            request.state.user = user  # Attach to request state
        except Exception:
            return JSONResponse(
                {"detail": "Invalid or expired token"},
                status_code=401
            )

        return await call_next(request)
