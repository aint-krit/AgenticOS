from pathlib import Path

import pytest
from src.intent.router import IntentRouter
from src.agent_bus.bus import AgentBus
from src.agents.application_agent import ApplicationAgent
from src.agents.ecosystem import create_core_agents
from src.agents.executor_agent import ExecutorAgent
from src.agents.file_agent import FileAgent
from src.agents.memory_agent import MemoryAgent
from src.agents.monitor_agent import MonitorAgent
from src.agents.planner_agent import PlannerAgent
from src.agents.security_agent import SecurityAgent
from src.global_agent_manager.manager import GlobalAgentManager


def make_message(
    sender: str,
    receiver: str,
    operation: str,
    payload: dict,
) -> dict:
    return {
        "message_id": f"msg-{operation.lower()}",
        "request_id": f"req-{operation.lower()}",
        "message_type": "REQUEST",
        "timestamp": "2026-10-03T00:00:00+00:00",
        "payload": {
            "operation": operation,
            **payload,
        },
        "sender": sender,
        "receiver": receiver,
    }


def activate(agent):
    agent.start()
    return agent


def test_core_agent_factory_creates_all_agents():
    agents = create_core_agents()

    assert len(agents) == 7

    ids = {
        agent.agent_id
        for agent in agents
    }

    assert ids == {
        "planner-agent",
        "executor-agent",
        "monitor-agent",
        "memory-agent",
        "security-agent",
        "application-agent",
        "file-agent",
    }


def test_all_agents_register_with_global_manager():
    bus = AgentBus()
    manager = GlobalAgentManager(bus)

    agents = create_core_agents()

    for agent in agents:
        manager.register_agent(agent)

    discovered = manager.discover_agents()

    assert len(discovered) == 7


def test_planner_creates_plan():
    agent = activate(PlannerAgent())

    result = agent.plan(
        goal_id="goal-1",
        description="Open browser",
    )

    assert result["status"] == "planned"
    assert result["tasks"][0]["description"] == "Open browser"


def test_executor_executes_task():
    agent = activate(ExecutorAgent())

    result = agent.execute_task(
        task_id="task-1",
        description="Open browser",
    )

    assert result["status"] == "completed"
    assert result["task_id"] == "task-1"


def test_monitor_records_event():
    agent = activate(MonitorAgent())

    event = agent.record_event(
        event_type="TASK_STARTED",
        source="executor-agent",
    )

    assert event["event_type"] == "TASK_STARTED"
    assert len(agent.get_events()) == 1


def test_memory_store_and_retrieve():
    agent = activate(MemoryAgent())

    stored = agent.remember(
        "user_name",
        "Krithikesh",
    )

    retrieved = agent.retrieve(
        "user_name",
    )

    assert stored["status"] == "stored"
    assert retrieved["status"] == "found"
    assert retrieved["value"] == "Krithikesh"


def test_memory_clear():
    agent = activate(MemoryAgent())

    agent.remember(
        "temporary",
        "value",
    )

    result = agent.clear(
        "temporary",
    )

    assert result["status"] == "deleted"
    assert agent.retrieve("temporary")["status"] == "not_found"


def test_security_authorizes_granted_capability():
    agent = activate(SecurityAgent())

    agent.grant(
        "application-agent",
        "open_browser",
    )

    result = agent.authorize(
        "application-agent",
        "open_browser",
    )

    assert result["authorized"] is True


def test_security_rejects_missing_capability():
    agent = activate(SecurityAgent())

    result = agent.authorize(
        "application-agent",
        "delete_system",
    )

    assert result["authorized"] is False


def test_application_agent_capabilities():
    agent = ApplicationAgent()

    assert "open_browser" in agent.capabilities
    assert "launch_application" in agent.capabilities


def test_file_agent_create_read_write_delete(
    tmp_path: Path,
):
    agent = activate(FileAgent())

    file_path = tmp_path / "test.txt"

    created = agent.create_file(
        str(file_path),
        "hello",
    )

    assert created["status"] == "created"

    read = agent.read_file(
        str(file_path),
    )

    assert read["content"] == "hello"

    written = agent.write_file(
        str(file_path),
        "updated",
    )

    assert written["status"] == "written"

    assert agent.read_file(
        str(file_path)
    )["content"] == "updated"

    deleted = agent.delete_file(
        str(file_path),
    )

    assert deleted["status"] == "deleted"
    assert not file_path.exists()


def test_agent_bus_routes_between_specialized_agents():
    bus = AgentBus()

    planner = activate(PlannerAgent())
    executor = activate(ExecutorAgent())

    bus.register_agent(planner)
    bus.register_agent(executor)

    message = make_message(
        sender="planner-agent",
        receiver="executor-agent",
        operation="EXECUTE_TASK",
        payload={
            "task_id": "task-1",
            "description": "Test execution",
        },
    )

    response = bus.send_message(
        sender_id="planner-agent",
        receiver_id="executor-agent",
        message=message,
    )

    assert response["message_type"] == "RESPONSE"
    assert response["payload"]["status"] == "completed"


