# Ghost QA — Complete Run Guide (Stage by Stage)

Everything needed to run Ghost QA from an empty machine to a monitored
production stack. Every stage lists: what it does, exact commands, and the
output you should see. PowerShell and bash commands are equivalent; pick one.

**Architecture in one paragraph:** a GitHub PR webhook hits the FastAPI
backend → the AI Brain generates UiPath test cases → the Executor runs them on
UiPath Test Cloud → the Risk Engine scores the run → failing tests get
Self-Healing proposals → approvers accept/reject in the React frontend →
Slack/UiPath Action Center get notified. Prometheus + Grafana observe it all.

---

## Choosing your run mode (decide this first)

| Question | Answer | What to do |
|----------|--------|-----------|
| Just evaluating / demoing, no budget? | **Demo Mode** (free) | keep `DEMO_MODE=true` (the `.env.example` default) — no credentials at all; every stage works on realistic fixtures |
| Have real credentials (GitHub, Gemini, Slack)? | **Live Mode** | set `DEMO_MODE=false`, fill `.env` (see README → "Quickstart — Live Mode"), verify with `python scripts/validate_credentials.py` |
| On the UiPath **free plan** (no Test Manager license)? | Live Mode + built-in executor | set `UIPATH_EXECUTION=mock` — GitHub/AI/Slack stay real, execution uses the built-in executor |
| Have a UiPath Test Manager license? | Full Live Mode | set `UIPATH_EXECUTION=cloud` + all `UIPATH_*` credentials |

The mode you are actually in is always visible: startup log line and
`GET /` → `demo_mode` + `execution_backend` (`demo` | `uipath` | `mock`).

---

## Stage 0 — Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.11+ | `python --version` |
| Node.js | 20+ | `node --version` |
| Git | any | `git --version` |
| Docker (optional, for Stages 6–7) | 24+ | `docker --version` |

```powershell
git clone https://github.com/ahsanmuslimm/ghost-qa.git
cd ghost-qa
```

## Stage 1 — Backend (development mode)

**What it does:** installs Python deps, creates the SQLite dev database,
seeds RBAC roles/permissions and the bootstrap admin, starts the API on :8000.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1          # bash: source .venv/bin/activate
pip install -r requirements.txt

copy .env.example .env              # bash: cp .env.example .env
# edit .env → set GEMINI_API_KEY (or leave AI_PROVIDER=demo for offline runs)

python run.py                       # dev server with reload
```

**Expected output:**
```
Ghost QA started in development mode (DEMO_MODE=False)
Uvicorn running on http://0.0.0.0:8000
```

**Verify:** `curl http://localhost:8000/` → `{"status":"Ghost QA running",...}`

> **Demo mode** (`DEMO_MODE=true`, `AI_PROVIDER=demo` in .env) runs the whole
> pipeline with stubbed AI/UiPath/GitHub — no external accounts needed. This
> is how the smoke tests and CI container test run.

**Login credentials (seeded):** `admin@ghost.qa` / `Admin123!`
(change `ADMIN_DEFAULT_PASSWORD` before any real deployment).

## Stage 2 — Simulate a GitHub webhook (see the pipeline run)

**What it does:** feeds a PR event into `/api/webhooks/github`; the pipeline
generates tests, executes them, scores risk, and (in demo) proposes a heal.

```powershell
curl -X POST http://localhost:8000/api/webhooks/github `
  -H "Content-Type: application/json" `
  -H "X-GitHub-Event: pull_request" `
  --data-binary @scripts\sample_webhook_payload.json
```

**Verify:** `GET /api/runs` (with Bearer token) shows a new run; in demo mode
it completes within seconds. Token:
`POST /auth/login {"email":"admin@ghost.qa","password":"Admin123!"}` → `token`.

## Stage 3 — Frontend (development)

**What it does:** installs the React SPA and serves it on :5173 with a dev
proxy forwarding `/api`, `/auth`, `/report` to the backend on :8000
(same-origin, no CORS setup needed).

```powershell
cd frontend
npm ci
npm run dev
```

**Expected:** `Local: http://localhost:5173/` — log in with the admin
credentials. Pages: Dashboard, Pipeline Runs, Run detail (tests/results/risk
report/heals tabs), Test Cases, Admin (users & roles).

**Production build check:** `npm run build` → type-check + Vite bundle in `dist/`.

## Stage 4 — Tests, security scan, smoke suite (quality gates)

```powershell
# unit + integration suite (126 tests, coverage gate 70% in CI)
python -m pytest tests/ -q --cov=app --cov-report=term

# static analysis + dependency audit (same checks as CI)
pip install -r requirements-dev.txt
.\scripts\security_scan.ps1

# end-to-end deployment smoke test against a running instance
python scripts\smoke_test_deploy.py --url http://localhost:8000
```

