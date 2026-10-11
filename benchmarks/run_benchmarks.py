
#!/usr/bin/env python3
"""
AgenticOS Automated Performance & Reliability Benchmark Runner.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agent_bus.bus import AgentBus
from src.agent_runtime.agent import Agent
from src.agents.ecosystem import create_core_agents
from src.agents.file_agent import FileAgent
from src.agent_platform.orchestrator import AgentPlatform
from src.capability.registry import CapabilityRegistry
from src.global_agent_manager.manager import GlobalAgentManager
from src.goal_runtime.manager import GoalManager
from src.workflow_runtime.manager import WorkflowManager
from src.intent.parser import IntentParser
from src.kernel_intelligence.monitor import ResourceMonitor


def run_benchmarks() -> dict[str, float | bool]:
    print("=" * 60)
    print("      AgenticOS v0.1 Alpha - Performance Benchmark")
    print("=" * 60)

    # 1. Agent Bus Latency
    bus = AgentBus()
    a1 = Agent("agent-1", "Agent 1", capabilities=["test"])
    a2 = Agent("agent-2", "Agent 2", capabilities=["test"])
    a1.start()
    a2.start()
    bus.register_agent(a1)
    bus.register_agent(a2)

    bus_iterations = 500
    t0 = time.perf_counter()
    for i in range(bus_iterations):
        bus.send_message(
            "agent-1",
            "agent-2",
            {
                "message_id": f"m-{i}",
                "request_id": f"r-{i}",
                "message_type": "REQUEST",
                "timestamp": "2026-10-11T00:00:00Z",
                "payload": {"ping": i},
            },
        )
    bus_total = time.perf_counter() - t0
    bus_avg_us = (bus_total / bus_iterations) * 1_000_000
    print(f"[+] Agent Bus Latency: {bus_avg_us:.2f} microseconds / message")

    # 2. Intent Parser Latency
    parser = IntentParser()
    test_prompts = [
        "Open Chrome",
        "Create file notes.txt with content hello",
        "Show my CPU and memory usage",
        "Remember that server port is 8001",
    ]
    nlp_iterations = 250
    t0 = time.perf_counter()
    for _ in range(nlp_iterations):
        for prompt in test_prompts:
            parser.parse(prompt)
    nlp_total = time.perf_counter() - t0
    nlp_avg_us = (
        nlp_total / (nlp_iterations * len(test_prompts))
    ) * 1_000_000
    print(f"[+] Intent Parser Latency: {nlp_avg_us:.2f} microseconds / prompt")

    # 3. Kernel Telemetry Sampling Latency
    monitor = ResourceMonitor()
    telemetry_iterations = 50
    t0 = time.perf_counter()
    for _ in range(telemetry_iterations):
        monitor.collect()
    telemetry_total = time.perf_counter() - t0
    telemetry_avg_ms = (telemetry_total / telemetry_iterations) * 1000
    print(f"[+] Kernel Telemetry Sampling: {telemetry_avg_ms:.2f} ms / sample")

    # 4. End-to-End Workflow Latency
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
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
        ):
            platform.register_capability_route(
                "file-agent", capability, operation
            )
            platform.grant_capability("file-agent", capability)

        e2e_iterations = 20
        t0 = time.perf_counter()
        for i in range(e2e_iterations):
            platform.execute_prompt(
                f"Create file test_{i}.txt with content benchmark_{i}"
            )
        e2e_total = time.perf_counter() - t0
        e2e_avg_ms = (e2e_total / e2e_iterations) * 1000

    print(
        f"[+] Full E2E Pipeline (Prompt -> Goal -> Workflow -> File): "
        f"{e2e_avg_ms:.2f} ms"
    )

    # Check the explicitly defined SLAs.
    print("=" * 60)
    checks = [
        ("Agent Bus", bus_avg_us, 1000.0, "microseconds"),
        ("Intent Parser", nlp_avg_us, 5000.0, "microseconds"),
        ("End-to-End Pipeline", e2e_avg_ms, 50.0, "ms"),
    ]

    all_passed = True
    for name, actual, limit, unit in checks:
        passed = actual < limit
        print(
            f"[{'PASS' if passed else 'FAIL'}] {name}: "
            f"{actual:.2f} {unit} (limit: {limit:g} {unit})"
        )
        if not passed:
            all_passed = False

    print(
        f"[INFO] Kernel Telemetry: {telemetry_avg_ms:.2f} ms/sample "
        "(no SLA defined)"
    )
    print("=" * 60)

    return {
        "bus_latency_us": bus_avg_us,
        "intent_latency_us": nlp_avg_us,
        "telemetry_latency_ms": telemetry_avg_ms,
        "e2e_latency_ms": e2e_avg_ms,
        "all_sla_passed": all_passed,
    }


if __name__ == "__main__":
    results = run_benchmarks()
    if not results["all_sla_passed"]:
        raise SystemExit(1)
