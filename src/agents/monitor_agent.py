from datetime import datetime, timezone
from typing import Any

from src.agent_runtime.agent import Agent


class MonitorAgent(Agent):
    """
    Observes agent/task state and records monitoring events.
    """

    def __init__(
        self,
        agent_id: str = "monitor-agent",
    ):
        super().__init__(
            agent_id=agent_id,
            name="Monitor Agent",
            agent_type="core",
            capabilities=[
                "monitor_agent",
                "monitor_task",
                "health_check",
            ],
        )

        self.events: list[dict[str, Any]] = []

    def record_event(
        self,
        event_type: str,
        source: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = {
            "event_type": event_type,
            "source": source,
            "data": data or {},
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        self.events.append(event)

        return event

    def get_events(self) -> list[dict[str, Any]]:
        return list(self.events)

    def receive_message(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        self.received_messages.append(message)

        payload = message.get("payload", {})

        event = self.record_event(
            event_type=payload.get(
                "event_type",
                "MESSAGE_RECEIVED",
            ),
            source=message.get(
                "sender",
                "unknown",
            ),
            data=payload,
        )

        return {
            "message_id": message.get("message_id"),
            "request_id": message.get("request_id"),
            "sender": self.agent_id,
            "receiver": message.get("sender"),
            "message_type": "RESPONSE",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "payload": {
                "status": "monitored",
                "event": event,
            },
        }