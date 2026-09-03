#!/usr/bin/env python3
"""Fire a signed GitHub webhook for a REAL pull request and wait for the
pipeline run to reach a terminal state — the end-to-end live proof.

Usage:
    python scripts/live_pipeline_probe.py --owner ahsanmuslimm --repo ghost-qa --pr 12
Exits 0 when the run completes (status printed), 1 on timeout/intake failure.
"""
import argparse
import hashlib
import hmac
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests  # noqa: E402

from app.config import settings  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8100")
    ap.add_argument("--owner", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    gh = {"Authorization": f"Bearer {settings.GITHUB_TOKEN}",
          "Accept": "application/vnd.github+json"}
    pr = requests.get(
        f"{settings.GITHUB_API_BASE}/repos/{args.owner}/{args.repo}/pulls/{args.pr}",
        headers=gh, timeout=20).json()
    payload = {
        "action": "opened",
        "repository": {
            "id": pr["base"]["repo"]["id"],
            "name": args.repo,
            "full_name": f"{args.owner}/{args.repo}",
            "owner": {"login": args.owner},
            "default_branch": pr["base"]["repo"]["default_branch"],
        },
        "pull_request": {
            "number": pr["number"],
            "title": pr["title"],
            "body": pr.get("body") or "",
            "state": pr["state"],
            "head": {"sha": pr["head"]["sha"], "ref": pr["head"]["ref"]},
            "base": {"sha": pr["base"]["sha"], "ref": pr["base"]["ref"]},
            "changed_files": pr.get("changed_files", 1),
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0),
            "diff_url": pr.get("diff_url"),
            "patch_url": pr.get("patch_url"),
            "html_url": pr["html_url"],
        },
        "sender": {"login": pr["user"]["login"]},
    }
    body = json.dumps(payload).encode("utf-8")
    sig = "sha256=" + hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

    resp = requests.post(
        f"{args.url}/api/webhooks/github", data=body,
        headers={"Content-Type": "application/json",
                 "X-GitHub-Event": "pull_request",
                 "X-Hub-Signature-256": sig}, timeout=180)  # pipeline runs inline
    print(f"webhook intake: HTTP {resp.status_code} {resp.json()}")
    if resp.status_code != 200:
        return 1

    login = requests.post(
        f"{args.url}/auth/login",
        json={"email": "admin@ghost.qa", "password": settings.ADMIN_DEFAULT_PASSWORD},
        timeout=15).json()
    auth = {"Authorization": f"Bearer {login['token']}"}

    deadline = time.time() + args.timeout
    run = None
    while time.time() < deadline:
        runs = requests.get(
            f"{args.url}/api/runs/?page=1&page_size=20", headers=auth, timeout=15).json()
        for r in runs.get("runs", []):
            if r.get("pr_number") == args.pr and r.get("repository", "").endswith(args.repo):
                run = r
                break
        if run and run.get("status") in ("completed", "failed"):
            break
        time.sleep(5)

    if not run:
        print("TIMEOUT: no run record found")
        return 1
    print(json.dumps({k: run.get(k) for k in (
        "id", "status", "total_tests", "passed", "failed",
        "risk_level", "recommendation")}, indent=2, default=str))
    if run.get("status") not in ("completed", "failed"):
        print(f"TIMEOUT: run still {run.get('status')}")
        return 1
    print(f"run reached terminal state: {run.get('status')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
