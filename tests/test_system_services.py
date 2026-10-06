from pathlib import Path

from src.agents.web_agent import WebAgent
from src.system_services.capabilities import (
    create_agenticos_directory,
    get_cpu_information,
    get_memory_information,
    get_system_snapshot,
)
from src.system_services.system_info import SystemInfoService


def test_web_agent_initialization():
    agent = WebAgent()

    assert agent.agent_id == "web-agent"
    assert agent.name == "Web Agent"
    assert agent.status == "starting"

    assert "open_url" in agent.capabilities
    assert "open_browser" in agent.capabilities


def test_web_agent_start():
    agent = WebAgent()

    agent.start()

    assert agent.status == "active"


def test_web_agent_open_url(monkeypatch):
    agent = WebAgent()

    opened_urls = []

    def fake_open(url):
        opened_urls.append(url)
        return True

    monkeypatch.setattr(
        "src.agents.web_agent.webbrowser.open",
        fake_open,
    )

    result = agent.open_url(
        "https://example.com"
    )

    assert result["status"] == "opened"
    assert result["url"] == "https://example.com"
    assert result["browser_opened"] is True
    assert opened_urls == ["https://example.com"]


def test_web_agent_rejects_empty_url():
    agent = WebAgent()

    try:
        agent.open_url("")
        assert False, "Expected empty URL to fail."
    except ValueError as error:
        assert "non-empty" in str(error)


def test_web_agent_message_execution(monkeypatch):
    agent = WebAgent()
    agent.start()

    opened_urls = []

    def fake_open(url):
        opened_urls.append(url)
        return True

    monkeypatch.setattr(
        "src.agents.web_agent.webbrowser.open",
        fake_open,
    )

    message = {
        "message_id": "msg-web-001",
        "request_id": "req-web-001",
        "sender": "executor-agent",
        "receiver": "web-agent",
        "message_type": "REQUEST",
        "timestamp": "2026-10-06T00:00:00+00:00",
        "payload": {
            "operation": "OPEN_URL",
            "url": "https://example.com",
        },
    }

    response = agent.receive_message(message)

    assert response["message_type"] == "RESPONSE"
    assert response["request_id"] == "req-web-001"
    assert response["payload"]["status"] == "opened"
    assert opened_urls == ["https://example.com"]


def test_cpu_information():
    result = SystemInfoService.cpu_info()

    assert "logical_cpus" in result
    assert "architecture" in result
    assert "processor" in result

    assert result["logical_cpus"] is None or (
        isinstance(result["logical_cpus"], int)
        and result["logical_cpus"] > 0
    )


def test_memory_information():
    result = SystemInfoService.memory_info()

    assert "available" in result

    if result["available"]:
        assert "total_gb" in result
        assert "available_gb" in result
        assert "used_gb" in result

        assert result["total_gb"] > 0
        assert result["available_gb"] >= 0
        assert result["used_gb"] >= 0


def test_system_snapshot():
    result = SystemInfoService.snapshot()

    assert "platform" in result
    assert "platform_version" in result
    assert "cpu" in result
    assert "memory" in result

    assert "logical_cpus" in result["cpu"]
    assert "available" in result["memory"]


def test_create_agenticos_directory(tmp_path):
    result = create_agenticos_directory(
        base_directory=str(tmp_path)
    )

    expected_path = (
        Path(tmp_path) / "AgenticOS"
    )

    assert result["created"] is True
    assert result["exists"] is True
    assert Path(result["path"]) == expected_path
    assert expected_path.is_dir()


def test_create_agenticos_directory_is_idempotent(tmp_path):
    first = create_agenticos_directory(
        base_directory=str(tmp_path)
    )

    second = create_agenticos_directory(
        base_directory=str(tmp_path)
    )

    assert first["exists"] is True
    assert second["exists"] is True
    assert first["path"] == second["path"]


def test_system_capability_functions():
    cpu = get_cpu_information()
    memory = get_memory_information()
    snapshot = get_system_snapshot()

    assert "logical_cpus" in cpu
    assert "available" in memory
    assert "cpu" in snapshot
    assert "memory" in snapshot