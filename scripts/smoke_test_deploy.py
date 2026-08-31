"""Deployment smoke test — verifies a deployed Ghost QA instance end to end.

Usage:
    python scripts/smoke_test_deploy.py                       # http://localhost:8000
    python scripts/smoke_test_deploy.py --url https://staging.example.com
    python scripts/smoke_test_deploy.py --email admin@ghost.qa --password Admin123!

Exits non-zero if any check fails (CI/deploy-gate friendly).
"""
import argparse
import sys
import time

import requests

PASS = "[PASS]"
FAIL = "[FAIL]"

SECURITY_HEADERS = (
    "X-Content-Type-Options",
    "X-Frame-Options",
)


class SmokeReport:
    def __init__(self):
        self.results = []

    def check(self, name, ok, detail=""):
        self.results.append(ok)
        print(f"{PASS if ok else FAIL} {name}" + (f" — {detail}" if detail else ""))
        return ok

    @property
    def ok(self):
        return all(self.results)


def run(base_url, email, password):
    s = requests.Session()
    s.headers["User-Agent"] = "ghost-qa-smoke/1.0"
    r = SmokeReport()
    t0 = time.time()

    # 1. Health endpoint
    try:
        resp = s.get(f"{base_url}/", timeout=10)
        body = resp.json() if resp.ok else {}
        r.check(
            "health endpoint",
            resp.status_code == 200 and "status" in body,
            f"status={resp.status_code} env={body.get('app_env')}",
        )
        r.check(
            "security headers present",
            all(h in resp.headers for h in SECURITY_HEADERS),
            ", ".join(h for h in SECURITY_HEADERS if h in resp.headers) or "none",
        )
    except Exception as exc:
        r.check("health endpoint", False, str(exc))
        print("\nInstance unreachable — aborting remaining checks.")
        return r

    # 2. Authentication
    token = None
    resp = s.post(
        f"{base_url}/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    if r.check("login", resp.status_code == 200, f"status={resp.status_code}"):
        token = resp.json().get("token")
        r.check("login returns JWT", bool(token))

    resp = s.post(
        f"{base_url}/auth/login",
        json={"email": email, "password": "wrong-password"},
        timeout=10,
    )
    r.check("bad password rejected", resp.status_code in (401, 403))

    if not token:
        print("\nNo token — skipping authenticated checks.")
        return r
    s.headers["Authorization"] = f"Bearer {token}"

    # 3. Auth enforcement
    anon = requests.get(f"{base_url}/api/runs", timeout=10)
    r.check("unauthenticated /api/runs rejected", anon.status_code == 401)

    # 4. Core read APIs
    for path, name in (
        ("/api/dashboard/overview", "dashboard overview"),
        ("/api/runs?page=1&page_size=5", "pipeline runs list"),
        ("/api/users", "users list (admin)"),
    ):
        resp = s.get(f"{base_url}{path}", timeout=15)
        r.check(name, resp.status_code == 200, f"status={resp.status_code}")

    # 5. Metrics endpoint (monitoring)
    resp = s.get(f"{base_url}/metrics", timeout=10)
    r.check(
        "prometheus /metrics",
        resp.status_code == 200 and "ghost_qa_requests_total" in resp.text,
    )

    # 6. Webhook intake (demo-safe payload; no signature required in demo mode)
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 99999,
            "title": "smoke test PR",
            "html_url": f"{base_url}/smoke",
            "head": {"sha": "smoke" * 10},
            "user": {"login": "smoke-bot"},
        },
        "repository": {"full_name": "ghost-qa/smoke", "name": "smoke"},
        "sender": {"login": "smoke-bot"},
    }
    resp = s.post(
        f"{base_url}/api/webhooks/github",
        json=payload,
        headers={"X-GitHub-Event": "pull_request"},
        timeout=30,
    )
    r.check(
        "webhook intake",
        resp.status_code in (200, 202),
        f"status={resp.status_code}",
    )

    # 7. Pipeline created from the smoke webhook
    time.sleep(2)
    resp = s.get(f"{base_url}/api/runs?page=1&page_size=20", timeout=15)
    runs = resp.json().get("runs", []) if resp.ok else []
    smoke_run = next((x for x in runs if x.get("pr_number") == 99999), None)
    r.check(
        "pipeline run created for smoke PR",
        smoke_run is not None,
        f"status={smoke_run.get('status')}" if smoke_run else "not found",
    )

    print(f"\nCompleted in {time.time() - t0:.1f}s")
    return r


def main():
    parser = argparse.ArgumentParser(description="Ghost QA deployment smoke test")
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--email", default="admin@ghost.qa")
    parser.add_argument("--password", default="Admin123!")
    args = parser.parse_args()

    print(f"Smoke-testing {args.url}\n" + "-" * 50)
    report = run(args.url.rstrip("/"), args.email, args.password)
    print("-" * 50)
    passed = sum(report.results)
    print(f"Result: {passed}/{len(report.results)} checks passed")
    sys.exit(0 if report.ok else 1)


if __name__ == "__main__":
    main()
