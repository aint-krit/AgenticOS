from src.agent_bus.bus import AgentBus
from src.agent_runtime.agent import Agent
from src.global_agent_manager.manager import GlobalAgentManager


def create_global_manager():
    bus = AgentBus()

    manager = GlobalAgentManager(
        bus=bus,
        manager_agent_id="global-agent-manager",
    )

    return bus, manager


def create_agent(
    agent_id: str,
    name: str,
    agent_type: str = "specialized",
    capabilities: list[str] | None = None,
):
    agent = Agent(
        agent_id=agent_id,
        name=name,
        agent_type=agent_type,
        capabilities=capabilities or [],
    )

    agent.start()

    return agent


def test_agent_registration():
    bus, manager = create_global_manager()

    agent = create_agent(
        "planner-agent",
        "Planner Agent",
        "core",
        ["planning"],
    )

    registration = manager.register_agent(agent)

    assert registration["agent_id"] == "planner-agent"
    assert registration["name"] == "Planner Agent"
    assert registration["type"] == "core"
    assert registration["status"] == "active"
    assert registration["capabilities"] == ["planning"]

    assert "planner-agent" in manager.registry
    assert "planner-agent" in bus.agents


def test_duplicate_agent_registration_is_rejected():
    bus, manager = create_global_manager()

    agent = create_agent(
        "planner-agent",
        "Planner Agent",
    )

    manager.register_agent(agent)

    try:
        manager.register_agent(agent)
        assert False, "Expected duplicate registration to fail."
    except ValueError as error:
        assert "already registered" in str(error)


def test_agent_discovery():
    bus, manager = create_global_manager()

    planner = create_agent(
        "planner-agent",
        "Planner Agent",
        "core",
        ["planning"],
    )

    executor = create_agent(
        "executor-agent",
        "Executor Agent",
        "specialized",
        ["task_execution"],
    )

    manager.register_agent(planner)
    manager.register_agent(executor)

    agents = manager.discover_agents()

    agent_ids = {
        agent["agent_id"]
        for agent in agents
    }

    assert agent_ids == {
        "planner-agent",
        "executor-agent",
    }


def test_get_registered_agent():
    bus, manager = create_global_manager()

    agent = create_agent(
        "memory-agent",
        "Memory Agent",
        "specialized",
        ["memory_read", "memory_write"],
    )

    manager.register_agent(agent)

    registration = manager.get_agent(
        "memory-agent"
    )

    assert registration["agent_id"] == "memory-agent"
    assert registration["capabilities"] == [
        "memory_read",
        "memory_write",
    ]


def test_unknown_agent_lookup_is_rejected():
    bus, manager = create_global_manager()

    try:
        manager.get_agent("unknown-agent")
        assert False, "Expected unknown agent lookup to fail."
    except ValueError as error:
        assert "not registered" in str(error)


def test_agent_status_is_reported():
    bus, manager = create_global_manager()

    agent = create_agent(
        "executor-agent",
        "Executor Agent",
    )

    manager.register_agent(agent)

    assert manager.get_agent_status(
        "executor-agent"
    ) == "active"


def test_agent_can_be_paused():
    bus, manager = create_global_manager()

    agent = create_agent(
        "executor-agent",
        "Executor Agent",
    )

    manager.register_agent(agent)

    registration = manager.update_agent_status(
        "executor-agent",
        "paused",
    )

    assert registration["status"] == "paused"
    assert manager.get_agent_status(
        "executor-agent"
    ) == "paused"


def test_agent_can_be_resumed():
    bus, manager = create_global_manager()

    agent = create_agent(
        "executor-agent",
        "Executor Agent",
    )

    manager.register_agent(agent)

    manager.update_agent_status(
        "executor-agent",
        "paused",
    )

    registration = manager.update_agent_status(
        "executor-agent",
        "active",
    )

    assert registration["status"] == "active"
    assert manager.get_agent_status(
        "executor-agent"
    ) == "active"


def test_agent_can_be_marked_unhealthy():
    bus, manager = create_global_manager()

    agent = create_agent(
        "executor-agent",
        "Executor Agent",
    )

    manager.register_agent(agent)

    registration = manager.update_agent_status(
        "executor-agent",
        "unhealthy",
    )

    assert registration["status"] == "unhealthy"
    assert manager.get_agent_status(
        "executor-agent"
    ) == "unhealthy"


