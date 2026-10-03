from datetime import datetime, timezone
from typing import Any

from src.agent_runtime.agent import Agent


class SecurityAgent(Agent):
    """
    Performs basic authorization checks for agent capabilities.

    This is intentionally simple for v0.1.
    The full capability/permission layer is implemented later.
    """

    def __init__(
        self,
        agent_id: str = "security-agent",
    ):
        super().__init__(
            agent_id=agent_id,
            name="Security Agent",
            agent_type="core",
            capabilities=[
                "authorize",
                "check_permission",
            ],
        )

        self.permissions: dict[str, set[str]] = {}

    def grant(
        self,
        agent_id: str,
        capability: str,
    ) -> None:
        self.permissions.setdefault(
            agent_id,
            set(),
        ).add(capability)

    def authorize(
        self,
        agent_id: str,
        capability: str,
    ) -> dict[str, Any]:
        allowed = capability in self.permissions.get(
            agent_id,
            set(),
        )

        return {
            "authorized": allowed,
            "agent_id": agent_id,
            "capability": capability,
        }

    def receive_message(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        self.received_messages.append(message)

        payload = message.get("payload", {})
        operation = payload.get("operation")

        if operation == "AUTHORIZE":
            result = self.authorize(
                agent_id=payload.get("agent_id", ""),
                capability=payload.get(
                    "capability",
                    "",
                ),
            )

        else:
            result = {
                "authorized": False,
                "error": "Unsupported security operation.",
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