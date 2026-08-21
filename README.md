# Ghost QA

**AI-powered QA engineer that lives inside your CI/CD pipeline.**

Ghost QA listens to GitHub pull request webhooks, analyzes code changes using Claude AI, generates contextual test cases, and orchestrates their execution through UiPath Test Cloud or a mock executor. It then calculates risk, posts results back to GitHub, and can even propose self-healing fixes for qualifying test failures.

## Architecture

```
Developer → GitHub PR → Webhook → Ghost QA
                                ↓
                        ┌───────────────┐
                        │  AI Brain     │ ← Claude analyzes diff + context
                        │  (Anthropic)  │ → Generates structured test cases
                        └──────┬────────┘
                               ↓
                        ┌──────┴────────┐
                        │  Database     │ ← Pipeline runs, test cases,
                        │  (PostgreSQL)  │   results, heal attempts
                        └──────┬────────┘
                               ↓
                        ┌──────┴────────┐
                        │ Human Gate    │ ← Approval (local demo or
                        │  (Action      │    UiPath Action Center)
                        │   Center)     │
                        └──────┬────────┘
                               ↓
                        ┌──────┴────────┐
                        │ Execution     │ ← UiPath Test Cloud or Mock
                        │  (UiPath)      │   executor
                        └──────┬────────┘
                               ↓
                        ┌──────┴────────┐
                        │ Risk Engine   │ ← Calculates risk level based
                        │               │   on failures, priorities, test
                        │               │   debt, and coverage
                        └──────┬────────┘
                               ↓
                        ┌──────┴────────┐
                        │ Output        │ ← GitHub PR comment + commit
                        │               │   status
                        └──────┬────────┘
                               ↓
                        ┌──────┴────────┐
                        │ Self-Healing  │ ← AI proposes test fixes for
                        │               │   qualifying failures
                        └───────────────┘
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI |
| AI | Anthropic Claude 3.5 Sonnet |
| Database | PostgreSQL (SQLite for local dev) |
| CI/CD | GitHub Webhooks |
| Test Execution | UiPath Test Cloud + Orchestrator |
| Human Approval | UiPath Action Center (local demo in DEMO_MODE) |
| Dashboard | HTML/CSS/JavaScript |
| Testing | pytest |

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ (for production)

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd ghost-qa

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials

# Initialize database
python -c "from app.database import init_db; init_db()"
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_NAME` | No | `Ghost QA` | Application name |
| `APP_ENV` | No | `development` | Environment (development/staging/production) |
| `APP_DEBUG` | No | `true` | Enable debug mode |
| `APP_PORT` | No | `8000` | Server port |
| `APP_HOST` | No | `0.0.0.0` | Server host |
| `DEMO_MODE` | No | `false` | Enable demo mode (mock all external services) |
| `DATABASE_URL` | Yes | `sqlite:///./ghost_qa.db` | Database connection string |
| `GITHUB_TOKEN` | No* | — | GitHub API token |
| `GITHUB_WEBHOOK_SECRET` | No* | — | GitHub webhook secret for HMAC verification |
| `ANTHROPIC_API_KEY` | No* | — | Claude API key |
| `UIPATH_CLIENT_ID` | No* | — | UiPath client ID |
| `UIPATH_CLIENT_SECRET` | No* | — | UiPath client secret |
| `UIPATH_TENANT_NAME` | No* | — | UiPath tenant name |
| `UIPATH_ORG_ID` | No* | — | UiPath organization ID |
| `UIPATH_ENVIRONMENT_ID` | No* | — | UiPath environment ID |
| `UIPATH_TEST_FOLDER` | No | `GhostQA` | UiPath test folder name |
| `SLACK_BOT_TOKEN` | No | — | Slack bot token for notifications |
| `SLACK_CHANNEL` | No | `ghost-qa-alerts` | Slack channel for notifications |
| `SECRET_KEY` | Yes | — | Application secret key |

*Not required when `DEMO_MODE=true`.

## Database Setup

### SQLite (Local Development)

SQLite is used by default — no additional setup required. The database file is created automatically on startup.

### PostgreSQL (Production)

```sql
CREATE USER ghost_qa WITH PASSWORD 'your_password';
CREATE DATABASE ghost_qa OWNER ghost_qa;
```

Set `DATABASE_URL=postgresql://ghost_qa:your_password@localhost:5432/ghost_qa` in `.env`.

## Running Locally

### Start the server

```bash
# With default settings (SQLite, demo mode)
DEMO_MODE=true python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or use the entry point
python3 run.py
```

### Access the application

- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8000/dashboard
- **Health Check**: http://localhost:8000/

## Running Tests

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_webhook.py -v

# Run with coverage
python3 -m pytest tests/ -v --cov=app --cov-report=html
```

## DEMO_MODE

When `DEMO_MODE=true`, all external services use mock implementations:

- **GitHub**: Returns fixture data (PR diffs, changed files, etc.)
- **Claude AI**: Returns deterministic test cases and healing proposals
- **UiPath**: Mock executor simulates PASS/FAIL/TIMEOUT with random outcomes
- **Action Center**: Tests are auto-approved
- **GitHub Output**: PR comments and commit status are logged but not posted

This allows the entire pipeline to run end-to-end without any external credentials.

When real credentials are configured and `DEMO_MODE=false`:
- Real GitHub API calls are made
- Claude AI generates actual test cases
- Real UiPath Test Cloud executes tests
- Human approval is required via Action Center or API

## GitHub Webhook Setup

### 1. Configure the webhook

In your GitHub repository → Settings → Webhooks → Add webhook:

- **Payload URL**: `http://your-server:8000/api/webhooks/github`
- **Content type**: `application/json`
- **Secret**: Match the `GITHUB_WEBHOOK_SECRET` in your `.env`
- **Events**: Pull requests (opened, synchronize, reopened)

