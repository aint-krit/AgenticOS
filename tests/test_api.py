from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from src.agent_bus.bus import AgentBus
from src.agent_platform.orchestrator import AgentPlatform
from src.agent_runtime.agent import Agent
from src.agents.ecosystem import create_core_agents
from src.agents.file_agent import FileAgent
from src.api.app import app
from src.api.dependencies import get_runtime
from src.api.runtime import AgenticOSRuntime
from src.capability.registry import CapabilityRegistry
from src.global_agent_manager.manager import GlobalAgentManager
from src.goal_runtime.manager import GoalManager
from src.workflow_runtime.manager import WorkflowManager


def create_test_runtime(workspace_root: Path) -> AgenticOSRuntime:
    workspace_root.mkdir(parents=True, exist_ok=True)
    bus = AgentBus()
    agent_manager = GlobalAgentManager(bus)
    goal_manager = GoalManager(bus)
    workflow_manager = WorkflowManager(bus)
    capability_registry = CapabilityRegistry()

    coordinator = Agent(
        "agent-platform",
        "Agent Platform",
        agent_type="core",
    )
    agents = [coordinator, *create_core_agents()]
    agents = [
        FileAgent(workspace_root=workspace_root)
        if agent.agent_id == "file-agent"
        else agent
        for agent in agents
    ]

    for agent in agents:
        agent.start()
        agent_manager.register_agent(agent)

    platform = AgentPlatform(
        bus=bus,
        agent_manager=agent_manager,
        goal_manager=goal_manager,
        workflow_manager=workflow_manager,
        capability_registry=capability_registry,
    )

    for capability, operation in (
        ("create_file", "CREATE_FILE"),
        ("read_file", "READ_FILE"),
        ("write_file", "WRITE_FILE"),
        ("delete_file", "DELETE_FILE"),
    ):
        platform.register_capability_route(
            "file-agent",
            capability,
            operation,
        )
        platform.grant_capability("file-agent", capability)

    return AgenticOSRuntime(
        bus=bus,
        agent_manager=agent_manager,
        goal_manager=goal_manager,
        workflow_manager=workflow_manager,
        capability_registry=capability_registry,
        platform=platform,
        workspace=workspace_root,
    )


@pytest.fixture
def client(tmp_path):
    test_runtime = create_test_runtime(tmp_path / "workspace")
    app.dependency_overrides[get_runtime] = lambda: test_runtime
    with TestClient(app) as test_client:
        yield test_client, test_runtime
    app.dependency_overrides.clear()


def test_api_health():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "AgenticOS"
    assert data["version"] == "0.1.0"


def test_api_system():
    client = TestClient(app)
    response = client.get("/api/system")
    assert response.status_code == 200
    data = response.json()
    assert "platform" in data
    assert "cpu" in data
    assert "memory" in data


def test_api_agents_discovery(client):
    c, _ = client
    response = c.get("/api/agents")
    assert response.status_code == 200
    agents = response.json()
    assert isinstance(agents, list)
    agent_ids = {a["agent_id"] for a in agents}
    assert "file-agent" in agent_ids
    assert "agent-platform" in agent_ids


def test_api_get_agent_and_not_found(client):
    c, _ = client
    response = c.get("/api/agents/file-agent")
    assert response.status_code == 200
    assert response.json()["agent_id"] == "file-agent"

    response = c.get("/api/agents/non-existent-agent")
    assert response.status_code == 404


