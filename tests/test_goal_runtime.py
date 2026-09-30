import pytest

from src.agent_bus.bus import AgentBus
from src.agent_runtime.agent import Agent
from src.goal_runtime.goal import Goal
from src.goal_runtime.manager import GoalManager


def create_manager():
    bus = AgentBus()

    planner = Agent(
        agent_id="planner-agent",
        name="Planner Agent",
    )

    goal_manager = Agent(
        agent_id="goal-manager-agent",
        name="Goal Manager Agent",
    )

    planner.start()
    goal_manager.start()

    bus.register_agent(planner)
    bus.register_agent(goal_manager)

    return bus, GoalManager(bus)


def test_goal_creation():
    bus, manager = create_manager()

    goal = manager.create_goal(
        goal_id="goal-001",
        description="Create AgenticOS project",
    )

    assert goal.goal_id == "goal-001"
    assert goal.status == "created"


def test_goal_activation():
    bus, manager = create_manager()

    goal = manager.create_goal(
        "goal-001",
        "Create AgenticOS project",
    )

    manager.handle_operation(
        "goal-001",
        "ACTIVATE",
    )

    assert goal.status == "active"


def test_goal_update():
    bus, manager = create_manager()

    goal = manager.create_goal(
        "goal-001",
        "Create AgenticOS project",
    )

    manager.handle_operation(
        "goal-001",
        "UPDATE",
        description="Build AgenticOS runtime",
        priority="high",
    )

    assert goal.description == "Build AgenticOS runtime"
    assert goal.priority == "high"


def test_goal_pause():
    bus, manager = create_manager()

    goal = manager.create_goal(
        "goal-001",
        "Create AgenticOS project",
    )

    manager.handle_operation("goal-001", "ACTIVATE")
    manager.handle_operation("goal-001", "PAUSE")

    assert goal.status == "paused"


def test_goal_cancel():
    bus, manager = create_manager()

    goal = manager.create_goal(
        "goal-001",
        "Create AgenticOS project",
    )

    manager.handle_operation("goal-001", "CANCEL")

    assert goal.status == "cancelled"


def test_goal_complete():
    bus, manager = create_manager()

    goal = manager.create_goal(
        "goal-001",
        "Create AgenticOS project",
    )

    manager.handle_operation("goal-001", "ACTIVATE")
    manager.handle_operation("goal-001", "COMPLETE")

    assert goal.status == "completed"


def test_goal_fail():
    bus, manager = create_manager()

    goal = manager.create_goal(
        "goal-001",
        "Create AgenticOS project",
    )

    manager.handle_operation("goal-001", "ACTIVATE")
    manager.handle_operation("goal-001", "FAIL")

    assert goal.status == "failed"


def test_goal_replan():
    bus, manager = create_manager()

    goal = manager.create_goal(
        "goal-001",
        "Create AgenticOS project",
    )

    manager.handle_operation("goal-001", "ACTIVATE")
    manager.handle_operation("goal-001", "REPLAN")

    assert goal.status == "replanning"


def test_invalid_goal_operation():
    bus, manager = create_manager()

    manager.create_goal(
        "goal-001",
        "Create AgenticOS project",
    )

    with pytest.raises(ValueError, match="Unknown goal operation"):
        manager.handle_operation(
            "goal-001",
            "DESTROY",
        )


def test_duplicate_goal_is_rejected():
    bus, manager = create_manager()

    manager.create_goal(
        "goal-001",
        "Create AgenticOS project",
    )

    with pytest.raises(ValueError, match="already exists"):
        manager.create_goal(
            "goal-001",
            "Another goal",
        )


def test_goal_message_through_bus():
    bus, manager = create_manager()

    manager.create_goal(
        "goal-001",
        "Create AgenticOS project",
    )

    response = manager.send_goal_message(
        sender_id="planner-agent",
        receiver_id="goal-manager-agent",
        operation="ACTIVATE",
        goal_id="goal-001",
        request_id="req-goal-001",
        message_id="msg-goal-001",
    )

    received = bus.agents["goal-manager-agent"].received_messages

    assert response["payload"]["status"] == "received"
    assert received[0]["payload"]["operation"] == "ACTIVATE"


def test_goal_message_handler():
    bus, manager = create_manager()

    goal = manager.create_goal(
        "goal-001",
        "Create AgenticOS project",
    )

    message = {
        "message_id": "msg-goal-002",
        "request_id": "req-goal-002",
        "message_type": "REQUEST",
        "timestamp": "2026-09-30T10:00:00Z",
        "sender": "planner-agent",
        "payload": {
            "operation": "ACTIVATE",
            "goal_id": "goal-001",
        },
    }

    response = manager.handle_goal_message(message)

    assert goal.status == "active"
    assert response["message_type"] == "RESPONSE"
    assert response["request_id"] == "req-goal-002"
    assert response["payload"]["status"] == "success"
def test_unknown_goal_returns_error_response():
    bus, manager = create_manager()

    message = {
        "message_id": "msg-error-001",
        "request_id": "req-error-001",
        "message_type": "REQUEST",
        "timestamp": "2026-09-30T10:00:00Z",
        "sender": "planner-agent",
        "payload": {
            "operation": "COMPLETE",
            "goal_id": "does-not-exist",
        },
    }

    response = manager.handle_goal_message(message)

    assert response["message_type"] == "ERROR"
    assert response["request_id"] == "req-error-001"
    assert response["receiver"] == "planner-agent"
    assert response["payload"]["status"] == "error"


def test_invalid_goal_operation_returns_error_response():
    bus, manager = create_manager()

    manager.create_goal(
        "goal-001",
        "Create AgenticOS project",
    )

    message = {
        "message_id": "msg-error-002",
        "request_id": "req-error-002",
        "message_type": "REQUEST",
        "timestamp": "2026-09-30T10:00:00Z",
        "sender": "planner-agent",
        "payload": {
            "operation": "DESTROY",
            "goal_id": "goal-001",
        },
    }

    response = manager.handle_goal_message(message)

    assert response["message_type"] == "ERROR"
    assert response["payload"]["error_type"] == "ValueError"


def test_missing_goal_id_returns_error_response():
    bus, manager = create_manager()

    message = {
        "message_id": "msg-error-003",
        "request_id": "req-error-003",
        "message_type": "REQUEST",
        "timestamp": "2026-09-30T10:00:00Z",
        "sender": "planner-agent",
        "payload": {
            "operation": "ACTIVATE",
        },
    }

    response = manager.handle_goal_message(message)

    assert response["message_type"] == "ERROR"
    assert response["payload"]["status"] == "error"


def test_goal_lifecycle_history():
    bus, manager = create_manager()

    goal = manager.create_goal(
        "goal-001",
        "Create AgenticOS project",
    )

    manager.handle_operation("goal-001", "ACTIVATE")
    manager.handle_operation("goal-001", "PAUSE")
    manager.handle_operation("goal-001", "REPLAN")
    manager.handle_operation("goal-001", "ACTIVATE")
    manager.handle_operation("goal-001", "COMPLETE")

    assert goal.status == "completed"
    assert len(goal.history) == 5