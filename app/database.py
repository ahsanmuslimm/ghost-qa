from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Engine configuration follows standard production practice:
# - SQLite (dev): allow cross-thread access (FastAPI thread pool)
# - PostgreSQL (prod): pooled connections with pre-ping to drop stale sockets
engine_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update(
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)


def seed_initial_data():
    """Seed RBAC roles, permissions and the bootstrap admin user.

    Idempotent: skipped when roles already exist.
    """
    import uuid
    import logging
    from app.models import User, Role, Permission
    from app.services.auth import hash_password

    logger = logging.getLogger(__name__)
    db = SessionLocal()
    try:
        if db.query(Role).count() > 0:
            return

        permission_defs = [
            ("dashboard:view", "View dashboard", "dashboard", "read"),
            ("pipeline:view", "View pipelines", "pipeline", "read"),
            ("pipeline:create", "Create pipelines", "pipeline", "write"),
            ("test:view", "View tests", "test", "read"),
            ("test:approve", "Approve tests", "test", "approve"),
            ("test:reject", "Reject tests", "test", "reject"),
            ("heal:propose", "Propose heals", "heal", "write"),
            ("heal:approve", "Approve heals", "heal", "approve"),
            ("heal:execute", "Execute heals", "heal", "execute"),
            ("user:view", "View users", "user", "read"),
            ("user:create", "Create users", "user", "write"),
            ("user:edit", "Edit users", "user", "update"),
            ("user:delete", "Delete users", "user", "delete"),
            ("system:configure", "Configure system", "system", "write"),
        ]
        perms = {
            name: Permission(
                id=str(uuid.uuid4()), name=name,
                description=description, resource=resource, action=action
            )
            for name, description, resource, action in permission_defs
        }
        db.add_all(perms.values())
        db.commit()

        viewer = Role(id=str(uuid.uuid4()), name="viewer",
                      description="Read-only access", is_default=True)
        developer = Role(id=str(uuid.uuid4()), name="developer",
                         description="Developer access")
        qa_engineer = Role(id=str(uuid.uuid4()), name="qa_engineer",
                           description="QA Engineer access")
        approver = Role(id=str(uuid.uuid4()), name="approver",
                        description="Can approve tests and heals")
        admin = Role(id=str(uuid.uuid4()), name="admin",
                     description="Administrator access")
        db.add_all([viewer, developer, qa_engineer, approver, admin])
        db.commit()

        view = [perms[n] for n in ("dashboard:view", "pipeline:view", "test:view")]
        viewer.permissions.extend(view)
        developer.permissions.extend(view + [perms["pipeline:create"]])
        qa_engineer.permissions.extend(
            view + [perms["pipeline:create"], perms["heal:propose"], perms["heal:execute"]]
        )
        approver.permissions.extend(
            view + [
                perms["pipeline:create"], perms["test:approve"], perms["test:reject"],
                perms["heal:propose"], perms["heal:approve"], perms["heal:execute"]
            ]
        )
        admin.permissions.extend(perms.values())
        db.commit()

        admin_user = User(
            id=str(uuid.uuid4()),
            email="admin@ghost.qa",
            password_hash=hash_password(settings.ADMIN_DEFAULT_PASSWORD),
            full_name="Admin User"
        )
        admin_user.roles.append(admin)
        db.add(admin_user)
        db.commit()

        logger.info("Initial RBAC data seeded successfully")
    finally:
        db.close()
