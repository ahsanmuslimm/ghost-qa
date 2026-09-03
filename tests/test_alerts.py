import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import slack_service

SECRET = "test-am-secret"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "ALERTMANAGER_WEBHOOK_SECRET", SECRET)
    with TestClient(app) as c:
        yield c


def _payload(status="firing", severity="critical", count=1):
    return {
        "version": "4",
        "status": status,
        "alerts": [
            {
                "status": status,
                "labels": {"alertname": f"HighErrorRate{i}", "severity": severity},
                "annotations": {
                    "summary": "Ghost QA 5xx error rate above 5%",
                    "description": "More than 5% of requests are failing.",
                },
                "startsAt": "2026-09-03T00:00:00Z",
                "generatorURL": "http://prometheus:9090/graph",
            }
            for i in range(count)
        ],
    }


def _headers():
    return {"Authorization": f"Bearer {SECRET}"}


def test_unconfigured_secret_disables_endpoint(client, monkeypatch):
    monkeypatch.setattr(settings, "ALERTMANAGER_WEBHOOK_SECRET", "")
    resp = client.post("/alertmanager/webhook", json=_payload())
    assert resp.status_code == 503


def test_wrong_secret_rejected(client):
    resp = client.post(
        "/alertmanager/webhook",
        json=_payload(),
        headers={"Authorization": "Bearer nope"},
    )
    assert resp.status_code == 401


def test_missing_auth_header_rejected(client):
    resp = client.post("/alertmanager/webhook", json=_payload())
    assert resp.status_code == 401


def test_relays_firing_alert_to_slack(client, monkeypatch):
    sent = []
    monkeypatch.setattr(
        slack_service,
        "send_notification",
        lambda title, message, color="#000000": sent.append((title, message, color)),
    )
    resp = client.post("/alertmanager/webhook", json=_payload(), headers=_headers())
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "delivered": 1}

    title, message, color = sent[0]
    assert "firing" in title.lower()
    assert "HighErrorRate0" in message
    assert "5xx error rate" in message
    assert color == "#c92a2a"  # critical


def test_resolved_alerts_use_resolved_title(client, monkeypatch):
    sent = []
    monkeypatch.setattr(
        slack_service,
        "send_notification",
        lambda title, message, color="#000000": sent.append((title, message, color)),
    )
    resp = client.post(
        "/alertmanager/webhook", json=_payload(status="resolved"), headers=_headers()
    )
    assert resp.status_code == 200
    assert "resolved" in sent[0][0].lower()
    assert "✅" in sent[0][1]


def test_warning_severity_color(client, monkeypatch):
    sent = []
    monkeypatch.setattr(
        slack_service,
        "send_notification",
        lambda title, message, color="#000000": sent.append((title, message, color)),
    )
    resp = client.post(
        "/alertmanager/webhook",
        json=_payload(severity="warning"),
        headers=_headers(),
    )
    assert resp.status_code == 200
    assert sent[0][2] == "#f2c748"


def test_empty_alert_list_is_acked(client, monkeypatch):
    monkeypatch.setattr(
        slack_service, "send_notification", lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not send"))
    )
    resp = client.post(
        "/alertmanager/webhook",
        json={"version": "4", "status": "firing", "alerts": []},
        headers=_headers(),
    )
    assert resp.status_code == 200
    assert resp.json()["delivered"] == 0


def test_large_groups_are_truncated(client, monkeypatch):
    sent = []
    monkeypatch.setattr(
        slack_service,
        "send_notification",
        lambda title, message, color="#000000": sent.append((title, message, color)),
    )
    resp = client.post(
        "/alertmanager/webhook", json=_payload(count=8), headers=_headers()
    )
    assert resp.status_code == 200
    assert resp.json()["delivered"] == 8
    assert "3 more" in sent[0][1]


def test_invalid_json_rejected(client):
    resp = client.post(
        "/alertmanager/webhook",
        content=b"{not json",
        headers={"Content-Type": "application/json", **_headers()},
    )
    assert resp.status_code == 400
