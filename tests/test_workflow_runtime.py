import pytest

from src.workflow_runtime.task import Task
from src.workflow_runtime.workflow import Workflow


def test_task_creation():
    task = Task(
        task_id="task-001",
        description="Open browser",
    )

    assert task.task_id == "task-001"
    assert task.status == "pending"
    assert task.retry_count == 0


def test_task_lifecycle():
    task = Task(
        task_id="task-001",
        description="Open browser",
    )

    task.mark_ready()
    task.start()
    task.complete("Browser opened")

    assert task.status == "completed"
    assert task.result == "Browser opened"


def test_task_failure():
    task = Task(
        task_id="task-001",
        description="Open browser",
        max_retries=1,
    )

    task.mark_ready()
    task.start()
    task.fail("Browser unavailable")

    assert task.status == "failed"
    assert task.error == "Browser unavailable"


def test_task_retry():
    task = Task(
        task_id="task-001",
        description="Open browser",
        max_retries=1,
    )

    task.mark_ready()
    task.start()
    task.fail("Browser unavailable")
    task.retry()

    assert task.status == "ready"
    assert task.retry_count == 1
    assert task.error is None


def test_retry_limit():
    task = Task(
        task_id="task-001",
        description="Open browser",
        max_retries=1,
    )

    task.mark_ready()
    task.start()
    task.fail("Browser unavailable")
    task.retry()

    task.start()
    task.fail("Browser still unavailable")

    with pytest.raises(RuntimeError, match="exhausted"):
        task.retry()


def test_workflow_adds_tasks():
    workflow = Workflow(
        workflow_id="workflow-001",
        goal_id="goal-001",
        description="Open browser and create file",
    )

    task = Task(
        task_id="task-001",
        description="Open browser",
    )

    workflow.add_task(task)

    assert "task-001" in workflow.tasks


def test_workflow_dependency_execution():
    workflow = Workflow(
        workflow_id="workflow-001",
        goal_id="goal-001",
        description="Two-step workflow",
    )

    task_1 = Task(
        task_id="task-001",
        description="Open browser",
    )

    task_2 = Task(
        task_id="task-002",
        description="Navigate to website",
        dependencies=["task-001"],
    )

    workflow.add_task(task_1)
    workflow.add_task(task_2)

    workflow.start()

    assert task_1.status == "ready"
    assert task_2.status == "pending"

    task_1.start()
    task_1.complete("Browser opened")

    ready_tasks = workflow.get_ready_tasks()

    assert task_2 in ready_tasks
    assert task_2.status == "ready"


def test_unknown_dependency_is_rejected():
    workflow = Workflow(
        workflow_id="workflow-001",
        goal_id="goal-001",
        description="Invalid workflow",
    )

    task = Task(
        task_id="task-002",
        description="Navigate",
        dependencies=["task-001"],
    )

    workflow.add_task(task)

    with pytest.raises(ValueError, match="unknown task"):
        workflow.start()


def test_self_dependency_is_rejected():
    workflow = Workflow(
        workflow_id="workflow-001",
        goal_id="goal-001",
        description="Invalid workflow",
    )

    task = Task(
        task_id="task-001",
        description="Invalid task",
        dependencies=["task-001"],
    )

    with pytest.raises(
        ValueError,
        match="cannot depend on itself",
    ):
        workflow.add_task(task)
from src.agent_bus.bus import AgentBus
from src.agent_runtime.agent import Agent
from src.workflow_runtime.manager import WorkflowManager


def create_workflow_manager():
    bus = AgentBus()

    planner = Agent(
        agent_id="planner-agent",
        name="Planner Agent",
    )

    workflow_agent = Agent(
        agent_id="workflow-manager-agent",
        name="Workflow Manager Agent",
    )

    executor = Agent(
        agent_id="executor-agent",
        name="Executor Agent",
    )

    planner.start()
    workflow_agent.start()
    executor.start()

    bus.register_agent(planner)
    bus.register_agent(workflow_agent)
    bus.register_agent(executor)

    return bus, WorkflowManager(bus)


