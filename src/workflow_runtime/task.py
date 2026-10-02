from datetime import datetime, timezone
from typing import Any


class Task:
    """
    Represents an executable task within a Workflow.

    A Task may depend on one or more other tasks.
    """

    VALID_STATUSES = {
        "pending",
        "ready",
        "running",
        "completed",
        "failed",
        "cancelled",
    }

    def __init__(
        self,
        task_id: str,
        description: str,
        dependencies: list[str] | None = None,
        max_retries: int = 0,
        metadata: dict[str, Any] | None = None,
    ):
        if not task_id.strip():
            raise ValueError("Task ID must not be empty.")

        if not description.strip():
            raise ValueError(
                "Task description must not be empty."
            )

        if max_retries < 0:
            raise ValueError(
                "Max retries must not be negative."
            )

        self.task_id = task_id
        self.description = description
        self.dependencies = dependencies or []
        self.max_retries = max_retries
        self.retry_count = 0
        self.metadata = metadata or {}

        self.status = "pending"
        self.result: Any = None
        self.error: str | None = None

        self.created_at = self._timestamp()
        self.updated_at = self.created_at

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def mark_ready(self) -> None:
        if self.status != "pending":
            raise RuntimeError(
                f"Task '{self.task_id}' cannot be marked ready "
                f"from status '{self.status}'."
            )

        self.status = "ready"
        self.updated_at = self._timestamp()

    def start(self) -> None:
        if self.status != "ready":
            raise RuntimeError(
                f"Task '{self.task_id}' cannot start "
                f"from status '{self.status}'."
            )

        self.status = "running"
        self.updated_at = self._timestamp()

    def complete(self, result: Any = None) -> None:
        if self.status != "running":
            raise RuntimeError(
                f"Task '{self.task_id}' cannot complete "
                f"from status '{self.status}'."
            )

        self.status = "completed"
        self.result = result
        self.error = None
        self.updated_at = self._timestamp()

    def fail(self, error: str) -> None:
        if self.status != "running":
            raise RuntimeError(
                f"Task '{self.task_id}' cannot fail "
                f"from status '{self.status}'."
            )

        self.status = "failed"
        self.error = error
        self.updated_at = self._timestamp()

    def retry(self) -> None:
        if self.status != "failed":
            raise RuntimeError(
                f"Task '{self.task_id}' cannot retry "
                f"from status '{self.status}'."
            )

        if self.retry_count >= self.max_retries:
            raise RuntimeError(
                f"Task '{self.task_id}' has exhausted "
                f"its retry limit."
            )

        self.retry_count += 1
        self.status = "ready"
        self.error = None
        self.updated_at = self._timestamp()

    def cancel(self) -> None:
        if self.status in {"completed", "cancelled"}:
            raise RuntimeError(
                f"Task '{self.task_id}' cannot be cancelled "
                f"from status '{self.status}'."
            )

        self.status = "cancelled"
        self.updated_at = self._timestamp()

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "dependencies": self.dependencies,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }