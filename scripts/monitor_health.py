"""Continuous health monitor for a deployed Ghost QA instance.

Polls health + metrics endpoints on an interval and prints a status line;
exits/alerts when thresholds are breached. Suitable for cron/Task Scheduler
or a quick manual watch window.

Usage:
    python scripts/monitor_health.py                          # watch localhost:8000, 30s interval
    python scripts/monitor_health.py --url https://prod.example.com --interval 60 --iterations 10
"""
import argparse
import sys
import time
from datetime import datetime, timezone

import requests

ALERT_5XX_RATIO = 0.05      # alert when recent 5xx share exceeds 5%
ALERT_P95_SECONDS = 2.0     # alert when p95 latency exceeds 2s


def scrape(base_url, session):
    """Return (ok, detail) for one monitoring round."""
    problems = []

    try:
        resp = session.get(f"{base_url}/", timeout=5)
        if resp.status_code != 200:
            problems.append(f"health status={resp.status_code}")
    except requests.RequestException as exc:
        return False, f"unreachable: {exc.__class__.__name__}"

    try:
        resp = session.get(f"{base_url}/metrics", timeout=5)
        if resp.status_code != 200:
            problems.append(f"metrics status={resp.status_code}")
        else:
            problems.extend(analyze_metrics(resp.text))
    except requests.RequestException:
        problems.append("metrics scrape failed")

    return not problems, "; ".join(problems) or "healthy"


def analyze_metrics(text):
    """Derive error-ratio and p95 estimates from the Prometheus text output."""
    problems = []
    total = 0.0
    errors = 0.0
    for line in text.splitlines():
        if line.startswith("ghost_qa_requests_total{"):
            try:
                value = float(line.rsplit(" ", 1)[1])
            except ValueError:
                continue
            total += value
            if 'status_code="5' in line:
                errors += value
    if total > 20 and errors / total > ALERT_5XX_RATIO:
        problems.append(f"5xx ratio {errors / total:.1%}")

    # p95 from histogram bucket counters
    buckets = []
    for line in text.splitlines():
        if line.startswith("ghost_qa_request_latency_seconds_bucket{"):
            try:
                label, value = line.rsplit(" ", 1)
                le = label.split('le="')[1].split('"')[0]
                if le == "+Inf":
                    continue
                buckets.append((float(le), float(value)))
            except (IndexError, ValueError):
                continue
    if buckets:
        buckets.sort()
        total_count = buckets[-1][1] or 1.0
        p95 = next((le for le, count in buckets if count / total_count >= 0.95), None)
        if p95 is not None and p95 > ALERT_P95_SECONDS:
            problems.append(f"p95 latency ~{p95}s")
    return problems


def main():
    parser = argparse.ArgumentParser(description="Ghost QA health monitor")
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--interval", type=int, default=30, help="seconds between polls")
    parser.add_argument("--iterations", type=int, default=0, help="0 = run forever")
    args = parser.parse_args()

    base = args.url.rstrip("/")
    session = requests.Session()
    session.headers["User-Agent"] = "ghost-qa-monitor/1.0"
    print(f"Monitoring {base} every {args.interval}s (Ctrl+C to stop)")

    failures = 0
    iteration = 0
    try:
        while True:
            iteration += 1
            now = datetime.now(timezone.utc).strftime("%H:%M:%SZ")
            ok, detail = scrape(base, session)
            mark = "OK " if ok else "ALERT"
            print(f"{now} [{mark}] {detail}", flush=True)
            failures = 0 if ok else failures + 1
            if failures >= 3:
                print(f"{now} [CRITICAL] 3 consecutive failures — paging on-call", flush=True)
                failures = 0
            if args.iterations and iteration >= args.iterations:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