def test_workflow_manager_creates_workflow():
    bus, manager = create_workflow_manager()

    workflow = manager.create_workflow(
        workflow_id="workflow-001",
        goal_id="goal-001",
        description="Open browser and navigate",
    )

    assert workflow.workflow_id == "workflow-001"
    assert workflow.status == "created"


def test_workflow_manager_adds_tasks():
    bus, manager = create_workflow_manager()

    manager.create_workflow(
        "workflow-001",
        "goal-001",
        "Two-step workflow",
    )

    task = Task(
        task_id="task-001",
        description="Open browser",
    )

    manager.add_task(
        "workflow-001",
        task,
    )

    workflow = manager.get_workflow(
        "workflow-001"
    )

    assert "task-001" in workflow.tasks


def test_workflow_manager_starts_workflow():
    bus, manager = create_workflow_manager()

    manager.create_workflow(
        "workflow-001",
        "goal-001",
        "Two-step workflow",
    )

    manager.add_task(
        "workflow-001",
        Task(
            "task-001",
            "Open browser",
        ),
    )

    ready_tasks = manager.start_workflow(
        "workflow-001"
    )

    assert len(ready_tasks) == 1
    assert ready_tasks[0].task_id == "task-001"
    assert ready_tasks[0].status == "ready"


def test_dispatch_task_through_agent_bus():
    bus, manager = create_workflow_manager()

    manager.create_workflow(
        "workflow-001",
        "goal-001",
        "Open browser",
    )

    manager.add_task(
        "workflow-001",
        Task(
            "task-001",
            "Open browser",
        ),
    )

    manager.start_workflow("workflow-001")

    response = manager.dispatch_task(
        workflow_id="workflow-001",
        task_id="task-001",
        sender_id="workflow-manager-agent",
        receiver_id="executor-agent",
        request_id="req-task-001",
        message_id="msg-task-001",
    )

    assert response["payload"]["status"] == "received"

    received = bus.agents[
        "executor-agent"
    ].received_messages[-1]

    assert received["payload"]["operation"] == "EXECUTE_TASK"
    assert received["payload"]["task_id"] == "task-001"


def test_completed_task_unlocks_dependency():
    bus, manager = create_workflow_manager()

    manager.create_workflow(
        "workflow-001",
        "goal-001",
        "Two-step workflow",
    )

    manager.add_task(
        "workflow-001",
        Task(
            "task-001",
            "Open browser",
        ),
    )

    manager.add_task(
        "workflow-001",
        Task(
            "task-002",
            "Navigate to website",
            dependencies=["task-001"],
        ),
    )

    manager.start_workflow("workflow-001")

    manager.get_workflow(
        "workflow-001"
    ).get_task("task-001").start()

    ready_tasks = manager.complete_task(
        "workflow-001",
        "task-001",
        result="Browser opened",
    )

    assert len(ready_tasks) == 1
    assert ready_tasks[0].task_id == "task-002"
    assert ready_tasks[0].status == "ready"


def test_failed_task_can_be_retried():
    bus, manager = create_workflow_manager()

    manager.create_workflow(
        "workflow-001",
        "goal-001",
        "Retry workflow",
    )

    manager.add_task(
        "workflow-001",
        Task(
            "task-001",
            "Open browser",
            max_retries=1,
        ),
    )

    manager.start_workflow("workflow-001")

    task = manager.get_workflow(
        "workflow-001"
    ).get_task("task-001")

    task.start()

    manager.fail_task(
        "workflow-001",
        "task-001",
        "Browser unavailable",
    )

    manager.retry_task(
        "workflow-001",
        "task-001",
    )

    assert task.status == "ready"
    assert task.retry_count == 1


