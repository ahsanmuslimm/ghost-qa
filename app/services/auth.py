import os
import json
import time
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import HTTPException
from pydantic import BaseModel
from app.config import settings


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: datetime
    iat: datetime


def hash_password(password: str) -> str:
    """Return SHA-256 hex digest (placeholder). Use bcrypt/argon2 in production."""
    return hashlib.sha256(password.encode()).hexdigest()


class AuthService:
    VALID_ROLES = {"viewer", "developer", "qa_engineer", "approver", "admin"}

    def __init__(self):
        # Parse AUTH_USERS JSON string into in-memory dict: {email: {"password_hash": "...", "role": "..."}}
        auth_users_str = settings.AUTH_USERS
        self._credentials: Dict[str, Dict[str, str]] = {}
        try:
            raw = json.loads(auth_users_str)
            for email, data in raw.items():
                self._credentials[email] = {
                    "password_hash": data.get("password_hash", ""),
                    "role": data.get("role", "viewer")
                }
        except (json.JSONDecodeError, TypeError):
            raise RuntimeError("AUTH_USERS environment variable must be valid JSON")

        self._secret = settings.SECRET_KEY
        self._expiry_minutes = settings.JWT_EXPIRY_MINUTES

    def _hash_password(self, password: str) -> str:
        """Return bcrypt-compatible hash (placeholder). In production, use bcrypt."""
        return hash_password(password)

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash."""
        return hmac.compare_digest(self._hash_password(password), stored_hash)

    def create_token(self, email: str, role: str = "viewer") -> Dict[str, Any]:
        """Return {"token": str, "expires_in": int}."""
        if role not in self.VALID_ROLES:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(self.VALID_ROLES)}")

        # Use epoch seconds directly: .timestamp() on a naive UTC datetime
        # would be interpreted as local time and shift exp/iat by the
        # timezone offset, making tokens appear expired immediately.
        now_epoch = int(time.time())

        payload = {
            "sub": email,
            "role": role,
            "exp": now_epoch + self._expiry_minutes * 60,
            "iat": now_epoch
        }

        # HS256 signing
        import jwt
        token = jwt.encode(payload, self._secret, algorithm="HS256")
        return {"token": token, "expires_in": self._expiry_minutes * 60}

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Return decoded payload or raise HTTPException(401)."""
        import jwt
        from jwt import PyJWTError

        try:
            payload = jwt.decode(token, self._secret, algorithms=["HS256"])
            # Verify expiry
            if time.time() > payload.get("exp", 0):
                raise HTTPException(status_code=401, detail="Token expired")
            return payload
        except PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify credentials and return {"token": ..., "expires_in": ...} or None.

        Database users (RBAC) take priority; env-configured AUTH_USERS act as
        a fallback so deployments keep working before seeding runs.
        """
        db_user = self._authenticate_db_user(email, password)
        if db_user:
            return db_user

        creds = self._credentials.get(email)
        if not creds:
            return None
        if not self._verify_password(password, creds["password_hash"]):
            return None
        return self.create_token(email, creds["role"])

    def _authenticate_db_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Check credentials against the users table; return token dict or None."""
        from app.database import SessionLocal
        from app.models import User

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user or not user.is_active:
                return None
            if not hmac.compare_digest(hash_password(password), user.password_hash):
                return None
            # Primary role for the token claim; the middleware re-derives the
            # full permission set from the database on each request.
            if user.is_admin:
                role = "admin"
            else:
                role = user.roles[0].name if user.roles else "viewer"
            return self.create_token(user.email, role)
        finally:
            db.close()

    def get_user_role(self, email: str) -> Optional[str]:
        """Return user role or None if not found."""
        creds = self._credentials.get(email)
        return creds.get("role") if creds else None
