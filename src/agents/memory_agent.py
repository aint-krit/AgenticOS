from datetime import datetime, timezone
from typing import Any

from src.agent_runtime.agent import Agent


class MemoryAgent(Agent):
    """
    Simple episodic key-value memory for v0.1.

    The vector store / semantic retrieval layer comes in
    the Knowledge + Memory milestone.
    """

    def __init__(
        self,
        agent_id: str = "memory-agent",
    ):
        super().__init__(
            agent_id=agent_id,
            name="Memory Agent",
            agent_type="core",
            capabilities=[
                "remember",
                "retrieve_memory",
                "clear_memory",
            ],
        )

        self.memory: dict[str, Any] = {}

    def remember(
        self,
        key: str,
        value: Any,
    ) -> dict[str, Any]:
        if not key:
            raise ValueError("Memory key is required.")

        self.memory[key] = value

        return {
            "status": "stored",
            "key": key,
            "value": value,
        }

    def retrieve(
        self,
        key: str,
    ) -> dict[str, Any]:
        if key not in self.memory:
            return {
                "status": "not_found",
                "key": key,
                "value": None,
            }

        return {
            "status": "found",
            "key": key,
            "value": self.memory[key],
        }

    def clear(
        self,
        key: str,
    ) -> dict[str, Any]:
        if key in self.memory:
            del self.memory[key]
            return {
                "status": "deleted",
                "key": key,
            }

        return {
            "status": "not_found",
            "key": key,
        }

    def receive_message(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        self.received_messages.append(message)

        payload = message.get("payload", {})
        operation = payload.get("operation")

        if operation == "REMEMBER":
            result = self.remember(
                key=payload.get("key", ""),
                value=payload.get("value"),
            )

        elif operation == "RETRIEVE_MEMORY":
            result = self.retrieve(
                key=payload.get("key", ""),
            )

        elif operation == "CLEAR_MEMORY":
            result = self.clear(
                key=payload.get("key", ""),
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