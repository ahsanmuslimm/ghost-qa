# Ghost QA — Complete Demo & Showcase Guide

**Date:** September 3, 2026 | **Mode:** LIVE (real Gemini, GitHub, Slack, UiPath auth)  
**Status:** All stages verified and running

---

## What This Project Does

Ghost QA is an **AI-powered QA engineer embedded in your CI/CD pipeline**.  
When a developer opens a Pull Request on GitHub, Ghost QA:

1. Receives the PR webhook (HMAC-verified)
2. Fetches the actual code diff from GitHub
3. Sends it to **Gemini AI** to generate contextual, prioritized test cases (P0–P3)
4. Gates execution behind a **human approval step**
5. Executes tests via **UiPath Test Cloud** or the built-in executor
6. Scores **release risk** (LOW / MEDIUM / HIGH / CRITICAL)
7. Posts a **PR comment + commit status** back to GitHub
8. Sends a **Slack notification**
9. Proposes **AI self-healing fixes** for broken selectors/assertions
10. Serves everything through a **React dashboard** with RBAC

---

## Architecture Diagram

```
GitHub PR opened
      │
      ▼
POST /api/webhooks/github   ← HMAC signature verified
      │
      ▼
GitHub API  ──────────────► Fetch PR diff (real files changed)
      │
      ▼
Gemini AI  ────────────────► Generate P0-P3 test cases from diff
      │
      ▼
Human Approval Gate ────────► Dashboard / API approve/reject
      │
      ▼
Test Executor ─────────────► UiPath Test Cloud OR built-in mock
      │
      ▼
Risk Engine ───────────────► LOW / MEDIUM / HIGH / CRITICAL
      │
      ├──► GitHub PR comment + commit status (✅/❌)
      ├──► Slack notification
      ├──► HTML + JSON risk report
      └──► Self-healing proposals for failures
```

---

## Verified Run Results (September 3, 2026)

### Stage 0 — Prerequisites ✅
| Tool | Version |
|------|---------|
| Python | 3.14.3 |
| Node.js | v24.14.1 |
| Git | 2.53.0 |

---

### Stage 1 — Backend Running ✅

```
URL:   http://localhost:8000
Mode:  LIVE (DEMO_MODE=false)
AI:    Gemini 2.5 Flash (primary)
Exec:  Built-in executor (UiPath auth passes; Test Manager needs license)
```

**Health endpoint response:**
```json
{
  "status": "Ghost QA running",
  "demo_mode": false,
  "execution_backend": "mock",
  "execution": "live integrations — built-in executor",
  "app_env": "development"
}
```

**To run backend:**
```powershell
python run.py
# → http://localhost:8000
```

**Login:** `admin@ghost.qa` / `Admin123!`

---

### Stage 2a — Live Credential Validation ✅ (5/5 PASS)

```powershell
python scripts/validate_credentials.py
```

| Integration | Result | Evidence |
|-------------|--------|----------|
| Config/Mode | ✅ PASS | DEMO_MODE=False confirmed |
| Gemini AI   | ✅ PASS | `gemini-2.5-flash` returned 5 test cases in ~10s |
| UiPath Auth | ✅ PASS | Real bearer token, folders: `['Shared', 'ghostQA']` |
| Slack       | ✅ PASS | Message delivered to channel `C0BRK9XHCG7` |
| GitHub PAT  | ✅ PASS | Authenticated as `Saimasad123` |

---

### Stage 2b — Live End-to-End Pipeline (Real PR #10) ✅

```powershell
python scripts/live_pipeline_probe.py --owner ahsanmuslimm --repo ghost-qa --pr 10 --url http://127.0.0.1:8000
```

**Result:**
```
webhook intake: HTTP 200 {'status': 'pipeline_started', 'pipeline_run_id': '3e7c996d-...'}
run reached terminal state: completed   (in ~21 seconds)
```

**Full pipeline trace:**
| Stage | Evidence |
|-------|---------|
| Signed webhook intake | HMAC verified, run created |
| PR diff fetch | `GET /repos/ahsanmuslimm/ghost-qa/pulls/10/files` → 200 |
| AI test generation | `gemini-2.5-flash` → **4 tests generated** from real diff |
| Risk scoring | `risk_level: low` computed |
| UiPath auth | `identity_/connect/token` → 200 (token issued) |
| Test execution | Built-in executor → 4/4 passed |
| Slack notification | `chat.postMessage` → 200 (real message sent) |
| GitHub PR comment | `issues/10/comments` → 201 |
| Commit status | `statuses/19c85e60…` → 201 |
| DB persistence | run + 4 test_cases + 4 test_results stored |

**Risk report:**
```json
{
  "total_tests": 4,
  "passed": 4,
  "failed": 0,
  "risk_level": "low",
  "recommendation": "MERGE",
  "recommendations": ["All tests passed. Safe to merge."]
}
```

---

### Stage 3 — React Frontend ✅

```powershell
cd frontend
npm run dev
# → http://localhost:5173
```

**Production build:**
```
✔ 2311 modules transformed
dist/index.html        1.97 kB
dist/assets/index.css  30.28 kB
dist/assets/react.js   164.00 kB
dist/assets/index.js   217.81 kB
dist/assets/charts.js  392.10 kB
✔ built in 6.75s
```

