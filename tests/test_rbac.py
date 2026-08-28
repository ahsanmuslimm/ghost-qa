"""
Phase 4 (Tasks 4.2-4.7): RBAC tests.

Covers seeding, the RBAC service, DB-backed authentication, permission
enforcement on endpoints, admin user management and security headers.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import SessionLocal, seed_initial_data
from app.models import User, Role, Permission
from app.services import github_service, rbac_service
from app.services.auth import AuthService


@pytest.fixture
def client():
    from app.database import init_db, Base
    init_db()

    session = SessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()

    seed_initial_data()

    original = github_service.demo_mode
    github_service.demo_mode = True
    with TestClient(app) as c:
        yield c
    github_service.demo_mode = original


def _headers(role: str, email: str = None):
    """JWT for a user that does NOT exist in the users table (fallback map)."""
    service = AuthService()
    token = service.create_token(email or f"{role}-only@ghost.qa", role)["token"]
    return {"Authorization": f"Bearer {token}"}


def _admin_headers(client):
    """Login as the seeded admin and return auth headers."""
    response = client.post(
        "/auth/login",
        json={"email": "admin@ghost.qa", "password": settings.ADMIN_DEFAULT_PASSWORD}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


class TestSeeding:
    def test_seed_creates_roles_permissions_admin(self, client):
        db = SessionLocal()
        try:
            assert db.query(Role).count() == 5
            assert db.query(Permission).count() == 14
            admin = db.query(User).filter(User.email == "admin@ghost.qa").first()
            assert admin is not None
            assert admin.is_admin
        finally:
            db.close()

    def test_seed_is_idempotent(self, client):
        seed_initial_data()
        seed_initial_data()
        db = SessionLocal()
        try:
            assert db.query(Role).count() == 5
            assert db.query(User).filter(User.email == "admin@ghost.qa").count() == 1
        finally:
            db.close()

    def test_viewer_is_default_role(self, client):
        role = rbac_service.get_role("viewer")
        assert role is not None
        assert role.is_default is True


class TestRBACService:
    def test_create_user_assigns_default_role(self, client):
        user = rbac_service.create_user("qa1@ghost.qa", "pw-1", full_name="QA One")
        assert [r.name for r in user.roles] == ["viewer"]
        assert "test:approve" not in user.permissions

    def test_create_user_with_explicit_roles(self, client):
        user = rbac_service.create_user(
            "qa2@ghost.qa", "pw-2", role_names=["qa_engineer", "approver"]
        )
        assert {r.name for r in user.roles} == {"qa_engineer", "approver"}
        assert rbac_service.has_permission(user, "heal:approve")

    def test_create_duplicate_email_rejected(self, client):
        rbac_service.create_user("dup@ghost.qa", "pw-1")
        with pytest.raises(ValueError):
            rbac_service.create_user("dup@ghost.qa", "pw-2")

    def test_unknown_role_rejected(self, client):
        with pytest.raises(ValueError):
            rbac_service.create_user("x@ghost.qa", "pw", role_names=["superadmin"])

    def test_set_user_roles_replaces(self, client):
        user = rbac_service.create_user("swap@ghost.qa", "pw")
        updated = rbac_service.set_user_roles(user.id, ["approver"])
        assert [r.name for r in updated.roles] == ["approver"]

    def test_deactivate_blocks_lookup_auth(self, client):
        user = rbac_service.create_user("gone@ghost.qa", "pw")
        assert rbac_service.deactivate_user(user.id) is True
        assert AuthService().authenticate("gone@ghost.qa", "pw") is None

    def test_permission_checks_on_dict_user(self, client):
        dict_user = {"permissions": ["test:view", "heal:execute"]}
        assert rbac_service.has_permission(dict_user, "heal:execute")
        assert rbac_service.has_any_permission(dict_user, ["nope", "test:view"])
        assert not rbac_service.has_all_permissions(dict_user, ["test:view", "nope"])


class TestDBBackedAuth:
    def test_seeded_admin_can_login(self, client):
        headers = _admin_headers(client)
        assert headers["Authorization"].startswith("Bearer ")

    def test_admin_login_grants_admin_endpoints(self, client):
        response = client.get("/api/users", headers=_admin_headers(client))
        assert response.status_code == 200
        emails = [u["email"] for u in response.json()]
        assert "admin@ghost.qa" in emails

    def test_wrong_password_rejected(self, client):
        response = client.post(
            "/auth/login",
            json={"email": "admin@ghost.qa", "password": "wrong-password"}
        )
        assert response.status_code == 401


class TestPermissionEnforcement:
    def test_viewer_cannot_approve_or_manage_users(self, client):
        viewer = _headers("viewer")
        assert client.post("/api/heals/any-id/approve", headers=viewer).status_code == 403
        assert client.get("/api/users", headers=viewer).status_code == 403

    def test_qa_engineer_can_execute_but_not_approve(self, client):
        qa = _headers("qa_engineer")
        # Approve blocked (403 before reaching the not-found check)
        assert client.post("/api/heals/any-id/approve", headers=qa).status_code == 403
        # Execute allowed by permission; unknown heal id -> 400 from service
        assert client.post("/api/heals/any-id/execute", headers=qa).status_code == 400

    def test_fallback_approver_can_approve(self, client):
        approver = _headers("approver")
        # Permission passes; unknown heal id -> 400 from the service layer
        assert client.post("/api/heals/any-id/approve", headers=approver).status_code == 400

    def test_viewer_can_read_runs(self, client):
        assert client.get("/api/runs", headers=_headers("viewer")).status_code == 200


class TestUsersAdminAPI:
    def test_admin_user_lifecycle(self, client):
        admin = _admin_headers(client)

        # Create a new approver
        created = client.post(
            "/api/users",
            headers=admin,
            json={"email": "new.approver@ghost.qa", "password": "S3cret!",
                  "full_name": "New Approver", "roles": ["approver"]}
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["roles"] == ["approver"]
        user_id = body["id"]

        # New user can immediately authenticate
        login = client.post(
            "/auth/login",
            json={"email": "new.approver@ghost.qa", "password": "S3cret!"}
        )
        assert login.status_code == 200

        # Change roles
        updated = client.put(
            f"/api/users/{user_id}/roles",
            headers=admin,
            json={"roles": ["viewer"]}
        )
        assert updated.status_code == 200
        assert updated.json()["roles"] == ["viewer"]

        # Deactivate
        deleted = client.delete(f"/api/users/{user_id}", headers=admin)
        assert deleted.status_code == 204
        login_again = client.post(
            "/auth/login",
            json={"email": "new.approver@ghost.qa", "password": "S3cret!"}
        )
        assert login_again.status_code == 401

    def test_create_user_validation_errors(self, client):
        admin = _admin_headers(client)
        dup = client.post(
            "/api/users", headers=admin,
            json={"email": "admin@ghost.qa", "password": "x12345"}
        )
        assert dup.status_code == 400
        bad_role = client.post(
            "/api/users", headers=admin,
            json={"email": "y@ghost.qa", "password": "x12345", "roles": ["wizard"]}
        )
        assert bad_role.status_code == 400


class TestSecurityHeaders:
    def test_headers_present_on_responses(self, client):
        response = client.get("/")
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "no-referrer"
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]

    def test_hsts_only_in_production(self, client):
        # Test environment runs as development
        response = client.get("/")
        assert "Strict-Transport-Security" not in response.headers
