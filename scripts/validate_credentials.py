#!/usr/bin/env python3
"""Live credential validation — proves Ghost QA works WITHOUT demo mode.

Runs real (billable/visible) calls against each configured external service
and prints a PASS/FAIL table. Secrets are never printed in full.

Usage:
    python scripts/validate_credentials.py
Exit code 0 = every configured integration answered successfully.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests  # noqa: E402

from app.config import settings  # noqa: E402

RESULTS = []


def mask(value: str) -> str:
    if not value:
        return "<empty>"
    return f"{value[:6]}…{value[-2:]}" if len(value) > 12 else f"{value[:2]}…"


def record(name: str, ok: bool, detail: str, secs: float):
    RESULTS.append((name, ok, detail, secs))
    print(f"[{'PASS' if ok else 'FAIL'}] {name:<22} {detail}  ({secs:.1f}s)")


def check_config() -> bool:
    t0 = time.time()
    keys = {
        "GEMINI_API_KEY": settings.GEMINI_API_KEY,
        "XAI_API_KEY": settings.XAI_API_KEY,
        "ANTHROPIC_API_KEY": settings.ANTHROPIC_API_KEY,
        "UIPATH_CLIENT_ID": settings.UIPATH_CLIENT_ID,
        "UIPATH_CLIENT_SECRET": settings.UIPATH_CLIENT_SECRET,
        "SLACK_BOT_TOKEN": settings.SLACK_BOT_TOKEN,
        "GITHUB_TOKEN": settings.GITHUB_TOKEN,
        "GITHUB_WEBHOOK_SECRET": settings.GITHUB_WEBHOOK_SECRET,
    }
    present = {k: mask(v) for k, v in keys.items() if v}
    missing = [k for k, v in keys.items() if not v]
    ok = settings.DEMO_MODE is False
    detail = (
        f"DEMO_MODE={settings.DEMO_MODE} AI_PROVIDER={settings.AI_PROVIDER} "
        f"set={list(present)} missing={missing or 'none'}"
    )
    record("config", ok, detail, time.time() - t0)
    return ok


def check_ai() -> bool:
    from app.services import ai_service

    t0 = time.time()
    try:
        resp = ai_service.generate_tests(
            pr_title="Credential validation probe",
            pr_body="Verify live AI test generation works.",
            diff="diff --git a/app/auth.py b/app/auth.py\n+def login(user, pw): return token",
            changed_files=["app/auth.py"],
        )
        tests = getattr(resp, "test_cases", None) or getattr(resp, "tests", []) or []
        names = [getattr(t, "title", None) or getattr(t, "name", "") for t in tests]
        ok = len(tests) > 0
        detail = f"provider={ai_service.provider} tests={len(tests)} first={names[0] if names else '-'}"
    except Exception as e:  # noqa: BLE001
        ok, detail = False, f"provider={ai_service.provider} error={type(e).__name__}: {e}"
    record("ai-generation", ok, detail, time.time() - t0)
    return ok


def check_uipath() -> bool:
    t0 = time.time()
    try:
        auth_url = settings.UIPATH_AUTH_URL or (
            f"{settings.UIPATH_TEST_MANAGER_BASE}/{settings.UIPATH_ORG_ID}/identity_/connect/token"
        )
        resp = requests.post(
            auth_url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.UIPATH_CLIENT_ID,
                "client_secret": settings.UIPATH_CLIENT_SECRET,
                "scope": settings.UIPATH_TOKEN_SCOPE,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=20,
            allow_redirects=False,
        )
        if resp.status_code != 200 or "access_token" not in resp.json():
            record("uipath-auth", False, f"token endpoint HTTP {resp.status_code} ({auth_url})", time.time() - t0)
            return False
        token = resp.json()["access_token"]
        base = f"{settings.UIPATH_TEST_MANAGER_BASE}/{settings.UIPATH_ORG_ID}/{settings.UIPATH_TENANT_NAME}"
        folders = requests.get(
            f"{base}/orchestrator_/odata/Folders?$top=50",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=20,
        )
        names = [f.get("DisplayName") or f.get("Name") for f in folders.json().get("value", [])] if folders.status_code == 200 else []
        note = "" if folders.status_code == 200 else (
            " (token OK; folders scope missing — informational)" if folders.status_code == 403
            else f" (folders HTTP {folders.status_code})"
        )
        detail = f"token={mask(token)} folders={names[:5] or folders.status_code}{note}"
        ok = True
    except Exception as e:  # noqa: BLE001
        ok, detail = False, f"error={type(e).__name__}: {e}"
    record("uipath-auth", ok, detail, time.time() - t0)
    return ok


def check_slack() -> bool:
    from app.services import slack_service

    t0 = time.time()
    if not slack_service.enabled:
        record("slack", False, "service disabled (token missing or DEMO_MODE on)", time.time() - t0)
        return False
    result = slack_service.send_notification(
        "Credential validation", "Live (non-demo) Slack delivery check from Ghost QA."
    )
    ok = bool(result) and result.get("ok", True) is not False
    record("slack", ok, f"channel={settings.SLACK_CHANNEL} api_ok={bool(result)}", time.time() - t0)
    return ok


def check_github() -> bool:
    t0 = time.time()
    try:
        resp = requests.get(
            f"{settings.GITHUB_API_BASE}/user",
            headers={"Authorization": f"Bearer {settings.GITHUB_TOKEN}", "Accept": "application/vnd.github+json"},
            timeout=15,
        )
        ok = resp.status_code == 200
        detail = f"login={resp.json().get('login') if ok else resp.status_code}"
    except Exception as e:  # noqa: BLE001
        ok, detail = False, f"error={type(e).__name__}: {e}"
    record("github-token", ok, detail, time.time() - t0)
    return ok


def main() -> int:
    print("=" * 72)
    print("Ghost QA live credential validation (DEMO_MODE must be false)")
    print("=" * 72)
    oks = [check_config()]
    if oks[0]:
        oks.append(check_ai())
        oks.append(check_uipath())
        oks.append(check_slack())
        oks.append(check_github())
    failed = [name for name, ok, _, _ in RESULTS if not ok]
    print("-" * 72)
    print(f"{len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed"
          + (f" — FAILED: {failed}" if failed else " — all live integrations operational"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