**Pages available:**
- `/` → Login
- `/dashboard` → Overview (total repos, runs, risk breakdown)
- `/runs` → Pipeline Runs list
- `/runs/{id}` → Run detail: Tests | Results | Risk Report | Heals tabs
- `/tests` → All test cases
- `/admin` → Users & Roles (RBAC)

---

### Stage 4 — Test Suite & Quality Gates ✅

```powershell
python -m pytest tests/ -q
```

**Result: 135/135 tests passed** in 21.95s

```powershell
python scripts/smoke_test_deploy.py --url http://localhost:8000
```

**Result: 12/12 smoke checks passed** in 6.7s

| Smoke Check | Result |
|-------------|--------|
| Health endpoint | ✅ PASS |
| Security headers present | ✅ PASS |
| Login succeeds | ✅ PASS |
| JWT returned | ✅ PASS |
| Bad password rejected (401) | ✅ PASS |
| Unauthenticated /api/runs rejected | ✅ PASS |
| Dashboard overview | ✅ PASS |
| Pipeline runs list | ✅ PASS |
| Users list (admin RBAC) | ✅ PASS |
| Prometheus /metrics | ✅ PASS |
| Webhook intake | ✅ PASS |
| Pipeline run created | ✅ PASS |

---

### Stage 8 — Alertmanager → Slack Relay ✅

```powershell
$secret = "b1c83b739c9bda6f5b339fff54e772ce"
curl -X POST http://localhost:8000/alertmanager/webhook \
  -H "Authorization: Bearer $secret" \
  --data-binary @scripts/sample_alert.json
# → {"status":"ok","delivered":1}
```

Alert delivered to real Slack channel via bot token. ✅

---

## What You See in the Browser

### 1. Dashboard — http://localhost:5173
- Login with `admin@ghost.qa` / `Admin123!`
- Overview cards: total repos, total runs, risk breakdown chart
- Recent runs table with status badges

### 2. Pipeline Run Detail — http://localhost:5173/runs/3e7c996d-...
- **Tests tab**: 4 AI-generated test cases with priority (P0/P1), approval status, pass/fail
- **Results tab**: execution timing, per-test outcomes
- **Risk Report tab**: LOW risk, MERGE recommendation
- **Heals tab**: self-healing proposals for any failures

### 3. API Docs — http://localhost:8000/docs
Interactive Swagger UI showing all 40+ endpoints

### 4. HTML Risk Report — http://localhost:8000/report/3e7c996d-211c-418e-869e-0bd60602f11e
Full styled HTML report with risk level, test breakdown, recommendations

### 5. Prometheus Metrics — http://localhost:8000/metrics
Live counters: `ghost_qa_requests_total`, latency histograms, pipeline gauges

---

## Key API Endpoints

```
POST /api/webhooks/github           — receive signed PR events
POST /auth/login                    — JWT login
GET  /api/runs                      — list pipeline runs
GET  /api/runs/{id}/report          — JSON risk report
GET  /api/runs/{id}/tests           — AI-generated test cases
GET  /api/dashboard/overview        — dashboard data
GET  /report/{id}                   — HTML risk report
POST /api/runs/{id}/approve         — approve all tests
GET  /metrics                       — Prometheus metrics
POST /alertmanager/webhook          — alert relay → Slack
```

---

## RBAC Permissions (Admin User)

```
dashboard:view, heal:approve, heal:execute, heal:propose,
pipeline:create, pipeline:view, system:configure,
test:approve, test:reject, test:view,
user:create, user:delete, user:edit, user:view
```

---

## CI/CD Status (GitHub Actions)

| Workflow | Status |
|----------|--------|
| Backend CI (pytest + coverage) | ✅ |
| Frontend CI (tsc + vite build) | ✅ |
| Security Scan (bandit + pip-audit + trivy) | ✅ |
| Docker Build & Publish | ✅ |

---

## One Remaining Item (Not a Code Gap)

The only thing not fully live is **UiPath Test Manager execution itself** — the auth token is issued fine (200), but `Service: testmanager not found` because the Test Manager *service* needs to be enabled on the UiPath tenant (requires a Test Manager license). Set `UIPATH_EXECUTION=cloud` once enabled — zero code changes needed.

Everything else: Gemini AI, GitHub, Slack, HMAC webhooks, risk engine, RBAC, React dashboard — **fully live and verified**.

---

## Quick Restart Commands

```powershell
# Terminal 1 — Backend (Live Mode)
cd "d:\WORKING\PORTFOLIO\FEATURED PROJECTS\ghost-qa"
python run.py

# Terminal 2 — Frontend
cd "d:\WORKING\PORTFOLIO\FEATURED PROJECTS\ghost-qa\frontend"
npm run dev

# Trigger live pipeline (real PR)
python scripts/live_pipeline_probe.py --owner ahsanmuslimm --repo ghost-qa --pr 10 --url http://127.0.0.1:8000

# Validate all live credentials
python scripts/validate_credentials.py

# Full smoke test
python scripts/smoke_test_deploy.py --url http://localhost:8000

# Run all 135 tests
python -m pytest tests/ -q
```