def test_invalid_agent_status_is_rejected():
    bus, manager = create_global_manager()

    agent = create_agent(
        "executor-agent",
        "Executor Agent",
    )

    manager.register_agent(agent)

    try:
        manager.update_agent_status(
            "executor-agent",
            "invalid-status",
        )
        assert False, "Expected invalid status to fail."
    except ValueError as error:
        assert "Invalid agent status" in str(error)


def test_agent_heartbeat():
    bus, manager = create_global_manager()

    agent = create_agent(
        "monitor-agent",
        "Monitor Agent",
        "core",
        ["monitoring"],
    )

    manager.register_agent(agent)

    heartbeat = manager.heartbeat(
        "monitor-agent"
    )

    assert heartbeat["status"] == "healthy"
    assert heartbeat["agent_id"] == "monitor-agent"
    assert heartbeat["agent_status"] == "active"
    assert heartbeat["timestamp"] is not None

    assert (
        manager.registry["monitor-agent"]
        ["last_heartbeat"]
        is not None
    )


def test_unregister_agent():
    bus, manager = create_global_manager()

    agent = create_agent(
        "file-agent",
        "File Agent",
        "specialized",
        ["file_operations"],
    )

    manager.register_agent(agent)

    result = manager.unregister_agent(
        "file-agent"
    )

    assert result["status"] == "unregistered"
    assert "file-agent" not in manager.registry
    assert "file-agent" not in bus.agents


def test_unknown_agent_cannot_be_unregistered():
    bus, manager = create_global_manager()

    try:
        manager.unregister_agent(
            "unknown-agent"
        )
        assert False, "Expected unknown agent removal to fail."
    except ValueError as error:
        assert "not registered" in str(error)


def test_agent_communication_through_global_manager():
    bus, manager = create_global_manager()

    sender = create_agent(
        "planner-agent",
        "Planner Agent",
        "core",
        ["planning"],
    )

    receiver = create_agent(
        "executor-agent",
        "Executor Agent",
        "specialized",
        ["task_execution"],
    )

    manager.register_agent(sender)
    manager.register_agent(receiver)

    message = {
        "message_id": "msg-global-001",
        "request_id": "req-global-001",
        "message_type": "REQUEST",
        "timestamp": "2026-10-02T10:00:00Z",
        "payload": {
            "operation": "EXECUTE_TASK",
            "task_id": "task-001",
        },
    }

    response = manager.send_message(
        sender_id="planner-agent",
        receiver_id="executor-agent",
        message=message,
    )

    assert response["message_type"] == "RESPONSE"
    assert response["request_id"] == "req-global-001"
    assert response["sender"] == "executor-agent"

    assert len(receiver.received_messages) == 1
    assert (
        receiver.received_messages[0]["request_id"]
        == "req-global-001"
    )


def test_unregistered_sender_cannot_communicate():
    bus, manager = create_global_manager()

    receiver = create_agent(
        "executor-agent",
        "Executor Agent",
    )

    manager.register_agent(receiver)

    message = {
        "message_id": "msg-global-002",
        "request_id": "req-global-002",
        "message_type": "REQUEST",
        "timestamp": "2026-10-02T10:00:00Z",
        "payload": {
            "operation": "EXECUTE_TASK",
        },
    }

    try:
        manager.send_message(
            sender_id="unknown-agent",
            receiver_id="executor-agent",
            message=message,
        )
        assert False, "Expected unregistered sender to fail."
    except ValueError as error:
        assert "not registered" in str(error)


def test_paused_agent_cannot_communicate():
    bus, manager = create_global_manager()

    sender = create_agent(
        "planner-agent",
        "Planner Agent",
    )

    receiver = create_agent(
        "executor-agent",
        "Executor Agent",
    )

    manager.register_agent(sender)
    manager.register_agent(receiver)

    manager.update_agent_status(
        "planner-agent",
        "paused",
    )

    message = {
        "message_id": "msg-global-003",
        "request_id": "req-global-003",
        "message_type": "REQUEST",
        "timestamp": "2026-10-02T10:00:00Z",
        "payload": {
            "operation": "EXECUTE_TASK",
        },
    }

    try:
        manager.send_message(
            sender_id="planner-agent",
            receiver_id="executor-agent",
            message=message,
        )
        assert False, "Expected paused sender to fail."
    except RuntimeError as error:
        assert "not active" in str(error)