from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from app.config import settings
from app.database import init_db
from app.api import webhooks, runs, tests, heals, dashboard
import logging

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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="/home/kali-attacker/ghost-qa/static"), name="static")
templates = Jinja2Templates(directory="/home/kali-attacker/ghost-qa/templates")

# Include routers
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
app.include_router(tests.router, prefix="/api/tests", tags=["tests"])
app.include_router(heals.router, prefix="/api/heals", tags=["heals"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])


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


# Initialize database on startup
@app.on_event("startup")
def on_startup():
    init_db()
    logger.info(f"Ghost QA started in {settings.APP_ENV} mode (DEMO_MODE={settings.DEMO_MODE})")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG
    )
