from datetime import datetime, timezone
from typing import Any
import webbrowser

from src.agent_runtime.agent import Agent


class ApplicationAgent(Agent):
    """
    Handles application-level actions.

    v0.1 provides a browser launch capability.
    Additional application integrations can be added later.
    """

    def __init__(
        self,
        agent_id: str = "application-agent",
    ):
        super().__init__(
            agent_id=agent_id,
            name="Application Agent",
            agent_type="specialized",
            capabilities=[
                "open_browser",
                "launch_application",
            ],
        )

    def open_browser(
        self,
        url: str = "about:blank",
    ) -> dict[str, Any]:
        if not url:
            raise ValueError("Browser URL is required.")

        opened = webbrowser.open(url)

        return {
            "status": "completed" if opened else "failed",
            "action": "open_browser",
            "url": url,
            "opened": opened,
        }

    def launch_application(
        self,
        application: str,
    ) -> dict[str, Any]:
        if not application.strip():
            raise ValueError(
                "Application name is required."
            )

        if application.lower() in {
            "browser",
            "web browser",
            "webbrowser",
        }:
            return self.open_browser()

        return {
            "status": "unsupported",
            "application": application,
        }

    def receive_message(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        self.received_messages.append(message)

        payload = message.get("payload", {})
        operation = payload.get("operation")

        if operation == "OPEN_BROWSER":
            result = self.open_browser(
                url=payload.get(
                    "url",
                    "about:blank",
                )
            )

        elif operation == "LAUNCH_APPLICATION":
            result = self.launch_application(
                application=payload.get(
                    "application",
                    "",
                )
            )

        else:
            result = {
                "status": "unsupported_operation",
                "operation": operation,
            }

        return {
            "message_id": message.get("message_id"),
            "request_id": message.get("request_id"),
            "sender": self.agent_id,
            "receiver": message.get("sender"),
            "message_type": "RESPONSE",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "payload": result,
        }