def test_memory_agent_receives_bus_message():
    bus = AgentBus()

    sender = activate(PlannerAgent())
    memory = activate(MemoryAgent())

    bus.register_agent(sender)
    bus.register_agent(memory)

    message = make_message(
        sender="planner-agent",
        receiver="memory-agent",
        operation="REMEMBER",
        payload={
            "key": "test",
            "value": "stored-value",
        },
    )

    response = bus.send_message(
        sender_id="planner-agent",
        receiver_id="memory-agent",
        message=message,
    )

    assert response["payload"]["status"] == "stored"
    assert memory.retrieve("test")["value"] == "stored-value"


def test_application_agent_message_without_launching_browser(
    monkeypatch,
):
    agent = activate(ApplicationAgent())

    monkeypatch.setattr(
        "webbrowser.open",
        lambda url: True,
    )

    message = make_message(
        sender="planner-agent",
        receiver="application-agent",
        operation="OPEN_BROWSER",
        payload={
            "url": "about:blank",
        },
    )

    response = agent.receive_message(message)

    assert response["message_type"] == "RESPONSE"
    assert response["payload"]["status"] == "completed"
    assert response["payload"]["opened"] is True

def test_global_manager_tracks_live_agent_status():
    bus = AgentBus()
    manager = GlobalAgentManager(bus)

    agents = create_core_agents()

    for agent in agents:
        manager.register_agent(agent)
        agent.start()

    for agent in agents:
        status = manager.get_agent_status(
            agent.agent_id
        )
        assert status == "active"


def test_global_manager_can_pause_and_resume_agent():
    bus = AgentBus()
    manager = GlobalAgentManager(bus)

    executor = ExecutorAgent()

    manager.register_agent(executor)

    executor.start()

    paused = manager.update_agent_status(
        "executor-agent",
        "paused",
    )

    assert paused["status"] == "paused"
    assert manager.get_agent_status(
        "executor-agent"
    ) == "paused"

    resumed = manager.update_agent_status(
        "executor-agent",
        "active",
    )

    assert resumed["status"] == "active"
    assert manager.get_agent_status(
        "executor-agent"
    ) == "active"

def test_intent_router_routes_open_browser_to_application_agent(
    monkeypatch,
):
    bus = AgentBus()
    manager = GlobalAgentManager(bus)

    agents = create_core_agents()

    for agent in agents:
        manager.register_agent(agent)
        agent.start()

    monkeypatch.setattr(
        "webbrowser.open",
        lambda url: True,
    )

    router = IntentRouter(bus)

    message = {
        "message_id": "msg-e2e-browser",
        "request_id": "req-e2e-browser",
        "message_type": "REQUEST",
        "timestamp": "2026-10-03T00:00:00+00:00",
        "payload": {
            "intent": "open_browser",
            "operation": "OPEN_BROWSER",
            "url": "https://www.google.com",
        },
    }

    response = router.route(
        message=message,
        sender_id="planner-agent",
    )

    assert response["message_type"] == "RESPONSE"
    assert response["sender"] == "application-agent"
    assert response["receiver"] == "planner-agent"
    assert response["payload"]["status"] == "completed"
    assert response["payload"]["action"] == "open_browser"


def test_intent_router_rejects_unknown_agent_route():
    bus = AgentBus()

    planner = PlannerAgent()
    planner.start()

    bus.register_agent(planner)

    router = IntentRouter(bus)

    message = {
        "message_id": "msg-invalid-intent",
        "request_id": "req-invalid-intent",
        "message_type": "REQUEST",
        "timestamp": "2026-10-03T00:00:00+00:00",
        "payload": {
            "intent": "unknown_action",
        },
    }

    response = router.route(
        message=message,
        sender_id="planner-agent",
    )

    assert response["message_type"] == "ERROR"
    assert response["payload"]["error_type"] == "ValueError"
    assert "Unknown intent" in response["payload"]["error"]


def test_intent_router_rejects_inactive_target_agent():
    bus = AgentBus()

    planner = PlannerAgent()
    application = ApplicationAgent()

    planner.start()

    bus.register_agent(planner)
    bus.register_agent(application)

    router = IntentRouter(bus)

    message = {
        "message_id": "msg-inactive-agent",
        "request_id": "req-inactive-agent",
        "message_type": "REQUEST",
        "timestamp": "2026-10-03T00:00:00+00:00",
        "payload": {
            "intent": "open_browser",
        },
    }

    response = router.route(
        message=message,
        sender_id="planner-agent",
    )

    assert response["message_type"] == "ERROR"
    assert response["payload"]["error_type"] == "RuntimeError"
    assert "not active" in response["payload"]["error"]