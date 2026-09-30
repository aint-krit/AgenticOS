import pytest

from src.agent_bus.bus import AgentBus
from src.agent_runtime.agent import Agent
from src.intent.router import IntentRouter


def create_router():
    bus = AgentBus()

    agents = [
        Agent("planner-agent", "Planner Agent"),
        Agent("application-agent", "Application Agent"),
        Agent("file-agent", "File Agent"),
        Agent("memory-agent", "Memory Agent"),
        Agent("executor-agent", "Executor Agent"),
    ]

    for agent in agents:
        agent.start()
        bus.register_agent(agent)

    return bus, IntentRouter(bus)


def make_message(intent, request_id="req-intent-001"):
    return {
        "message_id": "msg-intent-001",
        "request_id": request_id,
        "message_type": "REQUEST",
        "timestamp": "2026-09-29T10:00:00Z",
        "payload": {"intent": intent},
    }


def test_valid_intent_is_resolved():
    bus, router = create_router()

    assert router.resolve("open_browser") == "application-agent"
    assert router.resolve("create_file") == "file-agent"


def test_valid_intent_is_routed():
    bus, router = create_router()

    response = router.route(
        make_message("open_browser"),
        sender_id="planner-agent",
    )

    assert response["payload"]["status"] == "received"
    assert response["sender"] == "application-agent"


def test_request_id_is_preserved():
    bus, router = create_router()

    response = router.route(
        make_message("create_file", "req-create-file-123"),
        sender_id="planner-agent",
    )

    assert response["request_id"] == "req-create-file-123"


def test_unknown_intent_returns_error():
    bus, router = create_router()

    response = router.route(
        make_message("launch_spaceship"),
        sender_id="planner-agent",
    )

    assert response["message_type"] == "ERROR"
    assert response["receiver"] == "planner-agent"
    assert response["payload"]["status"] == "error"


def test_empty_intent_returns_error():
    bus, router = create_router()

    response = router.route(
        make_message(""),
        sender_id="planner-agent",
    )

    assert response["message_type"] == "ERROR"
    assert response["payload"]["status"] == "error"


def test_malformed_request_returns_error():
    bus, router = create_router()

    message = {
        "message_id": "msg-bad",
        "request_id": "req-bad",
        "message_type": "REQUEST",
        "timestamp": "2026-09-29T10:00:00Z",
    }

    response = router.route(
        message,
        sender_id="planner-agent",
    )

    assert response["message_type"] == "ERROR"
    assert response["request_id"] == "req-bad"


def test_invalid_message_type_returns_error():
    bus, router = create_router()

    message = make_message("open_browser")
    message["message_type"] = "EVENT"

    response = router.route(
        message,
        sender_id="planner-agent",
    )

    assert response["message_type"] == "ERROR"


def test_unknown_target_agent_returns_error():
    bus, router = create_router()

    router.INTENT_TO_AGENT["test_unknown"] = "unknown-agent"

    response = router.route(
        make_message("test_unknown"),
        sender_id="planner-agent",
    )

    assert response["message_type"] == "ERROR"
    assert "not registered" in response["payload"]["error"]


def test_unavailable_target_agent_returns_error():
    bus, router = create_router()

    bus.agents["application-agent"].stop()

    response = router.route(
        make_message("open_browser"),
        sender_id="planner-agent",
    )

    assert response["message_type"] == "ERROR"
    assert "not active" in response["payload"]["error"]


def test_ambiguous_empty_payload_returns_error():
    bus, router = create_router()

    message = make_message("open_browser")
    message["payload"] = {}

    response = router.route(
        message,
        sender_id="planner-agent",
    )

    assert response["message_type"] == "ERROR"


def test_non_dictionary_payload_returns_error():
    bus, router = create_router()

    message = make_message("open_browser")
    message["payload"] = "open browser"

    response = router.route(
        message,
        sender_id="planner-agent",
    )

    assert response["message_type"] == "ERROR"


def test_sender_must_be_registered():
    bus, router = create_router()

    response = router.route(
        make_message("open_browser"),
        sender_id="unknown-sender",
    )

    assert response["message_type"] == "ERROR"
    assert "not registered" in response["payload"]["error"]


def test_sender_must_be_active():
    bus, router = create_router()

    bus.agents["planner-agent"].pause()

    response = router.route(
        make_message("open_browser"),
        sender_id="planner-agent",
    )

    assert response["message_type"] == "ERROR"
    assert "not active" in response["payload"]["error"]


def test_error_response_preserves_request_id():
    bus, router = create_router()

    response = router.route(
        make_message(
            "unknown_intent",
            request_id="req-error-123",
        ),
        sender_id="planner-agent",
    )

    assert response["message_type"] == "ERROR"
    assert response["request_id"] == "req-error-123"
    assert response["receiver"] == "planner-agent"
    assert response["sender"] == "intent-router"


def test_error_response_contains_error_type():
    bus, router = create_router()

    response = router.route(
        make_message("unknown_intent"),
        sender_id="planner-agent",
    )

    assert response["payload"]["error_type"] == "ValueError"
    assert response["payload"]["status"] == "error"