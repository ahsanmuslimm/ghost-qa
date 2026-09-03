"""Alertmanager webhook receiver.

Prometheus alert rules fire into Alertmanager, which forwards them here;
this endpoint formats them and delivers via the existing Slack service
(reuses SLACK_BOT_TOKEN — no extra Slack app provisioning needed).

Mounted at /alertmanager (outside /api, so no JWT); protected instead by a
shared bearer secret configured via ALERTMANAGER_WEBHOOK_SECRET, which
Alertmanager presents from a credentials file (compose/k8s secret).
"""
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.services import slack_service

logger = logging.getLogger(__name__)
router = APIRouter()

_SEVERITY_COLORS = {
    "critical": "#c92a2a",
    "high": "#ff6b6b",
    "warning": "#f2c748",
    "info": "#36a64f",
}


def _format_alert(alert: dict) -> str:
    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})
    status = alert.get("status", "firing")
    icon = "✅" if status == "resolved" else "🚨"
    lines = [
        f"{icon} *{labels.get('alertname', 'UnknownAlert')}* "
        f"({labels.get('severity', 'unknown')}) — {status.upper()}",
    ]
    if annotations.get("summary"):
        lines.append(f"*Summary:* {annotations['summary']}")
    if annotations.get("description"):
        lines.append(f"{annotations['description']}")
    if alert.get("generatorURL"):
        lines.append(f"<{alert['generatorURL']}|Prometheus rule>")
    if alert.get("startsAt"):
        lines.append(f"*Started:* {alert['startsAt']}")
    return "\n".join(lines)


@router.post("/webhook")
async def alertmanager_webhook(request: Request):
    """Receive an Alertmanager notification and relay it to Slack."""
    if not settings.ALERTMANAGER_WEBHOOK_SECRET:
        return JSONResponse(
            {"detail": "ALERTMANAGER_WEBHOOK_SECRET not configured"},
            status_code=503,
        )

    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {settings.ALERTMANAGER_WEBHOOK_SECRET}":
        return JSONResponse({"detail": "Invalid alertmanager secret"}, status_code=401)

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"detail": "Invalid JSON payload"}, status_code=400)

    alerts = payload.get("alerts", [])
    if not alerts:
        return {"status": "ok", "delivered": 0}

    worst = "info"
    for alert in alerts:
        severity = alert.get("labels", {}).get("severity", "info")
        if severity in ("critical", "high"):
            worst = severity
            break
        if severity == "warning":
            worst = "warning"

    status = payload.get("status", "firing")
    title = (
        f"Alerts resolved ({len(alerts)})" if status == "resolved"
        else f"Alerts firing ({len(alerts)})"
    )
    message = "\n\n".join(_format_alert(a) for a in alerts[:5])
    if len(alerts) > 5:
        message += f"\n\n_…and {len(alerts) - 5} more_"

    slack_service.send_notification(
        title, message, color=_SEVERITY_COLORS.get(worst, "#f2c748")
    )
    logger.info(f"Relayed {len(alerts)} alertmanager notification(s) to Slack")
    return {"status": "ok", "delivered": len(alerts)}
