#!/usr/bin/env python3
"""Send the bundled sample GitHub webhook payload to a running Ghost QA server.

Works in both modes:
  - Demo Mode: the pipeline runs entirely on fixtures — no credentials needed.
  - Live Mode: payload is signed with GITHUB_WEBHOOK_SECRET exactly like GitHub.

Usage:
    python scripts/send_sample_webhook.py [--url http://127.0.0.1:8000]
                                          [--payload scripts/sample_webhook_payload.json]
"""
import argparse
import hashlib
import hmac
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests  # noqa: E402

from app.config import settings  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--payload",
                    default=str(Path(__file__).parent / "sample_webhook_payload.json"))
    args = ap.parse_args()

    health = requests.get(f"{args.url}/", timeout=10).json()
    print(f"server mode: demo_mode={health.get('demo_mode')} "
          f"execution_backend={health.get('execution_backend')}")

    body = Path(args.payload).read_bytes()
    headers = {"Content-Type": "application/json", "X-GitHub-Event": "pull_request"}
    if settings.GITHUB_WEBHOOK_SECRET:
        sig = hmac.new(settings.GITHUB_WEBHOOK_SECRET.encode(), body,
                       hashlib.sha256).hexdigest()
        headers["X-Hub-Signature-256"] = f"sha256={sig}"

    resp = requests.post(f"{args.url}/api/webhooks/github",
                         data=body, headers=headers, timeout=180)
    print(f"webhook: HTTP {resp.status_code} {resp.json()}")
    if resp.status_code != 200:
        return 1

    run_id = resp.json().get("pipeline_run_id")
    if run_id:
        print(f"track it:  {args.url}/api/runs/{run_id}")
        print(f"report:    {args.url}/report/{run_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
