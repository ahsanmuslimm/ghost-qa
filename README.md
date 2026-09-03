# Ghost QA

**AI-powered QA engineer that lives inside your CI/CD pipeline.**

Ghost QA listens to GitHub pull request webhooks, analyzes the code changes with
AI (Gemini by default), generates contextual test cases, gates them behind human
approval, executes them (UiPath Test Cloud **or** a built-in executor), scores
the release risk, reports back to the PR and Slack, and proposes self-healing
fixes for qualifying failures.

It ships in two professional run modes — **Demo Mode** (free, zero credentials,
full functionality) and **Live Mode** (real integrations via a `.env` file) —
so it can be evaluated instantly and upgraded to production without code changes.

---

## Core Functionality

| # | Capability | What it does |
|---|-----------|--------------|
| 1 | **Webhook-driven pipeline** | Signed GitHub PR webhooks (`X-Hub-Signature-256`) trigger a pipeline run, with deduplication per repo + PR + commit SHA |
| 2 | **AI test generation** | Gemini (primary), Claude or Grok analyze the PR title, body and diff and generate structured, prioritized test cases (P0–P3) |
| 3 | **Human approval gate** | Generated tests are never executed blindly — they wait for approval via the dashboard or API (auto-approve configurable) |
| 4 | **Test execution** | UiPath Test Cloud (XAML generated, uploaded, test set started and polled) **or** the built-in executor when Test Cloud is unavailable |
| 5 | **Risk engine** | Computes LOW / MEDIUM / HIGH / CRITICAL release risk from failures, priorities, test debt and coverage gaps, with a merge recommendation |
| 6 | **Self-healing** | Qualifying failures (`selector_broken`, `api_contract`, `assertion_stale`) get AI-proposed fixes, human-approved and re-executed |
| 7 | **Reporting & notifications** | PR comment + commit status on GitHub, Slack notifications, HTML/JSON risk reports |
| 8 | **Dashboard (React)** | Runs, tests, approvals, heal attempts, risk overview, RBAC-protected |
| 9 | **Auth & RBAC** | JWT login, roles/permissions, per-organisation users |
| 10 | **Ops-ready** | Prometheus metrics, alert rules + Alertmanager→Slack relay, Grafana dashboard, Docker/compose/K8s manifests, CI/CD with security scans |

## Run Modes

Ask yourself one question: **do you want a demo, or a real integration?**

| | 🟢 Demo Mode (default) | 🔵 Live Mode |
|---|---|---|
| Cost | **Free — no accounts, no keys** | Free-tier keys where possible (see below) |
| Setup | none | copy `.env.example` → `.env`, fill credentials |
| GitHub | fixture PR data | real PR fetch, real comment + commit status |
| AI | deterministic demo test cases | real Gemini / Claude / Grok generation |
| Execution | built-in mock executor | UiPath Test Cloud **or** built-in executor |
| Approval | auto-approved | human approval via dashboard/API |
| Slack | logged only | real messages |
| Switch | `DEMO_MODE=true` | `DEMO_MODE=false` |

The active mode is always visible — startup log, and `GET /`:

```json
{"status": "Ghost QA running", "demo_mode": false,
 "execution_backend": "mock",
 "execution": "live integrations — built-in executor (UiPath Test Cloud not enabled)"}
```

### UiPath free plan?

UiPath **Test Manager / Test Cloud requires a paid license**. On the free plan
the API answers `Service: testmanager not found`. That is fully supported here —
keep real GitHub, AI and Slack integrations and set:

```dotenv
UIPATH_EXECUTION=mock
```

Execution then uses the built-in executor while everything else stays live.
When a Test Manager license becomes available, set `UIPATH_EXECUTION=cloud` —
no code changes needed.

---

## Quickstart — Demo Mode (2 minutes, free)

```bash
git clone <repo-url> && cd ghost-qa
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
python run.py
```

