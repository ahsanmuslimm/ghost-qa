from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.database import init_db, seed_initial_data
from app.api import webhooks, runs, tests, heals, dashboard, auth, orgs, users, alerts
from app.middleware.auth import JWTMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.monitoring.metrics import metrics_middleware
from app.rate_limit import limiter
from prometheus_client import make_asgi_app
import logging
import os

# Resolve paths relative to this file (project root)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_static_dir = os.path.join(_project_root, "static")
_template_dir = os.path.join(_project_root, "templates")

# Ensure directories exist
os.makedirs(_static_dir, exist_ok=True)
os.makedirs(_template_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.APP_DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered QA engineer for CI/CD pipelines",
    version="1.0.0"
)

# Rate limiter (shared instance lives in app.rate_limit so routers can use it)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit handler that logs and returns JSON response."""
    client_ip = request.client.host if request.client else "unknown"
    endpoint = request.url.path
    # Extract retry_after from slowapi's detail message or use default
    retry_after = "60"
    if hasattr(exc, "retry_after"):
        retry_after = str(exc.retry_after)
    elif " " in exc.detail:
        try:
            retry_after = exc.detail.split("Retry after ")[-1].split(" ")[0]
        except Exception:
            pass
    logger.warning(f"Rate limit exceeded for IP {client_ip} on endpoint {endpoint}")
    return __import__("fastapi").responses.JSONResponse(
        status_code=429,
        content={"error": f"Rate limit exceeded. Retry after {retry_after} seconds."},
        headers={"Retry-After": retry_after}
    )

# JWT Middleware
app.add_middleware(JWTMiddleware)

# Security response headers (applied to every response)
app.add_middleware(SecurityHeadersMiddleware)


# Prometheus instrumentation (registered last → outermost layer, sees all traffic)
@app.middleware("http")
async def prometheus_instrumentation(request: Request, call_next):
    return await metrics_middleware(request, call_next)

# CORS — origins come from config so production can lock them down
_cors_origins = (
    ["*"] if settings.CORS_ORIGINS.strip() == "*"
    else [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory=_static_dir), name="static")
templates = Jinja2Templates(directory=_template_dir)

# Prometheus scrape endpoint (outside /api so it bypasses JWT auth)
app.mount("/metrics", make_asgi_app())

# Include routers
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
app.include_router(tests.router, prefix="/api/tests", tags=["tests"])
app.include_router(heals.router, prefix="/api/heals", tags=["heals"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(orgs.router, prefix="/api/orgs", tags=["orgs"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
# Alert relay — outside /api (no JWT); bearer-secret protected instead
app.include_router(alerts.router, prefix="/alertmanager", tags=["alerts"])


@app.get("/")
def health():
    return {
        "status": "Ghost QA running",
        "demo_mode": settings.DEMO_MODE,
        "app_env": settings.APP_ENV
    }


@app.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/report/{run_id}")
def report_page(run_id: str, request: Request):
    return templates.TemplateResponse("report.html", {"request": request, "run_id": run_id})


# Initialize database and seed RBAC data on startup
@app.on_event("startup")
def on_startup():
    init_db()
    seed_initial_data()
    logger.info(f"Ghost QA started in {settings.APP_ENV} mode (DEMO_MODE={settings.DEMO_MODE})")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG
    )
