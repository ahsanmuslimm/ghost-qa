"""Locust load test for the Ghost QA API.

Run against a local instance:
    locust -f loadtests/locustfile.py --host http://localhost:8000

Headless example (100 users, spawn 10/s, run 5 minutes):
    locust -f loadtests/locustfile.py --host http://localhost:8000 \
        --headless -u 100 -r 10 -t 5m

Credentials come from the environment (defaults match the seeded admin).
"""
import os

from locust import HttpUser, between, task

EMAIL = os.environ.get("GHOSTQA_EMAIL", "admin@ghost.qa")
PASSWORD = os.environ.get("GHOSTQA_PASSWORD", "Admin123!")


class GhostQAUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Authenticate once per simulated user."""
        resp = self.client.post(
            "/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
            name="/auth/login",
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Login failed: {resp.status_code} {resp.text}")
        token = resp.json()["token"]
        self.client.headers["Authorization"] = f"Bearer {token}"

    @task(5)
    def dashboard_overview(self):
        self.client.get("/api/dashboard/overview", name="/api/dashboard/overview")

    @task(3)
    def list_runs(self):
        self.client.get("/api/runs?page=1&page_size=20", name="/api/runs")

    @task(2)
    def list_heals(self):
        self.client.get("/api/heals", name="/api/heals")

    @task(1)
    def run_report(self):
        """Fetch the run list, then open the report of the first run."""
        resp = self.client.get("/api/runs?page=1&page_size=1", name="/api/runs")
        runs = resp.json().get("runs") if resp.status_code == 200 else None
        if runs:
            self.client.get(
                f"/api/runs/{runs[0]['id']}/report",
                name="/api/runs/{id}/report",
            )

    @task(1)
    def health(self):
        self.client.get("/", name="/ (health)")
