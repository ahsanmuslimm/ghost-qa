"""Role-based access control service.

Permission checks accept either a User ORM model or the request-scoped user
dict produced by the JWT middleware ({"permissions": [...]}), so both DB
users and JWT-claim-only users flow through the same enforcement path.
"""
import uuid
import logging
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models import User, Role, Permission
from app.services.auth import hash_password

logger = logging.getLogger(__name__)

# Canonical permission catalogue (kept in sync with database seeding).
ALL_PERMISSIONS = [
    "dashboard:view",
    "pipeline:view", "pipeline:create",
    "test:view", "test:approve", "test:reject",
    "heal:propose", "heal:approve", "heal:execute",
    "user:view", "user:create", "user:edit", "user:delete",
    "system:configure",
]

_VIEWER = ["dashboard:view", "pipeline:view", "test:view"]

# Permission fallback for JWT-only users (no row in the users table), e.g.
# tokens minted from the legacy AUTH_USERS env config. Mirrors the seed map.
ROLE_PERMISSIONS_FALLBACK: Dict[str, List[str]] = {
    "viewer": list(_VIEWER),
    "developer": list(_VIEWER) + ["pipeline:create"],
    "qa_engineer": list(_VIEWER) + ["pipeline:create", "heal:propose", "heal:execute"],
    "approver": list(_VIEWER) + [
        "pipeline:create", "test:approve", "test:reject",
        "heal:propose", "heal:approve", "heal:execute"
    ],
    "admin": list(ALL_PERMISSIONS),
}


class RBACService:
    # ------------------------------------------------------------------
    # Permission checks
    # ------------------------------------------------------------------
    @staticmethod
    def _permissions_of(user: Union[User, Dict[str, Any]]) -> List[str]:
        if isinstance(user, dict):
            return list(user.get("permissions", []))
        return user.permissions

    def has_permission(self, user: Union[User, Dict[str, Any]], permission_name: str) -> bool:
        """Check if user has a specific permission."""
        return permission_name in self._permissions_of(user)

    def has_any_permission(self, user: Union[User, Dict[str, Any]], permission_names: List[str]) -> bool:
        """Check if user has any of the specified permissions."""
        owned = set(self._permissions_of(user))
        return any(p in owned for p in permission_names)

    def has_all_permissions(self, user: Union[User, Dict[str, Any]], permission_names: List[str]) -> bool:
        """Check if user has all of the specified permissions."""
        owned = set(self._permissions_of(user))
        return all(p in owned for p in permission_names)

    # ------------------------------------------------------------------
    # User management
    # ------------------------------------------------------------------
    @staticmethod
    def _user_query(db):
        return db.query(User).options(
            joinedload(User.roles).joinedload(Role.permissions)
        )

    def get_user_by_email(self, email: str) -> Optional[User]:
        db = SessionLocal()
        try:
            return self._user_query(db).filter(User.email == email).first()
        finally:
            db.close()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        db = SessionLocal()
        try:
            return self._user_query(db).filter(User.id == user_id).first()
        finally:
            db.close()

    def list_users(self) -> List[User]:
        db = SessionLocal()
        try:
            return self._user_query(db).order_by(User.email).all()
        finally:
            db.close()

    def create_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role_names: Optional[List[str]] = None
    ) -> User:
        """Create a user; assigns the default role unless roles are given."""
        db = SessionLocal()
        try:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                raise ValueError(f"User with email '{email}' already exists")

            user = User(
                id=str(uuid.uuid4()),
                email=email,
                password_hash=hash_password(password),
                full_name=full_name
            )
            db.add(user)

            if role_names:
                roles = db.query(Role).filter(Role.name.in_(role_names)).all()
                found = {r.name for r in roles}
                missing = set(role_names) - found
                if missing:
                    raise ValueError(f"Unknown roles: {', '.join(sorted(missing))}")
                user.roles.extend(roles)
            else:
                default_role = db.query(Role).filter(Role.is_default == True).first()  # noqa: E712
                if default_role:
                    user.roles.append(default_role)

            db.commit()
            db.refresh(user)
            return self._user_query(db).filter(User.id == user.id).first()
        finally:
            db.close()

    def set_user_roles(self, user_id: str, role_names: List[str]) -> Optional[User]:
        """Replace a user's roles; returns the updated user or None."""
        db = SessionLocal()
        try:
            user = self._user_query(db).filter(User.id == user_id).first()
            if not user:
                return None
            roles = db.query(Role).filter(Role.name.in_(role_names)).all()
            found = {r.name for r in roles}
            missing = set(role_names) - found
            if missing:
                raise ValueError(f"Unknown roles: {', '.join(sorted(missing))}")
            user.roles = roles
            db.commit()
            return self._user_query(db).filter(User.id == user_id).first()
        finally:
            db.close()

    def deactivate_user(self, user_id: str) -> bool:
        """Soft-delete: keep audit history but block authentication."""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            user.is_active = False
            db.commit()
            return True
        finally:
            db.close()

    def assign_role(self, user_id: str, role_name: str) -> bool:
        db = SessionLocal()
        try:
            user = self._user_query(db).filter(User.id == user_id).first()
            role = db.query(Role).filter(Role.name == role_name).first()
            if not user or not role or role in user.roles:
                return False
            user.roles.append(role)
            db.commit()
            return True
        finally:
            db.close()

    def remove_role(self, user_id: str, role_name: str) -> bool:
        db = SessionLocal()
        try:
            user = self._user_query(db).filter(User.id == user_id).first()
            role = db.query(Role).filter(Role.name == role_name).first()
            if not user or not role or role not in user.roles:
                return False
            user.roles.remove(role)
            db.commit()
            return True
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Role / permission management
    # ------------------------------------------------------------------
    def get_role(self, name: str) -> Optional[Role]:
        db = SessionLocal()
        try:
            return (
                db.query(Role)
                .options(joinedload(Role.permissions))
                .filter(Role.name == name)
                .first()
            )
        finally:
            db.close()

    def create_role(self, name: str, description: str = "", is_default: bool = False) -> Role:
        db = SessionLocal()
        try:
            role = Role(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                is_default=is_default
            )
            db.add(role)
            db.commit()
            db.refresh(role)
            return role
        finally:
            db.close()

    def assign_permission_to_role(self, role_name: str, permission_name: str) -> bool:
        db = SessionLocal()
        try:
            role = (
                db.query(Role)
                .options(joinedload(Role.permissions))
                .filter(Role.name == role_name)
                .first()
            )
            permission = db.query(Permission).filter(Permission.name == permission_name).first()
            if not role or not permission or permission in role.permissions:
                return False
            role.permissions.append(permission)
            db.commit()
            return True
        finally:
            db.close()

    def get_permissions_by_resource(self, resource: str) -> List[Permission]:
        db = SessionLocal()
        try:
            return db.query(Permission).filter(Permission.resource == resource).all()
        finally:
            db.close()

    @staticmethod
    def user_payload(user: User) -> Dict[str, Any]:
        """Serialisable representation of a user for API responses."""
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "roles": [r.name for r in user.roles],
            "permissions": user.permissions,
        }