def test_workflow_completion():
    bus, manager = create_workflow_manager()

    manager.create_workflow(
        "workflow-001",
        "goal-001",
        "Single-step workflow",
    )

    manager.add_task(
        "workflow-001",
        Task(
            "task-001",
            "Open browser",
        ),
    )

    manager.start_workflow("workflow-001")

    task = manager.get_workflow(
        "workflow-001"
    ).get_task("task-001")

    task.start()

    ready_tasks = manager.complete_task(
        "workflow-001",
        "task-001",
        result="Done",
    )

    workflow = manager.get_workflow(
        "workflow-001"
    )

    assert ready_tasks == []
    assert workflow.status == "completed"


def test_workflow_message_handler():
    bus, manager = create_workflow_manager()

    manager.create_workflow(
        "workflow-001",
        "goal-001",
        "Open browser",
    )

    manager.add_task(
        "workflow-001",
        Task(
            "task-001",
            "Open browser",
        ),
    )

    message = {
        "message_id": "msg-workflow-001",
        "request_id": "req-workflow-001",
        "message_type": "REQUEST",
        "timestamp": "2026-10-01T10:00:00Z",
        "sender": "planner-agent",
        "payload": {
            "operation": "START",
            "workflow_id": "workflow-001",
        },
    }

    response = manager.handle_workflow_message(
        message
    )

    assert response["message_type"] == "RESPONSE"
    assert response["request_id"] == "req-workflow-001"
    assert response["payload"]["status"] == "success"
    assert len(response["payload"]["ready_tasks"]) == 1


def test_unknown_workflow_operation_returns_error():
    bus, manager = create_workflow_manager()

    manager.create_workflow(
        "workflow-001",
        "goal-001",
        "Test workflow",
    )

    message = {
        "message_id": "msg-error-001",
        "request_id": "req-error-001",
        "message_type": "REQUEST",
        "timestamp": "2026-10-01T10:00:00Z",
        "sender": "planner-agent",
        "payload": {
            "operation": "DESTROY",
            "workflow_id": "workflow-001",
        },
    }

    response = manager.handle_workflow_message(
        message
    )

    assert response["message_type"] == "ERROR"
    assert response["request_id"] == "req-error-001"
    assert response["payload"]["status"] == "error"

def test_three_step_workflow_dependency_execution():
    bus, manager = create_workflow_manager()

    manager.create_workflow(
        "workflow-003",
        "goal-003",
        "Three-step workflow",
    )

    manager.add_task(
        "workflow-003",
        Task(
            "task-001",
            "Open browser",
        ),
    )

    manager.add_task(
        "workflow-003",
        Task(
            "task-002",
            "Navigate to website",
            dependencies=["task-001"],
        ),
    )

    manager.add_task(
        "workflow-003",
        Task(
            "task-003",
            "Extract page data",
            dependencies=["task-002"],
        ),
    )

    ready_tasks = manager.start_workflow(
        "workflow-003"
    )

    assert [task.task_id for task in ready_tasks] == [
        "task-001"
    ]

    manager.dispatch_task(
        workflow_id="workflow-003",
        task_id="task-001",
        sender_id="workflow-manager-agent",
        receiver_id="executor-agent",
        request_id="req-003-1",
        message_id="msg-003-1",
    )

    ready_tasks = manager.complete_task(
        "workflow-003",
        "task-001",
        result="Browser opened",
    )

    assert [task.task_id for task in ready_tasks] == [
        "task-002"
    ]

    manager.dispatch_task(
        workflow_id="workflow-003",
        task_id="task-002",
        sender_id="workflow-manager-agent",
        receiver_id="executor-agent",
        request_id="req-003-2",
        message_id="msg-003-2",
    )

    ready_tasks = manager.complete_task(
        "workflow-003",
        "task-002",
        result="Website loaded",
    )

    assert [task.task_id for task in ready_tasks] == [
        "task-003"
    ]

    manager.dispatch_task(
        workflow_id="workflow-003",
        task_id="task-003",
        sender_id="workflow-manager-agent",
        receiver_id="executor-agent",
        request_id="req-003-3",
        message_id="msg-003-3",
    )

    ready_tasks = manager.complete_task(
        "workflow-003",
        "task-003",
        result="Data extracted",
    )

    assert ready_tasks == []

    workflow = manager.get_workflow(
        "workflow-003"
    )

    assert workflow.status == "completed"


