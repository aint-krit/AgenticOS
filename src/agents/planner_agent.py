from typing import Any

from src.agent_runtime.agent import Agent


class PlannerAgent(Agent):
    """
    Creates a simple executable plan from a goal.

    v0.1 intentionally keeps planning deterministic.
    The agent interface can later be backed by an LLM.
    """

    def __init__(
        self,
        agent_id: str = "planner-agent",
    ):
        super().__init__(
            agent_id=agent_id,
            name="Planner Agent",
            agent_type="core",
            capabilities=[
                "plan_task",
                "create_plan",
                "decompose_goal",
            ],
        )

    def plan(
        self,
        goal_id: str,
        description: str,
    ) -> dict[str, Any]:
        if not goal_id:
            raise ValueError("goal_id is required.")

        if not description.strip():
            raise ValueError("Goal description is required.")

        return {
            "goal_id": goal_id,
            "status": "planned",
            "tasks": [
                {
                    "task_id": f"{goal_id}-task-1",
                    "description": description,
                    "dependencies": [],
                }
            ],
        }

    def receive_message(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        self.received_messages.append(message)

        payload = message.get("payload", {})
        operation = payload.get("operation")

        if operation == "PLAN":
            result = self.plan(
                goal_id=payload.get("goal_id", ""),
                description=payload.get("description", ""),
            )

            return {
                "message_id": message.get("message_id"),
                "request_id": message.get("request_id"),
                "sender": self.agent_id,
                "receiver": message.get("sender"),
                "message_type": "RESPONSE",
                "timestamp": self._timestamp(),
                "payload": result,
            }

        return super().receive_message(message)

    @staticmethod
    def _timestamp() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()