- Health: http://localhost:8000/ → `"demo_mode": true`
- API docs: http://localhost:8000/docs
- Dashboard: http://localhost:8000/dashboard
- Login: `admin@ghost.qa` / `Admin123!` (change via `ADMIN_DEFAULT_PASSWORD`)

Trigger a demo pipeline with the bundled sample payload:

```bash
python scripts/send_sample_webhook.py    # or see docs/HOW_TO_RUN.md
```

## Quickstart — Live Mode (client `.env` handoff)

1. **Copy the template**

   ```bash
   copy .env.example .env        # Windows (Linux/macOS: cp)
   ```

2. **Fill in what you have.** Every credential is optional — each integration
   activates when its keys are present and degrades gracefully when they are not.

   | Credential | Where to get it | Cost |
   |---|---|---|
   | `GEMINI_API_KEY` | https://aistudio.google.com/apikey | **Free tier** (primary AI provider) |
   | `GITHUB_TOKEN` | GitHub → Settings → Developer → PAT (`repo` scope) | Free |
   | `GITHUB_WEBHOOK_SECRET` | you invent it (`python -c "import secrets; print(secrets.token_hex(32))"`) and paste the same value into repo Settings → Webhooks | Free |
   | `SLACK_BOT_TOKEN` / `SLACK_CHANNEL` | https://api.slack.com/apps → OAuth (`chat:write`) | Free |
   | `UIPATH_*` | Automation Cloud → Admin → External Applications | **Test Cloud execution needs a paid Test Manager license**; free plan → `UIPATH_EXECUTION=mock` |
   | `SECRET_KEY` | generate (see comment in `.env.example`) | Free |
   | `ANTHROPIC_API_KEY` / `XAI_API_KEY` | optional AI fallbacks — leave blank | paid, optional |

3. **Set the mode**

   ```dotenv
   DEMO_MODE=false
   ```

4. **Validate before going live**

   ```bash
   python scripts/validate_credentials.py     # live-probes every configured integration
   ```

   Exit code 0 = all configured integrations operational (masked output, secrets
   never printed in full).

5. **Start**

   ```bash
   python run.py
   ```

   The startup log tells you exactly which mode is active
   (`LIVE MODE (real integrations, UiPath Test Cloud execution)` vs
   `... built-in executor ...`).

> 🔒 `.env` is git-ignored (`.gitignore`) and must never be committed.
> Deliver it to the deployment host out-of-band (secret manager, encrypted copy).

---

## Architecture

```
Developer → GitHub PR → Webhook (HMAC-verified) → Ghost QA
                                ↓
                        ┌───────────────┐
                        │  AI Brain     │ ← Gemini / Claude / Grok analyze
                        │               │   diff + context → test cases
                        └──────┬────────┘
                               ↓
                        ┌──────┴────────┐
                        │ Human Gate    │ ← Approval via dashboard/API
                        │               │   (Action Center)
                        └──────┬────────┘
                               ↓
                        ┌──────┴────────┐
                        │ Execution     │ ← UiPath Test Cloud or built-in
                        │               │   executor (UIPATH_EXECUTION)
                        └──────┬────────┘
                               ↓
                        ┌──────┴────────┐
                        │ Risk Engine   │ ← LOW/MED/HIGH/CRITICAL from
                        │               │   failures, priorities, debt
                        └──────┬────────┘
                               ↓
                        ┌──────┴────────┐
                        │ Output        │ ← PR comment + commit status +
                        │               │   Slack + HTML/JSON report
                        └──────┬────────┘
                               ↓
                        ┌──────┴────────┐
                        │ Self-Healing  │ ← AI proposes fixes for
                        │               │   qualifying failures
                        └───────────────┘
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI, SQLAlchemy, Alembic |
| AI | Gemini 2.5 Flash (primary); Claude / Grok optional fallbacks |
| Database | SQLite (dev) · PostgreSQL (prod) |
| Test Execution | UiPath Test Cloud (paid) or built-in executor (free) |
| Frontend | React + TypeScript + Vite |
| Notifications | GitHub PR comments/commit status, Slack |
| Monitoring | Prometheus, Alertmanager, Grafana |
| Deployment | Docker, docker-compose, Kubernetes manifests |
| CI/CD | GitHub Actions (tests, bandit, pip-audit, Trivy, image builds) |
| Testing | pytest (+ Hypothesis), 135 tests |

## GitHub Webhook Setup (Live Mode)

Repo → Settings → Webhooks → Add webhook:

- **Payload URL**: `https://your-host/api/webhooks/github` (tunnel with ngrok for local dev)
- **Content type**: `application/json`
- **Secret**: same value as `GITHUB_WEBHOOK_SECRET` in `.env`
- **Events**: Pull requests (opened, synchronize, reopened)