def test_failed_task_triggers_workflow_failure():
    bus, manager = create_workflow_manager()

    manager.create_workflow(
        "workflow-failure",
        "goal-failure",
        "Failure workflow",
    )

    manager.add_task(
        "workflow-failure",
        Task(
            "task-001",
            "Execute risky operation",
        ),
    )

    manager.start_workflow(
        "workflow-failure"
    )

    manager.dispatch_task(
        workflow_id="workflow-failure",
        task_id="task-001",
        sender_id="workflow-manager-agent",
        receiver_id="executor-agent",
        request_id="req-failure-1",
        message_id="msg-failure-1",
    )

    manager.fail_task(
        "workflow-failure",
        "task-001",
        "Execution failed",
    )

    workflow = manager.get_workflow(
        "workflow-failure"
    )

    task = workflow.get_task(
        "task-001"
    )

    assert task.status == "failed"
    assert task.error == "Execution failed"
    assert workflow.status == "failed"


def test_failed_task_can_be_retried_and_completed():
    bus, manager = create_workflow_manager()

    manager.create_workflow(
        "workflow-retry",
        "goal-retry",
        "Retry workflow",
    )

    manager.add_task(
        "workflow-retry",
        Task(
            "task-001",
            "Execute task",
            max_retries=2,
        ),
    )

    manager.start_workflow(
        "workflow-retry"
    )

    manager.dispatch_task(
        workflow_id="workflow-retry",
        task_id="task-001",
        sender_id="workflow-manager-agent",
        receiver_id="executor-agent",
        request_id="req-retry-1",
        message_id="msg-retry-1",
    )

    manager.fail_task(
        "workflow-retry",
        "task-001",
        "Temporary failure",
    )

    task = manager.retry_task(
        "workflow-retry",
        "task-001",
    )

    assert task.status == "ready"
    assert task.retry_count == 1

    manager.dispatch_task(
        workflow_id="workflow-retry",
        task_id="task-001",
        sender_id="workflow-manager-agent",
        receiver_id="executor-agent",
        request_id="req-retry-2",
        message_id="msg-retry-2",
    )

    manager.complete_task(
        "workflow-retry",
        "task-001",
        result="Successful retry",
    )

    workflow = manager.get_workflow(
        "workflow-retry"
    )

    assert task.status == "completed"
    assert task.retry_count == 1
    assert workflow.status == "completed"


def test_workflow_replanning():
    bus, manager = create_workflow_manager()

    manager.create_workflow(
        "workflow-replan",
        "goal-replan",
        "Replanning workflow",
    )

    manager.add_task(
        "workflow-replan",
        Task(
            "task-001",
            "Original task",
        ),
    )

    manager.start_workflow(
        "workflow-replan"
    )

    manager.dispatch_task(
        workflow_id="workflow-replan",
        task_id="task-001",
        sender_id="workflow-manager-agent",
        receiver_id="executor-agent",
        request_id="req-replan-1",
        message_id="msg-replan-1",
    )

    manager.fail_task(
        "workflow-replan",
        "task-001",
        "Task failed",
    )

    workflow = manager.replan_workflow(
        "workflow-replan"
    )

    assert workflow.status == "replanning"
def test_terminal_workflow_status_is_not_overwritten():
    bus, manager = create_workflow_manager()

    manager.create_workflow(
        "workflow-terminal",
        "goal-terminal",
        "Terminal state test",
    )

    manager.add_task(
        "workflow-terminal",
        Task(
            "task-001",
            "Execute task",
        ),
    )

    manager.start_workflow("workflow-terminal")

    workflow = manager.get_workflow("workflow-terminal")
    workflow.fail()

    workflow.get_task("task-001").status = "completed"
    workflow.check_completion()

    assert workflow.status == "failed"
