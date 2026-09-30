import pytest

from src.agent_bus.bus import AgentBus
from src.agent_runtime.agent import Agent
from src.intent.router import IntentRouter


def create_router():
    bus = AgentBus()

    planner = Agent(
        agent_id="planner-agent",
        name="Planner Agent",
    )

    application = Agent(
        agent_id="application-agent",
        name="Application Agent",
    )

    file_agent = Agent(
        agent_id="file-agent",
        name="File Agent",
    )

    memory = Agent(
        agent_id="memory-agent",
        name="Memory Agent",
    )

    executor = Agent(
        agent_id="executor-agent",
        name="Executor Agent",
    )

    for agent in [
        planner,
        application,
        file_agent,
        memory,
        executor,
    ]:
        agent.start()
        bus.register_agent(agent)

    return bus, IntentRouter(bus)


def make_message(intent, request_id="req-intent-001"):
    return {
        "message_id": "msg-intent-001",
        "request_id": request_id,
        "message_type": "REQUEST",
        "timestamp": "2026-09-29T10:00:00Z",
        "payload": {
            "intent": intent,
        },
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
        make_message(
            "create_file",
            request_id="req-create-file-123",
        ),
        sender_id="planner-agent",
    )

    assert response["request_id"] == "req-create-file-123"


def test_unknown_intent_is_rejected():
    bus, router = create_router()

    with pytest.raises(ValueError, match="Unknown intent"):
        router.route(
            make_message("launch_spaceship"),
            sender_id="planner-agent",
        )


def test_empty_intent_is_rejected():
    bus, router = create_router()

    with pytest.raises(ValueError, match="non-empty"):
        router.route(
            make_message(""),
            sender_id="planner-agent",
        )


def test_malformed_intent_message_is_rejected():
    bus, router = create_router()

    malformed_message = {
        "message_id": "msg-bad",
        "request_id": "req-bad",
        "message_type": "REQUEST",
        "timestamp": "2026-09-29T10:00:00Z",
    }

    with pytest.raises(ValueError, match="missing required fields"):
        router.route(
            malformed_message,
            sender_id="planner-agent",
        )


def test_invalid_message_type_is_rejected():
    bus, router = create_router()

    message = make_message("open_browser")
    message["message_type"] = "EVENT"

    with pytest.raises(ValueError, match="REQUEST"):
        router.route(
            message,
            sender_id="planner-agent",
        )


def test_unknown_target_agent_is_rejected():
    bus, router = create_router()

    router.INTENT_TO_AGENT["test_unknown"] = "unknown-agent"

    with pytest.raises(
        ValueError,
        match="not registered",
    ):
        router.route(
            make_message("test_unknown"),
            sender_id="planner-agent",
        )


def test_unavailable_target_agent_is_rejected():
    bus, router = create_router()

    application = bus.agents["application-agent"]
    application.stop()

    with pytest.raises(
        RuntimeError,
        match="not active",
    ):
        router.route(
            make_message("open_browser"),
            sender_id="planner-agent",
        )


def test_ambiguous_empty_payload_is_rejected():
    bus, router = create_router()

    message = make_message("open_browser")
    message["payload"] = {}

    with pytest.raises(
        ValueError,
        match="non-empty 'intent'",
    ):
        router.route(
            message,
            sender_id="planner-agent",
        )


def test_non_dictionary_payload_is_rejected():
    bus, router = create_router()

    message = make_message("open_browser")
    message["payload"] = "open browser"

    with pytest.raises(
        ValueError,
        match="payload must be a dictionary",
    ):
        router.route(
            message,
            sender_id="planner-agent",
        )


def test_sender_must_be_registered():
    bus, router = create_router()

    with pytest.raises(
        ValueError,
        match="Sender 'unknown-sender' is not registered",
    ):
        router.route(
            make_message("open_browser"),
            sender_id="unknown-sender",
        )


def test_sender_must_be_active():
    bus, router = create_router()

    planner = bus.agents["planner-agent"]
    planner.pause()

    with pytest.raises(
        RuntimeError,
        match="Sender 'planner-agent' is not active",
    ):
        router.route(
            make_message("open_browser"),
            sender_id="planner-agent",
        )