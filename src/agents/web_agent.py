import webbrowser
from typing import Any

from src.agent_runtime.agent import Agent


class WebAgent(Agent):
    """
    AgenticOS Web Agent.

    Provides controlled browser operations.
    """

    def __init__(
        self,
        agent_id: str = "web-agent",
        name: str = "Web Agent",
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            version="0.1.0",
            agent_type="specialized",
            capabilities=[
                "open_url",
                "open_browser",
            ],
        )

    def open_url(
        self,
        url: str,
    ) -> dict[str, Any]:
        if not isinstance(url, str) or not url.strip():
            raise ValueError(
                "URL must be a non-empty string."
            )

        normalized_url = url.strip()

        opened = webbrowser.open(
            normalized_url
        )

        return {
            "status": "opened" if opened else "requested",
            "url": normalized_url,
            "browser_opened": bool(opened),
        }

    def receive_message(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        self.received_messages.append(message)

        payload = message.get(
            "payload",
            {},
        )

        operation = (
            payload.get("operation")
            or message.get("operation")
        )

        try:
            if operation in {
                "OPEN_URL",
                "OPEN_BROWSER",
            }:
                url = (
                    payload.get("url")
                    or message.get("url")
                )

                if url is None:
                    raise ValueError(
                        "OPEN_URL requires 'url'."
                    )

                result = self.open_url(
                    url
                )

            else:
                raise ValueError(
                    f"Unknown web operation: {operation}"
                )

            return {
                "message_id": message.get(
                    "message_id"
                ),
                "request_id": message.get(
                    "request_id"
                ),
                "sender": self.agent_id,
                "receiver": message.get(
                    "sender"
                ),
                "message_type": "RESPONSE",
                "timestamp": message.get(
                    "timestamp"
                ),
                "payload": result,
            }

        except ValueError as error:
            return {
                "message_id": message.get(
                    "message_id"
                ),
                "request_id": message.get(
                    "request_id"
                ),
                "sender": self.agent_id,
                "receiver": message.get(
                    "sender"
                ),
                "message_type": "ERROR",
                "timestamp": message.get(
                    "timestamp"
                ),
                "payload": {
                    "status": "error",
                    "error_type": type(error).__name__,
                    "error": str(error),
                },
            }