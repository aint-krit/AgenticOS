import pytest

from src.agent_bus.bus import AgentBus
from src.agent_runtime.agent import Agent


def create_active_agents():
    agent_a = Agent(
        agent_id="agent-a",
        name="Agent A",
        capabilities=["test.send"],
    )

    agent_b = Agent(
        agent_id="agent-b",
        name="Agent B",
        capabilities=["test.receive"],
    )

    agent_a.start()
    agent_b.start()

    return agent_a, agent_b


def test_agent_registration_and_message():
    bus = AgentBus()
    agent_a, agent_b = create_active_agents()

    bus.register_agent(agent_a)
    bus.register_agent(agent_b)

    response = bus.send_message(
        sender_id="agent-a",
        receiver_id="agent-b",
        message={
            "message_id": "msg-000001",
            "request_id": "req-000001",
            "message_type": "REQUEST",
            "timestamp": "2026-09-28T00:00:00Z",
            "payload": {
                "action": "test_message",
                "data": "Hello from Agent A",
            },
        },
    )

    assert response["message_type"] == "RESPONSE"
    assert response["sender"] == "agent-b"
    assert response["request_id"] == "req-000001"
    assert len(agent_b.received_messages) == 1


def test_invalid_message_is_rejected():
    bus = AgentBus()
    agent_a, agent_b = create_active_agents()

    bus.register_agent(agent_a)
    bus.register_agent(agent_b)

    with pytest.raises(ValueError):
        bus.send_message(
            sender_id="agent-a",
            receiver_id="agent-b",
            message={
                "message_id": "msg-invalid",
                "request_id": "req-invalid",
                "message_type": "REQUEST",
            },
        )


def test_unknown_receiver_is_rejected():
    bus = AgentBus()
    agent_a, _ = create_active_agents()

    bus.register_agent(agent_a)

    message = {
        "message_id": "msg-unknown",
        "request_id": "req-unknown",
        "message_type": "REQUEST",
        "timestamp": "2026-09-28T00:00:00Z",
        "payload": {
            "action": "test_message",
        },
    }

    with pytest.raises(ValueError):
        bus.send_message(
            sender_id="agent-a",
            receiver_id="does-not-exist",
            message=message,
        )

def test_duplicate_registration_is_rejected():
    bus = AgentBus()
    agent_a, _ = create_active_agents()

    bus.register_agent(agent_a)

    with pytest.raises(ValueError):
        bus.register_agent(agent_a)


def test_agent_can_be_unregistered():
    bus = AgentBus()
    agent_a, _ = create_active_agents()

    bus.register_agent(agent_a)

    result = bus.unregister_agent("agent-a")

    assert result["status"] == "unregistered"
    assert result["agent_id"] == "agent-a"
    assert bus.discover_agents() == []

def test_request_id_is_preserved():
    bus = AgentBus()
    agent_a, agent_b = create_active_agents()

    bus.register_agent(agent_a)
    bus.register_agent(agent_b)

    request_id = "req-correlation-001"

    response = bus.send_message(
        sender_id="agent-a",
        receiver_id="agent-b",
        message={
            "message_id": "msg-correlation-001",
            "request_id": request_id,
            "message_type": "REQUEST",
            "timestamp": "2026-09-28T00:00:00Z",
            "payload": {
                "action": "test_correlation",
            },
        },
    )

    assert response["request_id"] == request_id
    assert agent_b.received_messages[0]["request_id"] == request_id

def test_invalid_message_type_is_rejected():
    bus = AgentBus()
    agent_a, agent_b = create_active_agents()

    bus.register_agent(agent_a)
    bus.register_agent(agent_b)

    message = {
        "message_id": "msg-invalid-type",
        "request_id": "req-invalid-type",
        "message_type": "TOTALLY_INVALID",
        "timestamp": "2026-09-28T00:00:00Z",
        "payload": {
            "action": "test",
        },
    }

    with pytest.raises(ValueError):
        bus.send_message(
            sender_id="agent-a",
            receiver_id="agent-b",
            message=message,
        )