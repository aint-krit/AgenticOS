from datetime import datetime, timezone
from typing import Any


class Agent:
    """
    Base Agent Runtime.

    Provides:
    - Agent identity
    - Agent status
    - Capability declaration
    - Message receiving
    - Basic lifecycle management
    """

    VALID_STATUSES = {
        "starting",
        "active",
        "busy",
        "paused",
        "unhealthy",
        "stopped",
    }

    def __init__(
        self,
        agent_id: str,
        name: str,
        version: str = "0.1.0",
        agent_type: str = "specialized",
        capabilities: list[str] | None = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.version = version
        self.agent_type = agent_type
        self.capabilities = capabilities or []

        self.status = "starting"
        self.received_messages: list[dict[str, Any]] = []

    def start(self) -> None:
        """Start the agent."""
        self.status = "active"

    def stop(self) -> None:
        """Stop the agent."""
        self.status = "stopped"

    def pause(self) -> None:
        """Pause the agent."""
        self.status = "paused"

    def resume(self) -> None:
        """Resume the agent."""
        self.status = "active"

    def get_registration(self) -> dict[str, Any]:
        """Return the agent registration structure."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "type": self.agent_type,
            "status": self.status,
            "capabilities": self.capabilities,
        }

    def receive_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Receive and process a message from the Agent Bus."""

        self.received_messages.append(message)

        return {
            "message_id": message.get("message_id"),
            "request_id": message.get("request_id"),
            "sender": self.agent_id,
            "receiver": message.get("sender"),
            "message_type": "RESPONSE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "status": "received",
                "agent": self.agent_id,
            },
        }
    def send_message(
        self,
        bus: Any,
        receiver_id: str,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        if self.status != "active":
            raise RuntimeError(
                f"Agent '{self.agent_id}' is not active."
            )

        return bus.send_message(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message=message,
        )