from datetime import datetime, timezone
from typing import Any

from src.workflow_runtime.task import Task


class Workflow:
    """
    Represents a workflow consisting of dependent Tasks.
    """

    VALID_STATUSES = {
        "created",
        "running",
        "completed",
        "failed",
        "cancelled",
        "replanning",
    }

    def __init__(
        self,
        workflow_id: str,
        goal_id: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ):
        if not workflow_id.strip():
            raise ValueError(
                "Workflow ID must not be empty."
            )

        if not goal_id.strip():
            raise ValueError(
                "Goal ID must not be empty."
            )

        if not description.strip():
            raise ValueError(
                "Workflow description must not be empty."
            )

        self.workflow_id = workflow_id
        self.goal_id = goal_id
        self.description = description
        self.metadata = metadata or {}

        self.tasks: dict[str, Task] = {}
        self.status = "created"

        self.created_at = self._timestamp()
        self.updated_at = self.created_at

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def add_task(self, task: Task) -> None:
        if task.task_id in self.tasks:
            raise ValueError(
                f"Task '{task.task_id}' already exists "
                f"in workflow '{self.workflow_id}'."
            )

        for dependency in task.dependencies:
            if dependency == task.task_id:
                raise ValueError(
                    f"Task '{task.task_id}' cannot depend on itself."
                )

        self.tasks[task.task_id] = task
        self.updated_at = self._timestamp()

    def get_task(self, task_id: str) -> Task:
        if task_id not in self.tasks:
            raise ValueError(
                f"Task '{task_id}' does not exist "
                f"in workflow '{self.workflow_id}'."
            )

        return self.tasks[task_id]

    def validate_dependencies(self) -> None:
        for task in self.tasks.values():
            for dependency in task.dependencies:
                if dependency not in self.tasks:
                    raise ValueError(
                        f"Task '{task.task_id}' depends on "
                        f"unknown task '{dependency}'."
                    )

    def get_ready_tasks(self) -> list[Task]:
        ready_tasks = []

        for task in self.tasks.values():
            if task.status != "pending":
                continue

            dependencies_completed = all(
                self.tasks[dependency].status == "completed"
                for dependency in task.dependencies
            )

            if dependencies_completed:
                task.mark_ready()
                ready_tasks.append(task)

        return ready_tasks

    def start(self) -> None:
        if self.status != "created":
            raise RuntimeError(
                f"Workflow '{self.workflow_id}' cannot start "
                f"from status '{self.status}'."
            )

        self.validate_dependencies()

        self.status = "running"
        self.updated_at = self._timestamp()

        self.get_ready_tasks()

    def check_completion(self) -> None:
        if not self.tasks:
            return

        if all(
            task.status == "completed"
            for task in self.tasks.values()
        ):
            self.status = "completed"

        elif any(
            task.status == "failed"
            for task in self.tasks.values()
        ):
            self.status = "failed"

        elif all(
            task.status in {"completed", "cancelled"}
            for task in self.tasks.values()
        ):
            self.status = "completed"

        self.updated_at = self._timestamp()

    def replan(self) -> None:
        if self.status not in {"failed", "running"}:
            raise RuntimeError(
                f"Workflow '{self.workflow_id}' cannot be "
                f"replanned from status '{self.status}'."
            )

        self.status = "replanning"
        self.updated_at = self._timestamp()

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "goal_id": self.goal_id,
            "description": self.description,
            "metadata": self.metadata,
            "status": self.status,
            "tasks": {
                task_id: task.to_dict()
                for task_id, task in self.tasks.items()
            },
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }