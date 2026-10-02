from datetime import datetime, timezone
from typing import Any

from src.agent_bus.bus import AgentBus
from src.workflow_runtime.task import Task
from src.workflow_runtime.workflow import Workflow


class WorkflowManager:
    """
    Coordinates workflow execution and task dispatch through
    the Agent Bus.
    """

    def __init__(
        self,
        bus: AgentBus,
        manager_agent_id: str = "workflow-manager-agent",
    ):
        self.bus = bus
        self.manager_agent_id = manager_agent_id
        self.workflows: dict[str, Workflow] = {}

    def create_workflow(
        self,
        workflow_id: str,
        goal_id: str,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> Workflow:
        if workflow_id in self.workflows:
            raise ValueError(
                f"Workflow '{workflow_id}' already exists."
            )

        workflow = Workflow(
            workflow_id=workflow_id,
            goal_id=goal_id,
            description=description,
            metadata=metadata,
        )

        self.workflows[workflow_id] = workflow
        return workflow

    def get_workflow(self, workflow_id: str) -> Workflow:
        if workflow_id not in self.workflows:
            raise ValueError(
                f"Workflow '{workflow_id}' does not exist."
            )

        return self.workflows[workflow_id]

    def add_task(
        self,
        workflow_id: str,
        task: Task,
    ) -> None:
        workflow = self.get_workflow(workflow_id)
        workflow.add_task(task)

    def start_workflow(
        self,
        workflow_id: str,
    ) -> list[Task]:
        workflow = self.get_workflow(workflow_id)

        workflow.start()

        return [
            task
            for task in workflow.tasks.values()
            if task.status == "ready"
        ]

    def get_ready_tasks(
        self,
        workflow_id: str,
    ) -> list[Task]:
        workflow = self.get_workflow(workflow_id)

        return workflow.get_ready_tasks()

    def dispatch_task(
        self,
        workflow_id: str,
        task_id: str,
        sender_id: str,
        receiver_id: str,
        request_id: str,
        message_id: str,
    ) -> dict[str, Any]:
        workflow = self.get_workflow(workflow_id)
        task = workflow.get_task(task_id)

        if task.status != "ready":
            raise RuntimeError(
                f"Task '{task_id}' is not ready for dispatch."
            )

        task.start()

        message = {
            "message_id": message_id,
            "request_id": request_id,
            "message_type": "REQUEST",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "payload": {
                "operation": "EXECUTE_TASK",
                "workflow_id": workflow_id,
                "task_id": task_id,
                "description": task.description,
                "metadata": task.metadata,
            },
        }

        try:
            response = self.bus.send_message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                message=message,
            )
            return response

        except (ValueError, RuntimeError):
            task.fail("Task dispatch failed.")
            raise

    def complete_task(
        self,
        workflow_id: str,
        task_id: str,
        result: Any = None,
    ) -> list[Task]:
        workflow = self.get_workflow(workflow_id)
        task = workflow.get_task(task_id)

        task.complete(result)

        workflow.check_completion()

        if workflow.status == "completed":
            return []

        return workflow.get_ready_tasks()

    def fail_task(
        self,
        workflow_id: str,
        task_id: str,
        error: str,
    ) -> list[Task]:
        workflow = self.get_workflow(workflow_id)
        task = workflow.get_task(task_id)

        task.fail(error)

        workflow.check_completion()

        return workflow.get_ready_tasks()

    def retry_task(
        self,
        workflow_id: str,
        task_id: str,
    ) -> Task:
        workflow = self.get_workflow(workflow_id)
        task = workflow.get_task(task_id)

        task.retry()

        return task

    def replan_workflow(
        self,
        workflow_id: str,
    ) -> Workflow:
        workflow = self.get_workflow(workflow_id)

        workflow.replan()

        return workflow

    def process_task_result(
        self,
        workflow_id: str,
        task_id: str,
        success: bool,
        result: Any = None,
        error: str | None = None,
    ) -> list[Task]:
        if success:
            return self.complete_task(
                workflow_id=workflow_id,
                task_id=task_id,
                result=result,
            )

        return self.fail_task(
            workflow_id=workflow_id,
            task_id=task_id,
            error=error or "Task execution failed.",
        )

    def _error_response(
        self,
        message: dict[str, Any],
        error: Exception,
    ) -> dict[str, Any]:
        return {
            "message_id": (
                f"error-{message.get('message_id', 'unknown')}"
            ),
            "request_id": message.get(
                "request_id",
                "unknown-request",
            ),
            "sender": self.manager_agent_id,
            "receiver": message.get("sender"),
            "message_type": "ERROR",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "payload": {
                "status": "error",
                "error_type": type(error).__name__,
                "error": str(error),
            },
        }

    def handle_workflow_message(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle a workflow request received through
        the Agent Bus.
        """

        try:
            if not isinstance(message, dict):
                raise ValueError(
                    "Workflow message must be a dictionary."
                )

            payload = message.get("payload")

            if not isinstance(payload, dict):
                raise ValueError(
                    "Workflow message payload must be a dictionary."
                )

            operation = payload.get("operation")
            workflow_id = payload.get("workflow_id")

            if not operation:
                raise ValueError(
                    "Workflow message requires an operation."
                )

            if not workflow_id:
                raise ValueError(
                    "Workflow message requires a workflow_id."
                )

            operation = operation.upper()

            if operation == "START":
                ready_tasks = self.start_workflow(
                    workflow_id
                )

                payload_response = {
                    "status": "success",
                    "operation": operation,
                    "workflow_id": workflow_id,
                    "ready_tasks": [
                        task.to_dict()
                        for task in ready_tasks
                    ],
                }

            elif operation == "REPLAN":
                workflow = self.replan_workflow(
                    workflow_id
                )

                payload_response = {
                    "status": "success",
                    "operation": operation,
                    "workflow": workflow.to_dict(),
                }

            else:
                raise ValueError(
                    f"Unknown workflow operation: {operation}"
                )

            return {
                "message_id": message.get("message_id"),
                "request_id": message.get("request_id"),
                "sender": self.manager_agent_id,
                "receiver": message.get("sender"),
                "message_type": "RESPONSE",
                "timestamp": message.get("timestamp"),
                "payload": payload_response,
            }

        except (ValueError, RuntimeError) as error:
            return self._error_response(
                message,
                error,
            )