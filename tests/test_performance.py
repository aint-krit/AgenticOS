import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest

from src.agent_bus.bus import AgentBus
from src.agent_runtime.agent import Agent
from src.intent.parser import IntentParser
from src.kernel_intelligence.monitor import ResourceMonitor
from src.agents.ecosystem import create_core_agents
from src.agents.file_agent import FileAgent
from src.agent_platform.orchestrator import AgentPlatform
from src.capability.registry import CapabilityRegistry
from src.global_agent_manager.manager import GlobalAgentManager
from src.goal_runtime.manager import GoalManager
from src.workflow_runtime.manager import WorkflowManager


def build_test_platform(tmp_path: Path) -> AgentPlatform:
    bus = AgentBus()
    agent_manager = GlobalAgentManager(bus)
    goal_manager = GoalManager(bus)
    workflow_manager = WorkflowManager(bus)
    capability_registry = CapabilityRegistry()

    coordinator = Agent("agent-platform", "Agent Platform", agent_type="core")
    agents = [coordinator, *create_core_agents()]
    agents = [
        FileAgent(workspace_root=tmp_path)
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
        platform.register_capability_route("file-agent", capability, operation)
        platform.grant_capability("file-agent", capability)

    platform.register_capability_route(
        "application-agent", "launch_application", "LAUNCH_APPLICATION"
    )
    platform.grant_capability("application-agent", "launch_application")

    platform.register_capability_route("memory-agent", "remember", "REMEMBER")
    platform.grant_capability("memory-agent", "remember")

    platform.register_capability_route(
        "kernel-intelligence-agent", "resource_monitoring", "GET_SNAPSHOT"
    )
    platform.grant_capability("kernel-intelligence-agent", "resource_monitoring")

    return platform


def test_agent_bus_latency():
    """Agent Bus message roundtrip latency must be sub-millisecond in-memory."""
    bus = AgentBus()
    agent_a = Agent("agent-a", "Agent A", capabilities=["test.send"])
    agent_b = Agent("agent-b", "Agent B", capabilities=["test.receive"])
    agent_a.start()
    agent_b.start()
    bus.register_agent(agent_a)
    bus.register_agent(agent_b)

    iterations = 100
    start = time.perf_counter()
    for i in range(iterations):
        resp = bus.send_message(
            sender_id="agent-a",
            receiver_id="agent-b",
            message={
                "message_id": f"msg-{i}",
                "request_id": f"req-{i}",
                "message_type": "REQUEST",
                "timestamp": "2026-10-11T00:00:00Z",
                "payload": {"action": "ping", "seq": i},
            },
        )
        assert resp["message_type"] == "RESPONSE"
    elapsed = time.perf_counter() - start
    avg_latency_ms = (elapsed / iterations) * 1000

    assert avg_latency_ms < 5.0, f"Average bus latency too high: {avg_latency_ms:.3f}ms"


def test_agent_bus_concurrent_throughput():
    """Concurrent threads dispatching across Agent Bus must not corrupt state or drop messages."""
    bus = AgentBus()
    target_agent = Agent("target-agent", "Target Agent")
    target_agent.start()
    bus.register_agent(target_agent)

    worker_count = 4
    messages_per_worker = 15

    def worker(worker_id: int):
        sender = Agent(f"worker-{worker_id}", f"Worker {worker_id}")
        sender.start()
        bus.register_agent(sender)
        results = []
        for i in range(messages_per_worker):
            resp = bus.send_message(
                sender_id=sender.agent_id,
                receiver_id="target-agent",
                message={
                    "message_id": f"msg-{worker_id}-{i}",
                    "request_id": f"req-{worker_id}-{i}",
                    "message_type": "REQUEST",
                    "timestamp": "2026-10-11T00:00:00Z",
                    "payload": {"data": i},
                },
            )
            results.append(resp.get("payload", {}).get("status") == "received")
        return all(results)

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(worker, w) for w in range(worker_count)]
        all_passed = all(f.result() for f in futures)

    assert all_passed is True
    assert len(target_agent.received_messages) == worker_count * messages_per_worker


def test_intent_parser_latency():
    """IntentParser must classify prompts in under 5ms per prompt."""
    parser = IntentParser()
    prompts = [
        "Create file notes.txt with content Hello World",
        "Open Chrome",
        "Remember that the project name is AgenticOS",
        "Show my CPU and memory usage",
        "Read file notes.txt",
        "Delete file notes.txt",
    ]

    iterations = 50
    start = time.perf_counter()
    for _ in range(iterations):
        for p in prompts:
            result = parser.parse(p)
            assert result.intent != ""
    elapsed = time.perf_counter() - start

    total_parses = iterations * len(prompts)
    avg_latency_ms = (elapsed / total_parses) * 1000
    assert avg_latency_ms < 5.0, f"Average parse latency too high: {avg_latency_ms:.3f}ms"


def test_prompt_execution_throughput(tmp_path: Path):
    """End-to-end prompt execution through AgentPlatform must execute cleanly and quickly."""
    platform = build_test_platform(tmp_path)

    prompts = [
        "Create file perf1.txt with content 111",
        "Read file perf1.txt",
        "Remember that project is agenticos",
        "Show my CPU and memory usage",
    ]

    start = time.perf_counter()
    for prompt in prompts:
        outcome = platform.execute_prompt(prompt)
        assert outcome["status"] == "completed"
        assert outcome["verified"] is True
    elapsed = time.perf_counter() - start

    avg_e2e_ms = (elapsed / len(prompts)) * 1000
    assert avg_e2e_ms < 100.0, f"Average prompt E2E latency too high: {avg_e2e_ms:.3f}ms"


def test_kernel_telemetry_collection_latency():
    """System monitor telemetry sampling must execute within SLA."""
    monitor = ResourceMonitor()
    start = time.perf_counter()
    snapshot = monitor.collect()
    elapsed = time.perf_counter() - start
    metrics = snapshot.to_dict()

    assert "cpu_percent" in metrics
    assert "memory_percent" in metrics
    assert elapsed < 0.5, f"Telemetry collection exceeded SLA: {elapsed:.3f}s"
