from datetime import datetime, timezone
from typing import Any

from src.agent_runtime.agent import Agent


class ExecutorAgent(Agent):
    """
    Executes tasks dispatched by the Workflow Runtime.

    v0.1 provides a safe execution interface.
    Actual application/file execution is delegated to
    specialized agents.
    """

    def __init__(
        self,
        agent_id: str = "executor-agent",
    ):
        super().__init__(
            agent_id=agent_id,
            name="Executor Agent",
            agent_type="core",
            capabilities=[
                "execute_task",
                "dispatch_task",
            ],
        )

    def execute_task(
        self,
        task_id: str,
        description: str,
    ) -> dict[str, Any]:
        if not task_id:
            raise ValueError("task_id is required.")

        if not description.strip():
            raise ValueError("Task description is required.")

        return {
            "task_id": task_id,
            "status": "completed",
            "result": {
                "description": description,
                "executed_by": self.agent_id,
            },
        }

    def receive_message(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        self.received_messages.append(message)

        payload = message.get("payload", {})
        operation = payload.get("operation")

        if operation == "EXECUTE_TASK":
            result = self.execute_task(
                task_id=payload.get("task_id", ""),
                description=payload.get("description", ""),
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
                "payload": result,
            }

        return super().receive_message(message)