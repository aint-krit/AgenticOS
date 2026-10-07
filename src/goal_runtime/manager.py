from datetime import datetime, timezone
from typing import Any

from src.agent_bus.bus import AgentBus
from src.goal_runtime.goal import Goal


class GoalManager:
    """
    Manages goals and communicates goal operations through the Agent Bus.
    """

    def __init__(
        self,
        bus: AgentBus,
        manager_agent_id: str = "goal-manager-agent",
    ):
        self.bus = bus
        self.manager_agent_id = manager_agent_id
        self.goals: dict[str, Goal] = {}

    def create_goal(
        self,
        goal_id: str,
        description: str,
        priority: str = "normal",
        metadata: dict[str, Any] | None = None,
    ) -> Goal:
        if goal_id in self.goals:
            raise ValueError(
                f"Goal '{goal_id}' already exists."
            )

        goal = Goal(
            goal_id=goal_id,
            description=description,
            priority=priority,
            metadata=metadata,
        )

        self.goals[goal_id] = goal
        return goal

    def get_goal(self, goal_id: str) -> Goal:
        if goal_id not in self.goals:
            raise ValueError(
                f"Goal '{goal_id}' does not exist."
            )

        return self.goals[goal_id]

    def handle_operation(
        self,
        goal_id: str,
        operation: str,
        **kwargs: Any,
    ) -> Goal:
        goal = self.get_goal(goal_id)

        operations = {
            "UPDATE": lambda: goal.update(
                description=kwargs.get("description"),
                priority=kwargs.get("priority"),
                metadata=kwargs.get("metadata"),
            ),
            "PAUSE": goal.pause,
            "CANCEL": goal.cancel,
            "COMPLETE": goal.complete,
            "FAIL": goal.fail,
            "REPLAN": goal.replan,
            "ACTIVATE": goal.activate,
        }

        operation = operation.upper()

        if operation == "CREATE":
            raise ValueError(
                "CREATE must use create_goal()."
            )

        if operation not in operations:
            raise ValueError(
                f"Unknown goal operation: {operation}"
            )

        operations[operation]()
        return goal

    def send_goal_message(
        self,
        sender_id: str,
        receiver_id: str,
        operation: str,
        goal_id: str,
        request_id: str,
        message_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:

        message = {
            "message_id": message_id,
            "request_id": request_id,
            "message_type": "REQUEST",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "operation": operation.upper(),
                "goal_id": goal_id,
                **kwargs,
            },
        }

        return self.bus.send_message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message=message,
        )

    def _error_response(
        self,
        message: dict[str, Any],
        error: Exception,
    ) -> dict[str, Any]:
        return {
            "message_id": f"error-{message.get('message_id', 'unknown')}",
            "request_id": message.get(
                "request_id",
                "unknown-request",
            ),
            "sender": self.manager_agent_id,
            "receiver": message.get("sender"),
            "message_type": "ERROR",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {
                "status": "error",
                "error_type": type(error).__name__,
                "error": str(error),
            },
        }

    def handle_goal_message(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any]:

        try:
            if not isinstance(message, dict):
                raise ValueError(
                    "Goal message must be a dictionary."
                )

            payload = message.get("payload")

            if not isinstance(payload, dict):
                raise ValueError(
                    "Goal message payload must be a dictionary."
                )

            operation = payload.get("operation")
            goal_id = payload.get("goal_id")

            if not operation:
                raise ValueError(
                    "Goal message requires an operation."
                )

            operation = operation.upper()

            if operation == "CREATE":
                if not goal_id:
                    raise ValueError(
                        "CREATE goal messages require a goal_id."
                    )
                description = payload.get("description")
                if not isinstance(description, str) or not description.strip():
                    raise ValueError(
                        "CREATE goal messages require a non-empty description."
                    )
                goal = self.create_goal(
                    goal_id=goal_id,
                    description=description,
                    priority=payload.get("priority", "normal"),
                    metadata=payload.get("metadata"),
                )
            else:
                if not goal_id:
                    raise ValueError(
                        "Goal message requires a goal_id."
                    )
                goal = self.handle_operation(
                    goal_id=goal_id,
                    operation=operation,
                    **{
                        key: value
                        for key, value in payload.items()
                        if key not in {"operation", "goal_id"}
                    },
                )

            return {
                "message_id": message.get("message_id"),
                "request_id": message.get("request_id"),
                "sender": self.manager_agent_id,
                "receiver": message.get("sender"),
                "message_type": "RESPONSE",
                "timestamp": message.get("timestamp"),
                "payload": {
                    "status": "success",
                    "operation": operation.upper(),
                    "goal": goal.to_dict(),
                },
            }

        except (ValueError, RuntimeError) as error:
            return self._error_response(
                message,
                error,
            )