**Expected:** `126 passed`, bandit exit 0 (medium+), smoke `12/12 checks passed`.

## Stage 5 — Load testing (optional, pre-production)

```powershell
pip install -r loadtests\requirements.txt
locust -f loadtests\locustfile.py --host http://localhost:8000
# web UI on :8089; or headless:
locust -f loadtests\locustfile.py --host http://localhost:8000 --headless -u 100 -r 10 -t 5m
```

## Stage 6 — Production stack with Docker (single host)

**What it does:** builds hardened images (multi-stage, non-root) and runs the
full stack: PostgreSQL 15, API (migrations auto-run in entrypoint), frontend
nginx, Prometheus, Grafana.

```bash
cp .env.example .env
# REQUIRED edits: POSTGRES_PASSWORD, SECRET_KEY, GRAFANA_ADMIN_PASSWORD,
#                 CORS_ORIGINS=http://localhost:3000, real API keys

docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps     # all "healthy"
```

| Service | URL | Purpose |
|---------|-----|---------|
| API | http://localhost:8000 | FastAPI + `/metrics` |
| Frontend | http://localhost:3000 | nginx SPA, proxies /api |
| Prometheus | http://localhost:9090 | scrapes API every 15s |
| Alertmanager | http://localhost:9093 | routes alerts → API relay → Slack |
| Grafana | http://localhost:3001 | "Ghost QA Overview" dashboard |

**Verify:** `python scripts/smoke_test_deploy.py --url http://localhost:8000`
→ 12/12. Open Grafana → dashboards → request rate/latency panels populate
after a minute of traffic.

**Backups:** see `docs/deployment-guide.md` §3 (pg_dump recipe).

## Stage 7 — Kubernetes (cluster)

**What it does:** deploys the same image with migrations as an init container,
readiness/liveness probes, Prometheus scrape annotations, HPA 2→6 replicas.

```bash
# 1. create the secret with REAL values (template is k8s/secret.yaml)
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml     # set your hostname + TLS secret
kubectl apply -f k8s/hpa.yaml
kubectl -n ghost-qa rollout status deployment/ghost-qa
```

Replace `ghcr.io/YOUR_ORG/ghost-qa:latest` in deployment.yaml with the image
published by the `Docker Build & Publish` workflow.

## Stage 8 — Continuous monitoring (post-deploy)

```powershell
# manual watch window (alerts on >5% 5xx, p95 >2s, 3× consecutive failures)
python scripts\monitor_health.py --url https://your-host --interval 30
```

Plus always-on: Prometheus alert rules in `monitoring/alerts.yml`
(HighErrorRate / HighLatencyP95 / InstanceDown) and the Grafana dashboard.

**Alert delivery path:** Prometheus → Alertmanager (`:9093`) →
`POST /alertmanager/webhook` on the API (bearer secret
`ALERTMANAGER_WEBHOOK_SECRET`, injected into Alertmanager as a file secret) →
Slack via the existing bot token. Test the relay without waiting for a real
incident:

```powershell
curl -X POST http://localhost:8000/alertmanager/webhook `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer <ALERTMANAGER_WEBHOOK_SECRET>" `
  --data-binary @scripts\sample_alert.json
# → {"status":"ok","delivered":1} and a Slack message (or [DEMO] log line)
```

## Stage 9 — CI/CD (automatic on push)

| Workflow | Runs |
|----------|------|
| Backend CI | flake8 + pytest (coverage ≥70%) |
| Frontend CI | `npm ci` + type-check + build |
| Security Scan | bandit, pip-audit, Trivy image scan |
| Docker Build & Publish | builds images, container smoke test, pushes to GHCR on main/tags |

---

## Troubleshooting

| Symptom | Cause → fix |
|---------|-------------|
| `Address already in use :8000` | another instance running → stop it or change `APP_PORT` |
| Frontend login fails | backend not on :8000, or wrong `VITE_API_URL`; dev proxy needs backend up first |
| `401` on every API call | token expired (JWT 60 min) → log in again |
| Webhook returns 400 | missing `X-GitHub-Event` header or bad signature when `GITHUB_WEBHOOK_SECRET` is set |
| Container exits immediately | check `docker logs`; historically a path-resolution bug — fixed, verify image is current |
| Grafana dashboard empty | no traffic yet → hit the API or run the smoke suite |
| bandit fails locally but not CI | local bandit too old for your Python → `pip install -U bandit` |
| IDE shows phantom TS errors | command palette → "TypeScript: Restart TS Server" (workspace SDK pinned in .vscode/settings.json) |

**Full deployment/rollback procedures:** `docs/release-runbook.md`
**UAT sign-off checklist:** `docs/uat-checklist.md`
**Completion & gaps:** `docs/STATUS_REPORT.md`
