from datetime import datetime, timezone
from typing import Any


class IntentRouter:
    """
    Resolves intent messages to registered agents.

    v0.1 uses deterministic intent mapping.
    Routing failures generate structured ERROR responses.
    """

    INTENT_TO_AGENT = {
        "open_browser": "application-agent",
        "create_file": "file-agent",
        "read_file": "file-agent",
        "write_file": "file-agent",
        "delete_file": "file-agent",
        "remember": "memory-agent",
        "retrieve_memory": "memory-agent",
        "execute_task": "executor-agent",
        "plan_task": "planner-agent",
    }

    def __init__(self, bus: Any):
        self.bus = bus

    def resolve(self, intent: str) -> str:
        if not isinstance(intent, str) or not intent.strip():
            raise ValueError("Intent must be a non-empty string.")

        normalized_intent = intent.strip().lower()

        if normalized_intent not in self.INTENT_TO_AGENT:
            raise ValueError(
                f"Unknown intent: {normalized_intent}"
            )

        return self.INTENT_TO_AGENT[normalized_intent]

    def _error_response(
        self,
        message: dict[str, Any],
        sender_id: str,
        error: Exception,
    ) -> dict[str, Any]:
        """
        Create a structured ERROR response for a routing failure.
        """

        return {
            "message_id": f"error-{message.get('message_id', 'unknown')}",
            "request_id": message.get(
                "request_id",
                "unknown-request",
            ),
            "sender": "intent-router",
            "receiver": sender_id,
            "message_type": "ERROR",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "status": "error",
                "error_type": type(error).__name__,
                "error": str(error),
            },
        }

    def route(
        self,
        message: dict[str, Any],
        sender_id: str,
    ) -> dict[str, Any]:
        """
        Resolve and route an intent through the Agent Bus.

        Routing failures return a structured ERROR message.
        """

        try:
            if not isinstance(message, dict):
                raise ValueError(
                    "Intent message must be a dictionary."
                )

            required_fields = {
                "message_id",
                "request_id",
                "message_type",
                "timestamp",
                "payload",
            }

            missing = required_fields - message.keys()

            if missing:
                raise ValueError(
                    "Intent message is missing required fields: "
                    f"{sorted(missing)}"
                )

            if message["message_type"] != "REQUEST":
                raise ValueError(
                    "Intent messages must use message_type='REQUEST'."
                )

            payload = message["payload"]

            if not isinstance(payload, dict):
                raise ValueError(
                    "Intent payload must be a dictionary."
                )

            intent = payload.get("intent")

            if not isinstance(intent, str) or not intent.strip():
                raise ValueError(
                    "Intent payload must contain a "
                    "non-empty 'intent'."
                )

            receiver_id = self.resolve(intent)

            if receiver_id not in self.bus.agents:
                raise ValueError(
                    f"Target agent '{receiver_id}' is not registered."
                )

            receiver = self.bus.agents[receiver_id]

            if receiver.status != "active":
                raise RuntimeError(
                    f"Target agent '{receiver_id}' is not active."
                )

            return self.bus.send_message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                message=message,
            )

        except (ValueError, RuntimeError) as error:
            return self._error_response(
                message=message if isinstance(message, dict) else {},
                sender_id=sender_id,
                error=error,
            )