def test_api_capabilities(client):
    c, _ = client
    response = c.get("/api/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert "create_file" in data["capabilities"]
    assert "read_file" in data["capabilities"]
    assert "write_file" in data["capabilities"]
    assert "delete_file" in data["capabilities"]


def test_file_crud_lifecycle(client):
    c, runtime = client

    # 1. CREATE FILE
    create_res = c.post(
        "/api/files",
        json={"path": "hello.txt", "content": "Hello AgenticOS!"},
    )
    assert create_res.status_code == 200
    create_data = create_res.json()
    assert create_data["status"] == "created"
    assert "hello.txt" in create_data["path"]

    # Verify file exists on disk inside workspace
    expected_file = runtime.workspace / "hello.txt"
    assert expected_file.exists()
    assert expected_file.read_text(encoding="utf-8") == "Hello AgenticOS!"

    # 2. READ FILE (via query param)
    read_res = c.get("/api/files", params={"path": "hello.txt"})
    assert read_res.status_code == 200
    read_data = read_res.json()
    assert read_data["status"] == "read"
    assert read_data["content"] == "Hello AgenticOS!"

    # READ FILE (via path param)
    read_path_res = c.get("/api/files/hello.txt")
    assert read_path_res.status_code == 200
    assert read_path_res.json()["content"] == "Hello AgenticOS!"

    # 3. WRITE FILE (overwrite)
    write_res = c.put(
        "/api/files",
        json={"path": "hello.txt", "content": "Updated content v2"},
    )
    assert write_res.status_code == 200
    write_data = write_res.json()
    assert write_data["status"] == "written"

    # READ AGAIN to verify update
    read_res2 = c.get("/api/files", params={"path": "hello.txt"})
    assert read_res2.status_code == 200
    assert read_res2.json()["content"] == "Updated content v2"

    # 4. DELETE FILE (via query param)
    del_res = c.delete("/api/files", params={"path": "hello.txt"})
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # Verify deleted on disk
    assert not expected_file.exists()

    # 5. READ AFTER DELETE -> 404
    read_after_del = c.get("/api/files", params={"path": "hello.txt"})
    assert read_after_del.status_code == 404


def test_file_nested_directory(client):
    c, runtime = client
    nested_path = "nested/deep/folder/note.md"

    # Create nested
    create_res = c.post(
        "/api/files",
        json={"path": nested_path, "content": "Deep content"},
    )
    assert create_res.status_code == 200
    assert (runtime.workspace / "nested" / "deep" / "folder" / "note.md").exists()

    # Read nested
    read_res = c.get("/api/files", params={"path": nested_path})
    assert read_res.status_code == 200
    assert read_res.json()["content"] == "Deep content"

    # Delete nested with JSON body
    del_res = c.request("DELETE", "/api/files", json={"path": nested_path})
    assert del_res.status_code == 200
    assert not (runtime.workspace / "nested" / "deep" / "folder" / "note.md").exists()


def test_file_conflict_when_already_exists(client):
    c, _ = client
    create1 = c.post("/api/files", json={"path": "dup.txt", "content": "first"})
    assert create1.status_code == 200

    create2 = c.post("/api/files", json={"path": "dup.txt", "content": "second"})
    assert create2.status_code == 409
    assert "already exists" in create2.json()["detail"].lower()


def test_file_not_found(client):
    c, _ = client
    read_res = c.get("/api/files", params={"path": "missing.txt"})
    assert read_res.status_code == 404

    del_res = c.delete("/api/files", params={"path": "missing.txt"})
    assert del_res.status_code == 404


def test_file_path_traversal_rejection(client):
    c, runtime = client

    # Relative traversal attempting escape
    res_create = c.post(
        "/api/files",
        json={"path": "../escape.txt", "content": "bad"},
    )
    assert res_create.status_code == 400
    assert "workspace" in res_create.json()["detail"].lower()

    res_read = c.get("/api/files", params={"path": "../escape.txt"})
    assert res_read.status_code == 400
    assert "workspace" in res_read.json()["detail"].lower()

    res_write = c.put(
        "/api/files",
        json={"path": "sub/../../escape.txt", "content": "bad"},
    )
    assert res_write.status_code == 400
    assert "workspace" in res_write.json()["detail"].lower()

    res_del = c.delete("/api/files", params={"path": "../escape.txt"})
    assert res_del.status_code == 400
    assert "workspace" in res_del.json()["detail"].lower()

    # Ensure nothing was created outside workspace
    outside_file = runtime.workspace.parent / "escape.txt"
    assert not outside_file.exists()


def test_file_absolute_path_rejection(client):
    c, _ = client

    res = c.post(
        "/api/files",
        json={"path": "C:\\escape.txt", "content": "bad"},
    )
    assert res.status_code == 400
    assert "absolute" in res.json()["detail"].lower()


def test_file_empty_path_rejection(client):
    c, _ = client

    res = c.post("/api/files", json={"path": "   ", "content": "bad"})
    assert res.status_code == 400
    assert "non-empty" in res.json()["detail"].lower()


def test_file_operations_route_through_platform_orchestration(client):
    c, runtime = client
    # Perform a create operation
    res = c.post(
        "/api/files",
        json={"path": "traced.txt", "content": "traced content"},
    )
    assert res.status_code == 200

    # Verify that traces were recorded in the platform orchestrator
    assert len(runtime.platform.trace) > 0
    traces = [
        event
        for event_list in runtime.platform.trace.values()
        for event in event_list
    ]
    # Check that agent_bus.dispatch and workflow stages were executed
    stages = {event["stage"] for event in traces}
    assert "agent_bus.dispatch" in stages
    assert "workflow" in stages
    assert "intent" in stages
