from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import monotonic
from typing import Any
from uuid import uuid4

from src.agent_bus.bus import AgentBus
from src.capability.registry import CapabilityRegistry
from src.capability.tool import Tool
from src.global_agent_manager.manager import GlobalAgentManager
from src.goal_runtime.manager import GoalManager
from src.workflow_runtime.manager import WorkflowManager
from src.workflow_runtime.task import Task


@dataclass(frozen=True)
class IntentSpec:
    capability: str
    operation: str
    agent_id: str | None = None


@dataclass
class TaskSpec:
    task_id: str
    description: str
    capability: str
    operation: str
    payload: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    max_retries: int = 0
    timeout_seconds: float | None = None


class AgentPlatform:
    """
    AgenticOS v0.1 vertical orchestration layer.

    Intent -> Goal -> Workflow -> Global Agent Manager ->
    Capability/Permission -> Agent Bus -> Agent -> Result.

    The capability registry is the authorization gate. Registered
    capability tools dispatch authorized work through the Agent Bus.
    """

    INTENTS: dict[str, IntentSpec] = {
        "create_file": IntentSpec("create_file", "CREATE_FILE"),
        "read_file": IntentSpec("read_file", "READ_FILE"),
        "write_file": IntentSpec("write_file", "WRITE_FILE"),
        "delete_file": IntentSpec("delete_file", "DELETE_FILE"),
        "open_browser": IntentSpec("open_browser", "OPEN_BROWSER"),
        "open_url": IntentSpec("open_url", "OPEN_URL"),
        "remember": IntentSpec("remember", "REMEMBER"),
        "retrieve_memory": IntentSpec("retrieve_memory", "RETRIEVE_MEMORY"),
        "search_memory": IntentSpec("search_memory", "SEARCH_MEMORY"),
        "delete_memory": IntentSpec("delete_memory", "DELETE_MEMORY"),
        "clear_memory": IntentSpec("clear_memory", "CLEAR_MEMORY"),
        "verify_memory": IntentSpec("verify_memory", "VERIFY_MEMORY"),
        "execute_task": IntentSpec("execute_task", "EXECUTE_TASK"),
        "plan_task": IntentSpec("plan_task", "PLAN"),
    }

    def __init__(
        self,
        bus: AgentBus,
        agent_manager: GlobalAgentManager,
        goal_manager: GoalManager,
        workflow_manager: WorkflowManager,
        capability_registry: CapabilityRegistry,
        coordinator_agent_id: str = "agent-platform",
    ) -> None:
        self.bus = bus
        self.agent_manager = agent_manager
        self.goal_manager = goal_manager
        self.workflow_manager = workflow_manager
        self.capability_registry = capability_registry
        self.coordinator_agent_id = coordinator_agent_id
        self.trace: dict[str, list[dict[str, Any]]] = {}
        self._capability_owners: dict[str, str] = {}

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _record(self, request_id: str, stage: str, status: str, **data: Any) -> None:
        self.trace.setdefault(request_id, []).append({
            "timestamp": self._timestamp(),
            "stage": stage,
            "status": status,
            **data,
        })

    def register_capability_route(
        self,
        agent_id: str,
        capability: str,
        operation: str,
    ) -> dict[str, Any]:
        """Register a capability as an authorized Agent Bus route."""
        if agent_id not in self.bus.agents:
            raise ValueError(f"Agent '{agent_id}' is not registered.")
        if capability in self._capability_owners:
            raise ValueError(f"Capability '{capability}' already has an owner.")

        def dispatch(**kwargs: Any) -> dict[str, Any]:
            request_id = kwargs.pop("request_id", None)
            message_id = kwargs.pop("message_id", None)
            if not request_id or not message_id:
                raise ValueError("Capability dispatch requires request_id and message_id.")

            message = {
                "message_id": message_id,
                "request_id": request_id,
                "message_type": "REQUEST",
                "timestamp": self._timestamp(),
                "payload": {"operation": operation, **kwargs},
            }
            self._record(
                request_id,
                "agent_bus.dispatch",
                "started",
                agent_id=agent_id,
                capability=capability,
                operation=operation,
            )
            response = self.bus.send_message(
                sender_id=self.coordinator_agent_id,
                receiver_id=agent_id,
                message=message,
            )
            self._record(
                request_id,
                "agent_bus.dispatch",
                "completed" if response.get("message_type") == "RESPONSE" else "failed",
                agent_id=agent_id,
                capability=capability,
            )
            return response

        self.capability_registry.register_tool(
            Tool(
                tool_id=f"agent-route:{capability}",
                name=f"Agent route: {capability}",
                description=f"Authorized Agent Bus route for '{capability}' to '{agent_id}'.",
                handler=dispatch,
                capabilities=[capability],
            )
        )
        self._capability_owners[capability] = agent_id
        return {
            "status": "registered",
            "capability": capability,
            "agent_id": agent_id,
            "operation": operation,
        }

    def register_agent_capabilities(
        self,
        agent_id: str,
        operations: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        registration = self.agent_manager.get_agent(agent_id)
        declared = registration.get("capabilities", [])
        operations = operations or {
            capability: capability.upper() for capability in declared
        }
        return [
            self.register_capability_route(
                agent_id=agent_id,
                capability=capability,
                operation=operations.get(capability, capability.upper()),
            )
            for capability in declared
        ]

    def grant_capability(self, agent_id: str, capability: str) -> None:
        self.capability_registry.grant_permission(agent_id, capability)

    def select_agent(self, capability: str) -> str:
        return self.agent_manager.select_agent(capability)["agent_id"]

    def resolve_intent(self, intent: str) -> IntentSpec:
        if not isinstance(intent, str) or not intent.strip():
            raise ValueError("Intent must be a non-empty string.")
        normalized = intent.strip().lower()
        if normalized not in self.INTENTS:
            raise ValueError(f"Unknown intent: {normalized}")
        return self.INTENTS[normalized]

    def _ensure_coordinator(self) -> None:
        if self.coordinator_agent_id not in self.bus.agents:
            raise ValueError(f"Coordinator agent '{self.coordinator_agent_id}' is not registered.")
        if self.bus.agents[self.coordinator_agent_id].status != "active":
            raise RuntimeError(f"Coordinator agent '{self.coordinator_agent_id}' is not active.")

    def _build_task(self, spec: TaskSpec) -> Task:
        return Task(
            task_id=spec.task_id,
            description=spec.description,
            dependencies=spec.dependencies,
            max_retries=spec.max_retries,
            metadata={
                **spec.payload,
                "capability": spec.capability,
                "operation": spec.operation,
                "timeout_seconds": spec.timeout_seconds,
            },
        )

    def execute_workflow(
        self,
        goal_id: str,
        workflow_id: str,
        request_id: str,
        tasks: list[TaskSpec],
    ) -> dict[str, Any]:
        if not tasks:
            raise ValueError("Workflow requires at least one task.")
        self._ensure_coordinator()

        self.workflow_manager.create_workflow(
            workflow_id=workflow_id,
            goal_id=goal_id,
            description=f"Workflow for goal '{goal_id}'.",
            metadata={"request_id": request_id},
        )
        for spec in tasks:
            self.workflow_manager.add_task(workflow_id, self._build_task(spec))

        initial_ready = self.workflow_manager.start_workflow(workflow_id)
        self._record(
            request_id,
            "workflow",
            "started",
            workflow_id=workflow_id,
            ready_tasks=[task.task_id for task in initial_ready],
        )

        task_specs = {spec.task_id: spec for spec in tasks}
        completed: set[str] = set()
        task_results: dict[str, Any] = {}

        while len(completed) < len(tasks):
            ready = [
                task
                for task in self.workflow_manager.get_workflow(workflow_id).tasks.values()
                if task.status == "ready"
            ]
            if not ready:
                newly_ready = self.workflow_manager.get_ready_tasks(workflow_id)
                ready.extend(newly_ready)
            if not ready:
                workflow = self.workflow_manager.get_workflow(workflow_id)
                if workflow.status == "completed":
                    break
                raise RuntimeError("Workflow made no progress; dependency cycle or blocked task detected.")

            for task in ready:
                spec = task_specs[task.task_id]
                agent_id = self.select_agent(spec.capability)
                self._record(
                    request_id,
                    "global_agent_manager.select",
                    "completed",
                    capability=spec.capability,
                    agent_id=agent_id,
                    task_id=task.task_id,
                )

                attempt = 0
                while True:
                    if task.status == "ready":
                        task.start()
                    attempt += 1
                    started = monotonic()
                    message_id = f"msg-{uuid4().hex}"
                    # Authorization is a hard gate. Unauthorized work never
                    # reaches the Agent Bus or the target agent.
                    self.capability_registry.permission_manager.require_permission(
                        agent_id,
                        spec.capability,
                    )
                    try:
                        authorized_result = self.capability_registry.execute(
                            agent_id=agent_id,
                            capability=spec.capability,
                            request_id=request_id,
                            message_id=message_id,
                            **spec.payload,
                        )
                        response = authorized_result["result"]
                    except Exception as error:
                        response = {
                            "message_type": "ERROR",
                            "payload": {
                                "status": "error",
                                "error_type": type(error).__name__,
                                "error": str(error),
                            },
                        }

                    elapsed = monotonic() - started
                    timed_out = (
                        spec.timeout_seconds is not None
                        and elapsed > spec.timeout_seconds
                    )
                    failed = timed_out or response.get("message_type") == "ERROR"

                    if failed:
                        if timed_out:
                            error_message = (
                                f"Task '{task.task_id}' exceeded timeout "
                                f"of {spec.timeout_seconds} seconds."
                            )
                        else:
                            error_message = response.get("payload", {}).get(
                                "error", "Agent execution failed."
                            )

                        self._record(
                            request_id,
                            "workflow.task",
                            "failed",
                            task_id=task.task_id,
                            attempt=attempt,
                            error=error_message,
                        )

                        self.workflow_manager.fail_task(
                            workflow_id,
                            task.task_id,
                            error_message,
                        )
                        if attempt <= task.max_retries:
                            self.workflow_manager.retry_task(workflow_id, task.task_id)
                            continue
                        raise RuntimeError(error_message)

                    self.workflow_manager.complete_task(
                        workflow_id,
                        task.task_id,
                        result=response,
                    )
                    completed.add(task.task_id)
                    task_results[task.task_id] = response
                    self._record(
                        request_id,
                        "workflow.task",
                        "completed",
                        task_id=task.task_id,
                        agent_id=agent_id,
                        attempt=attempt,
                        elapsed_seconds=elapsed,
                    )
                    break

        workflow = self.workflow_manager.get_workflow(workflow_id)
        goal = self.goal_manager.get_goal(goal_id)
        if goal.status == "created":
            goal.activate()
        if goal.status == "active":
            goal.complete()

        self._record(request_id, "workflow", "completed", workflow_id=workflow_id)
        return {
            "status": "completed",
            "request_id": request_id,
            "goal": goal.to_dict(),
            "workflow": workflow.to_dict(),
            "results": task_results,
            "trace": list(self.trace.get(request_id, [])),
            "verified": workflow.status == "completed" and goal.status == "completed",
        }

    def execute_intent(
        self,
        intent: str,
        description: str,
        payload: dict[str, Any] | None = None,
        sender_id: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        payload = dict(payload or {})
        request_id = request_id or f"req-{uuid4().hex}"
        sender_id = sender_id or self.coordinator_agent_id
        spec = self.resolve_intent(intent)
        self._record(
            request_id,
            "intent",
            "resolved",
            intent=intent,
            capability=spec.capability,
        )

        goal_id = f"goal-{uuid4().hex}"
        workflow_id = f"workflow-{uuid4().hex}"
        goal = self.goal_manager.create_goal(
            goal_id=goal_id,
            description=description,
            metadata={
                "request_id": request_id,
                "intent": intent,
                "sender_id": sender_id,
            },
        )
        self._record(request_id, "goal", "created", goal_id=goal_id)

        return self.execute_workflow(
            goal_id=goal_id,
            workflow_id=workflow_id,
            request_id=request_id,
            tasks=[
                TaskSpec(
                    task_id=f"{workflow_id}-task-1",
                    description=description,
                    capability=spec.capability,
                    operation=spec.operation,
                    payload=payload,
                )
            ],
        )
