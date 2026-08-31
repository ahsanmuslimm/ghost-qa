# Ghost QA — Production Release Runbook

Step-by-step procedure for promoting a verified build from staging to production.

## Pre-flight (T-1 day)

1. Staging smoke suite green:
   `python scripts/smoke_test_deploy.py --url <staging-url>`
2. UAT checklist signed off (`docs/uat-checklist.md`)
3. Production checklist from `docs/deployment-guide.md` section 8 complete
4. Database backup taken and restore tested
5. Release tag cut: `git tag v<version> && git push origin v<version>`

## Deploy (T=0)

### Docker Compose target
```bash
git pull && git checkout v<version>
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d      # rolling restart
docker compose -f docker-compose.prod.yml ps          # all healthy?
```

### Kubernetes target
```bash
kubectl -n ghost-qa set image deployment/ghost-qa \
    api=ghcr.io/<org>/ghost-qa-backend:v<version>
kubectl -n ghost-qa rollout status deployment/ghost-qa --timeout=180s
```

## Verify (T+5 min)

1. Smoke suite against production:
   `python scripts/smoke_test_deploy.py --url <prod-url> --password <prod-admin-pw>`
2. Grafana: request rate resuming, error % near zero, p95 under 2s
3. Watch window: `python scripts/monitor_health.py --url <prod-url> --interval 30`
4. Trigger one real webhook from a test repo; confirm the run completes

## Roll back (if any verify step fails)

- **Compose:** `docker compose -f docker-compose.prod.yml up -d` with the previous
  image tag restored in `.env`/compose override; migrations are additive so code-only
  rollback is usually safe.
- **Kubernetes:** `kubectl -n ghost-qa rollout undo deployment/ghost-qa`

## Post-deploy (first 48h)

- Keep `monitor_health.py` or Prometheus alerts under active watch
- Check alert rules firing: HighErrorRate, HighLatencyP95, InstanceDown
- Triage any 401 spikes (token expiry config) or webhook signature failures
- Record outcomes in `docs/release-notes.md`