End-to-end proof tool:

```bash
python scripts/live_pipeline_probe.py --owner <owner> --repo <repo> --pr <n>
```

## Approval Flow

1. AI generates test cases → stored with `approval_status=pending`
2. Human reviews via dashboard or API
3. Only approved tests execute (`AUTO_APPROVE=true` skips the gate — demo default)

```
POST /api/runs/{run_id}/approve    — approve all tests in a run
POST /api/tests/{test_id}/approve  — approve one test
POST /api/tests/{test_id}/reject   — reject one test
```

## Risk Reports

| Risk Level | Criteria |
|-----------|----------|
| **LOW** | All tests pass |
| **MEDIUM** | Only P2/P3 tests fail |
| **HIGH** | P1 tests fail |
| **CRITICAL** | P0/critical tests fail |

- HTML: `GET /report/{run_id}` · JSON: `GET /api/runs/{run_id}/report`
- Posted to the PR as a comment + commit status

## Self-Healing

Failures typed `selector_broken`, `api_contract` or `assertion_stale` trigger an
AI heal proposal → human approve/reject → re-execute → `verified` on success.

```
GET  /api/tests/{test_id}/heals
POST /api/heals/{heal_id}/approve | reject | execute
```

## Key API Endpoints

```
POST /api/webhooks/github        — receive signed GitHub PR events
GET  /api/runs                   — list pipeline runs
GET  /api/runs/{id}/report       — risk report (JSON)
GET  /api/dashboard/overview     — dashboard data
POST /auth/login                 — JWT login
GET  /                           — health + active run mode
GET  /metrics                    — Prometheus metrics
POST /alertmanager/webhook       — Alertmanager → Slack relay (bearer secret)
```

Full list: http://localhost:8000/docs

## Running Tests

```bash
python -m pytest tests/ -v                 # 135 tests
python -m pytest tests/ --cov=app          # with coverage
```

## Documentation

| Doc | Purpose |
|-----|---------|
| `docs/HOW_TO_RUN.md` | stage-by-stage run guide (0→9) |
| `docs/live-validation-report.md` | recorded live end-to-end evidence |
| `docs/STATUS_REPORT.md` | requirements traceability + readiness |
| `docs/deployment-guide.md` | production deployment |
| `docs/release-runbook.md` | release procedure |
| `docs/uat-checklist.md` | user acceptance checklist |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Webhook 401 | `GITHUB_WEBHOOK_SECRET` must match the GitHub webhook secret |
| No tests generated | check AI key; without one, set `DEMO_MODE=true` for the demo AI |
| `Service: testmanager not found` | UiPath free plan — set `UIPATH_EXECUTION=mock` |
| Runs behave like demo despite `.env` | a leaked `DEMO_MODE` env var overrides `.env` — check `GET /` → `demo_mode` |
| Server won't start | `pip install -r requirements.txt`; check port 8000 free |
| DB errors | SQLite file writable; PostgreSQL URL correct — tables auto-create on startup |

## License

See LICENSE file.