### 2. GitHub token (for API access)

Create a Personal Access Token with `repo` scope and set `GITHUB_TOKEN` in `.env`.

## Claude Configuration

Set `ANTHROPIC_API_KEY` in `.env` to use real Claude AI. The application uses `claude-3-5-sonnet-20240620` for:

- Test case generation from PR diffs
- Test debt detection
- Self-healing proposal generation

## UiPath Configuration

Set the following in `.env`:

- `UIPATH_CLIENT_ID` / `UIPATH_CLIENT_SECRET`: OAuth credentials
- `UIPATH_TENANT_NAME`: Your UiPath tenant
- `UIPATH_ORG_ID`: Organization ID
- `UIPATH_ENVIRONMENT_ID`: Target environment

## Human Approval

Ghost QA does NOT execute AI-generated tests without approval.

### Approval API

```bash
# Approve all tests in a pipeline run
POST /api/runs/{run_id}/approve

# Approve individual test
POST /api/tests/{test_id}/approve

# Reject individual test
POST /api/tests/{test_id}/reject
```

### Approval Flow

1. AI generates test cases
2. Tests are stored with `approval_status=pending`
3. Human reviews tests via API or dashboard
4. Approved tests proceed to execution
5. Only approved tests are executed

In DEMO_MODE, tests are auto-approved for demonstration.

## Risk Reports

After test execution, Ghost QA calculates a risk level:

| Risk Level | Criteria |
|-----------|----------|
| **LOW** | All tests pass |
| **MEDIUM** | Only P2/P3 tests fail |
| **HIGH** | P1 tests fail |
| **CRITICAL** | P0/critical tests fail |

### Risk Factors

- Failed P0/P1 tests
- Failed critical path tests
- Number of failures
- Test priority
- Changed functionality
- Test debt findings
- Coverage gaps

Reports are available:
- As HTML: `GET /report/{run_id}`
- As JSON: `GET /api/runs/{run_id}/report`
- Posted to GitHub PR as a comment

## Self-Healing

When a test fails with a qualifying failure type (`selector_broken`, `api_contract`, `assertion_failed`), Ghost QA can propose a healing fix:

### Flow

1. Test fails with qualifying failure type
2. AI analyzes failure + current code context
3. Heal proposal is stored in `heal_attempts`
4. Human reviews and approves/rejects via API
5. Approved heal is executed
6. If the healed test passes, heal is marked as `verified`

### API

```bash
# Get heal attempts for a test
GET /api/tests/{test_id}/heals

# Approve a heal
POST /api/heals/{heal_id}/approve

# Reject a heal
POST /api/heals/{heal_id}/reject

# Execute a heal (re-run healed test)
POST /api/heals/{heal_id}/execute
```

## API Endpoints

### Webhook

```
POST /api/webhooks/github  — Receive GitHub PR events
```

### Pipeline Runs

```
GET    /api/runs                   — List all pipeline runs
GET    /api/runs/{run_id}          — Get pipeline run details
GET    /api/runs/{run_id}/tests    — Get tests for a run
GET    /api/runs/{run_id}/results  — Get results for a run
GET    /api/runs/{run_id}/report   — Get risk report for a run
POST   /api/runs/{run_id}/approve  — Approve all tests in a run
```

### Tests

```
POST /api/tests/{test_id}/approve  — Approve a test
POST /api/tests/{test_id}/reject   — Reject a test
GET  /api/tests/{test_id}/heals    — Get heal attempts for a test
```

### Heals

```
POST /api/heals/{heal_id}/approve  — Approve a heal proposal
POST /api/heals/{heal_id}/reject   — Reject a heal proposal
POST /api/heals/{heal_id}/execute  — Execute healed test
```

### Dashboard

```
GET /dashboard                      — Dashboard page
GET /report/{run_id}                — Risk report page
GET /api/dashboard/overview         — Dashboard overview data
GET /api/dashboard/runs/{run_id}/details — Pipeline details
```

## Pipeline State Machine

```
queued → extracting → generating → awaiting_approval → running → completed
                                  ↗                    ↘
                        (human rejects)              (self-healing)
                                  ↘                    ↓
                                    → failed       completed → test_failed → heal_proposed
                                                                    ↓
                                                          human_approval → re_run → verified
```

States:
- `queued` — Pipeline created, waiting to start
- `extracting` — Fetching PR data from GitHub
- `generating` — AI generating test cases
- `awaiting_approval` — Tests generated, waiting for human approval
- `running` — Tests executing
- `completed` — Pipeline finished (with results)
- `failed` — Pipeline failed at any stage

## Troubleshooting

### Server won't start

1. Check `.env` exists: `cp .env.example .env`
2. Ensure `DATABASE_URL` is correct
3. Check ports are not in use: `lsof -i :8000`

### Webhook returns 401

1. Ensure `GITHUB_WEBHOOK_SECRET` is set in `.env` (leave empty to skip verification)
2. Verify the secret matches your GitHub webhook configuration

### No tests generated

1. Check `DEMO_MODE=true` is set in `.env`
2. If `ANTHROPIC_API_KEY` is not set, demo mode will auto-enable
3. Check server logs for AI service errors

### Database errors

1. For PostgreSQL: ensure the database exists and credentials are correct
2. For SQLite: ensure the database file is writable
3. Tables are auto-created on startup via `init_db()`

### Tests fail to run

1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Ensure `DEMO_MODE=true` for running tests without external services
3. Clean test database: `rm -f test_ghost_qa.db`

## License

See LICENSE file.
