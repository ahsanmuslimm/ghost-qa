# Ghost QA — Deployment Guide

Production deployment options: Docker Compose (single host) and Kubernetes (cluster).
Local development instructions live in the root `README.md`.

---

## 1. Prerequisites

- Docker 24+ with the Compose plugin (or a Kubernetes 1.27+ cluster)
- A PostgreSQL 15 instance (included in the Compose stack)
- Secrets ready: `SECRET_KEY`, `POSTGRES_PASSWORD`, AI provider keys, GitHub webhook secret
- The frontend is served by its own nginx container; the backend API is proxied same-origin

## 2. Docker Compose (single host)

```bash
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD, SECRET_KEY, GRAFANA_ADMIN_PASSWORD,
# GEMINI_API_KEY, GITHUB_TOKEN, GITHUB_WEBHOOK_SECRET, CORS_ORIGINS ...

docker compose -f docker-compose.prod.yml up -d --build
```

Services and ports:

| Service    | Port | Notes                                        |
|------------|------|----------------------------------------------|
| ghost-qa   | 8000 | FastAPI; migrations run in the entrypoint     |
| frontend   | 3000 | nginx serving the React SPA, proxies `/api`   |
| postgres   | —    | internal only (uncomment ports for direct DB) |
| prometheus | 9090 | scrapes `ghost-qa:8000/metrics`               |
| grafana    | 3001 | provisioned datasource + dashboard            |

The schema migrates automatically on container start (`docker-entrypoint.sh` runs
`alembic upgrade head`). To run migrations alone: `docker compose run --rm ghost-qa ./docker-entrypoint.sh migrate`.

### Security hardening already applied
- Multi-stage image, runtime runs as non-root user `ghost` (uid 1001)
- No source/tests/docs shipped in the image
- `HEALTHCHECK` on backend, frontend, postgres
- Security response headers middleware + rate limiting
- CORS origins configurable via `CORS_ORIGINS` (never leave `*` in production)

### HTTPS
Terminate TLS in front of the stack (Caddy/Traefik/nginx) or with a cloud load
balancer, and set `CORS_ORIGINS` to the public origin.

## 3. PostgreSQL

- Connection pooling is configured in `app/config.py`:
  `DATABASE_POOL_SIZE=20`, `DATABASE_MAX_OVERFLOW=10`, `pool_pre_ping=True`,
  `pool_recycle=3600`.
- **Capacity rule:** `workers × (pool_size + max_overflow)` must stay below
  PostgreSQL `max_connections`. Default Compose stack uses 2 workers → max 60
  connections, safe for the default 100.
- **Backups:** schedule `pg_dump` from the host:
  ```bash
  docker compose -f docker-compose.prod.yml exec -T postgres \
      pg_dump -U ghost_qa ghost_qa | gzip > backup-$(date +%F).sql.gz
  ```
  Restore: `gunzip -c backup.sql.gz | docker compose ... exec -T postgres psql -U ghost_qa ghost_qa`

## 4. Monitoring & logging

- **Metrics:** the API exposes Prometheus metrics at `GET /metrics`
  (`ghost_qa_requests_total`, `ghost_qa_request_latency_seconds`,
  `ghost_qa_active_requests`). The endpoint bypasses JWT auth (it is outside `/api`)
  — restrict network access to it in production.
- **Prometheus** (`monitoring/prometheus.yml`) scrapes the API every 15s, 15-day retention.
- **Alerts** (`monitoring/alerts.yml`): HighErrorRate (>5% 5xx), HighLatencyP95 (>2s),
  InstanceDown. Wire an Alertmanager target in `prometheus.yml` to deliver them.
- **Grafana:** auto-provisioned Prometheus datasource and the "Ghost QA Overview"
  dashboard (request rate, 5xx %, latency percentiles, active requests).
- **Logs:** structured-ish single-line format to stdout; collect with
  `docker logs` / a log shipper (Fluent Bit, Vector) in larger setups.

## 5. Kubernetes

Manifests live in `k8s/`:

```bash
kubectl apply -f k8s/deployment.yaml   # namespace + deployment (migrate initContainer)
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml       # TEMPLATE — create the real secret out-of-band
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml      # set your hostname + TLS
kubectl apply -f k8s/hpa.yaml          # autoscale 2→6 replicas
```

- Replace `ghcr.io/YOUR_ORG/ghost-qa:latest` with your published image.
- The deployment runs `./docker-entrypoint.sh migrate` as an init container,
  so migrations complete before any pod serves traffic.
- Pods expose Prometheus scrape annotations (`/metrics:8000`).
- Provide PostgreSQL externally (managed DB recommended) and point
  `DATABASE_URL` in the secret at it.

## 6. CI/CD

GitHub Actions workflows in `.github/workflows/`:

| Workflow      | Trigger             | What it does                                   |
|---------------|---------------------|------------------------------------------------|
| Backend CI    | push/PR → main      | flake8 + pytest with 70% coverage gate         |
| Frontend CI   | push/PR (frontend/) | type-check + production build                  |
| Security Scan | push/PR + weekly    | bandit, pip-audit, Trivy image scan            |
| Docker Build  | push/PR/tags        | builds images, smoke-tests `/`, pushes to GHCR |

## 7. Load testing

Locust scenarios in `loadtests/locustfile.py`:

```bash
pip install -r loadtests/requirements.txt
locust -f loadtests/locustfile.py --host http://localhost:8000   # web UI at :8089
# or headless, 100 users:
locust -f loadtests/locustfile.py --host http://localhost:8000 --headless -u 100 -r 10 -t 5m
```

Watch `ghost_qa_request_latency_seconds` in Grafana while the test runs.

## 8. Security audit

```powershell
pip install -r requirements-dev.txt
.\scripts\security_scan.ps1     # bandit + pip-audit locally
```

Pre-production checklist:
- [ ] `SECRET_KEY` is a long random value (e.g. `openssl rand -hex 32`)
- [ ] Bootstrap admin password changed after first login
- [ ] `CORS_ORIGINS` locked to the real frontend origin
- [ ] `/metrics` not reachable from the public internet
- [ ] TLS termination in place; `AUTO_APPROVE=false` in production
- [ ] Backups scheduled and a restore tested
- [ ] pip-audit/Trivy findings reviewed

## 9. Rollback

- **Compose:** pin image tags and redeploy the previous tag; migrations are additive —
  only roll back code unless a migration must be reversed (`alembic downgrade -1`).
- **Kubernetes:** `kubectl rollout undo deployment/ghost-qa -n ghost-qa`.
