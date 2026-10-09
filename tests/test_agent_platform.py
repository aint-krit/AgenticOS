from pathlib import Path

import pytest

from src.agent_bus.bus import AgentBus
from src.agent_runtime.agent import Agent
from src.agents.application_agent import ApplicationAgent
from src.agents.file_agent import FileAgent
from src.capability.registry import CapabilityRegistry
from src.global_agent_manager.manager import GlobalAgentManager
from src.goal_runtime.manager import GoalManager
from src.agent_platform.orchestrator import AgentPlatform, TaskSpec
from src.workflow_runtime.manager import WorkflowManager


def build_platform(tmp_path: Path):
    bus = AgentBus()
    gam = GlobalAgentManager(bus)
    goals = GoalManager(bus)
    workflows = WorkflowManager(bus)
    registry = CapabilityRegistry()

    coordinator = Agent("agent-platform", "Agent Platform", "0.1.0", "core")
    coordinator.start()
    file_agent = FileAgent()
    file_agent.start()
    application = ApplicationAgent()
    application.start()

    gam.register_agent(coordinator)
    gam.register_agent(file_agent)
    gam.register_agent(application)

    platform = AgentPlatform(
        bus=bus,
        agent_manager=gam,
        goal_manager=goals,
        workflow_manager=workflows,
        capability_registry=registry,
    )

    for capability, operation in {
        "create_file": "CREATE_FILE",
        "read_file": "READ_FILE",
        "write_file": "WRITE_FILE",
        "delete_file": "DELETE_FILE",
    }.items():
        platform.register_capability_route("file-agent", capability, operation)
        platform.grant_capability("file-agent", capability)

    platform.register_capability_route("application-agent", "open_browser", "OPEN_BROWSER")
    platform.grant_capability("application-agent", "open_browser")

    return platform, gam, registry, goals, workflows


def test_global_manager_capability_selection(tmp_path):
    _, gam, _, _, _ = build_platform(tmp_path)
    selected = gam.select_agent("create_file")
    assert selected["agent_id"] == "file-agent"


def test_goal_create_through_bus():
    bus = AgentBus()
    manager = GoalManager(bus)
    receiver = Agent("goal-manager-agent", "Goal Manager")
    sender = Agent("agent-platform", "Agent Platform")
    receiver.start()
    sender.start()
    bus.register_agent(sender)
    bus.register_agent(receiver)
    receiver.receive_message = manager.handle_goal_message

    response = bus.send_message(
        "agent-platform",
        "goal-manager-agent",
        {
            "message_id": "msg-goal-create",
            "request_id": "req-goal-create",
            "message_type": "REQUEST",
            "timestamp": "2026-10-06T00:00:00+00:00",
            "payload": {
                "operation": "CREATE",
                "goal_id": "goal-001",
                "description": "Create a project file",
            },
        },
    )
    assert response["message_type"] == "RESPONSE"
    assert response["payload"]["operation"] == "CREATE"
    assert "goal-001" in manager.goals


def test_end_to_end_create_file(tmp_path):
    platform, _, registry, goals, workflows = build_platform(tmp_path)
    target = tmp_path / "AgenticOS" / "hello.txt"

    result = platform.execute_intent(
        intent="create_file",
        description="Create the AgenticOS project file",
        payload={"path": str(target), "content": "AgenticOS v0.1"},
        request_id="req-e2e-create",
    )

    assert result["status"] == "completed"
    assert result["verified"] is True
    assert target.read_text(encoding="utf-8") == "AgenticOS v0.1"
    assert result["goal"]["status"] == "completed"
    assert result["workflow"]["status"] == "completed"
    assert registry.permission_manager.is_allowed("file-agent", "create_file")
    assert goals.goals[result["goal"]["goal_id"]].status == "completed"
    assert workflows.workflows[result["workflow"]["workflow_id"]].status == "completed"
    assert any(item["stage"] == "agent_bus.dispatch" for item in result["trace"])


def test_unauthorized_capability_never_reaches_agent(tmp_path):
    platform, _, registry, _, _ = build_platform(tmp_path)
    registry.revoke_permission("file-agent", "create_file")
    target = tmp_path / "blocked.txt"

    with pytest.raises(PermissionError):
        platform.execute_intent(
            intent="create_file",
            description="Unauthorized file creation",
            payload={"path": str(target), "content": "blocked"},
            request_id="req-denied",
        )

    assert not target.exists()


def test_multi_step_dependency_execution(tmp_path):
    platform, _, _, goals, workflows = build_platform(tmp_path)
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    goal = goals.create_goal("goal-multi", "Create two files")

    result = platform.execute_workflow(
        goal_id=goal.goal_id,
        workflow_id="workflow-multi",
        request_id="req-multi",
        tasks=[
            TaskSpec(
                task_id="task-1",
                description="Create first file",
                capability="create_file",
                operation="CREATE_FILE",
                payload={"path": str(first), "content": "one"},
            ),
            TaskSpec(
                task_id="task-2",
                description="Create second file",
                capability="create_file",
                operation="CREATE_FILE",
                payload={"path": str(second), "content": "two"},
                dependencies=["task-1"],
            ),
        ],
    )

    assert result["verified"] is True
    assert first.exists() and second.exists()
    assert workflows.workflows["workflow-multi"].tasks["task-1"].status == "completed"
    assert workflows.workflows["workflow-multi"].tasks["task-2"].status == "completed"

def test_unauthorized_capability_never_reaches_agent(tmp_path):
    platform, _, registry, _, _ = build_platform(tmp_path)
    registry.revoke_permission("file-agent", "create_file")
    target = tmp_path / "blocked.txt"

    with pytest.raises(PermissionError):
        platform.execute_intent(
            intent="create_file",
            description="Unauthorized file creation",
            payload={"path": str(target), "content": "blocked"},
            request_id="req-denied",
        )

    assert not target.exists()

    trace = platform.trace["req-denied"]
    assert any(
        event["stage"] == "security.authorization"
        and event["status"] == "denied"
        for event in trace
    )
    assert any(
        event["stage"] == "workflow.task"
        and event["status"] == "failed"
        for event in trace
    )
    assert not any(
        event["stage"] == "agent_bus.dispatch"
        for event in trace
    )

    audit = registry.get_audit_log("req-denied")
    assert len(audit) == 1
    assert audit[0]["outcome"] == "denied"
    assert audit[0]["error_type"] == "PermissionError"

def test_route_owner_mismatch_is_denied_before_dispatch(tmp_path):
    platform, _, registry, _, _ = build_platform(tmp_path)
    target = tmp_path / "route-owner-blocked.txt"

    # Simulate the manager selecting an agent other than the registered
    # owner of the create_file capability route.
    platform.select_agent = lambda capability: "application-agent"

    with pytest.raises(PermissionError, match="does not match route owner"):
        platform.execute_intent(
            intent="create_file",
            description="Reject a mismatched route owner",
            payload={
                "path": str(target),
                "content": "must not be written",
            },
            request_id="req-route-owner-mismatch",
        )

    assert not target.exists()

    trace = platform.trace["req-route-owner-mismatch"]
    denied = [
        event for event in trace
        if event["stage"] == "security.authorization"
        and event["status"] == "denied"
    ]
    assert len(denied) == 1
    assert denied[0]["agent_id"] == "application-agent"
    assert denied[0]["route_owner"] == "file-agent"

    assert not any(
        event["stage"] == "agent_bus.dispatch"
        for event in trace
    )

    audit = registry.get_audit_log("req-route-owner-mismatch")
    assert len(audit) == 1
    assert audit[0]["outcome"] == "denied"