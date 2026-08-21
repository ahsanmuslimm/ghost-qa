import logging
import requests
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class SlackService:
    def __init__(self):
        self.token = settings.SLACK_BOT_TOKEN
        self.channel = settings.SLACK_CHANNEL
        self.demo_mode = settings.DEMO_MODE
        self.enabled = bool(self.token) and not self.demo_mode

    def send_notification(self, title: str, message: str, color: str = "#36a64f") -> Optional[Dict[str, Any]]:
        """Send a Slack notification with the test result summary."""
        if not self.enabled:
            logger.info(f"[DEMO] Slack notification: {title} - {message}")
            return {"demo": True, "title": title, "message": message}

        try:
            payload = {
                "channel": self.channel,
                "username": "Ghost QA",
                "icon_emoji": ":ghost:",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"👻 {title}"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    }
                ]
            }

            response = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return None

    def send_run_summary(self, report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a pipeline run summary to Slack."""
        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(
            report.get("risk_level", "low"), "⚪"
        )
        message = (
            f"*Repository:* `{report.get('repository', 'unknown')}`\n"
            f"*PR:* #{report.get('pr_number', 'N/A')}\n"
            f"*Total Tests:* {report.get('total_tests', 0)}\n"
            f"*Passed:* {report.get('passed', 0)} | "
            f"*Failed:* {report.get('failed', 0)}\n"
            f"*Risk:* {risk_emoji} **{report.get('risk_level', 'unknown').upper()}**\n"
            f"*Recommendation:* {report.get('recommendation', 'N/A')}"
        )
        return self.send_notification(
            "Pipeline Complete",
            message,
            color={"low": "#36a64f", "medium": "#f2c748", "high": "#ff6b6b", "critical": "#c92a2a"}.get(
                report.get("risk_level", "low"), "#36a64f"
            )
        )
