from datetime import datetime, timezone
from typing import Any


class Goal:
    """
    Represents a Goal in AgenticOS.

    v0.1 provides the basic goal lifecycle and state transitions.
    """

    VALID_STATUSES = {
        "created",
        "active",
        "paused",
        "cancelled",
        "completed",
        "failed",
        "replanning",
    }

    def __init__(
        self,
        goal_id: str,
        description: str,
        priority: str = "normal",
        metadata: dict[str, Any] | None = None,
    ):
        if not goal_id.strip():
            raise ValueError("Goal ID must not be empty.")

        if not description.strip():
            raise ValueError("Goal description must not be empty.")

        self.goal_id = goal_id
        self.description = description
        self.priority = priority
        self.metadata = metadata or {}
        self.status = "created"
        self.created_at = self._timestamp()
        self.updated_at = self.created_at
        self.history: list[dict[str, Any]] = []

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _record_transition(
        self,
        previous_status: str,
        new_status: str,
    ) -> None:
        self.status = new_status
        self.updated_at = self._timestamp()

        self.history.append(
            {
                "timestamp": self.updated_at,
                "from": previous_status,
                "to": new_status,
            }
        )

    def activate(self) -> None:
        if self.status not in {"created", "paused", "replanning"}:
            raise RuntimeError(
                f"Goal '{self.goal_id}' cannot be activated "
                f"from status '{self.status}'."
            )

        self._record_transition(self.status, "active")

    def update(
        self,
        description: str | None = None,
        priority: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self.status in {"cancelled", "completed", "failed"}:
            raise RuntimeError(
                f"Goal '{self.goal_id}' cannot be updated "
                f"from status '{self.status}'."
            )

        if description is not None:
            if not description.strip():
                raise ValueError(
                    "Goal description must not be empty."
                )
            self.description = description

        if priority is not None:
            self.priority = priority

        if metadata is not None:
            self.metadata.update(metadata)

        self.updated_at = self._timestamp()

    def pause(self) -> None:
        if self.status != "active":
            raise RuntimeError(
                f"Goal '{self.goal_id}' cannot be paused "
                f"from status '{self.status}'."
            )

        self._record_transition("active", "paused")

    def cancel(self) -> None:
        if self.status in {"completed", "cancelled"}:
            raise RuntimeError(
                f"Goal '{self.goal_id}' cannot be cancelled "
                f"from status '{self.status}'."
            )

        self._record_transition(self.status, "cancelled")

    def complete(self) -> None:
        if self.status != "active":
            raise RuntimeError(
                f"Goal '{self.goal_id}' cannot be completed "
                f"from status '{self.status}'."
            )

        self._record_transition("active", "completed")

    def fail(self) -> None:
        if self.status in {"completed", "cancelled"}:
            raise RuntimeError(
                f"Goal '{self.goal_id}' cannot fail "
                f"from status '{self.status}'."
            )

        self._record_transition(self.status, "failed")

    def replan(self) -> None:
        if self.status not in {"active", "failed", "paused"}:
            raise RuntimeError(
                f"Goal '{self.goal_id}' cannot be replanned "
                f"from status '{self.status}'."
            )

        self._record_transition(self.status, "replanning")

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "description": self.description,
            "priority": self.priority,
            "metadata": self.metadata,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "history": self.history,
        }