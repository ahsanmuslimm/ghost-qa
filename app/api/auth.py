from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.services.auth import AuthService
from app.rate_limit import limiter

router = APIRouter()
auth_service = AuthService()


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    expires_in: int


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest):
    """Authenticate user and return JWT token."""
    result = auth_service.authenticate(body.email, body.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return LoginResponse(**result)
