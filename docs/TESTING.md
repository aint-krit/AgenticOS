# AgenticOS v0.1 Alpha — Testing & Verification Guide

This document details test procedures, demo executions, performance benchmarks, and regression suites for AgenticOS v0.1 Alpha.

---

## 1. Test Environment Requirements

- **Python Version**: Python 3.12+ (tested with Python 3.12.3 on Windows 10/11 x64)
- **Dependencies**: `pip install -r requirements.txt` (FastAPI, Uvicorn, Pydantic, psutil, pytest, httpx)
- **Platform**: Cross-platform support (Windows and Linux). Sandboxed workspace file operations and in-memory bus messaging function identically on both platforms.

---

## 2. Automated Test Suite Execution

Run the complete automated test suite:
```powershell
python -m pytest -q
```

### Expected Results
- **Pass Count**: 215 passed
- **Warnings**: 1 warning (`StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated` originating from FastAPI testclient internals)
- **Duration**: ~105-120 seconds

### Subsystem Test Breakdown

| Test File | Focus Subsystem | Test Cases |
|---|---|---|
| `tests/test_agent_bus.py` | Agent Bus message routing, validation, duplicate registration, lifecycle checks | 12 |
| `tests/test_agents.py` | Core and specialized agents (File, Application, Web, Memory, Security, Monitor, Planner, Executor) | 18 |
| `tests/test_agent_platform.py` | Platform orchestration, vertical stack routing, capability dispatch | 15 |
| `tests/test_api.py` | FastAPI REST endpoints, prompt submission, file management, system telemetry, dashboard | 16 |
| `tests/test_capability_layer.py` | ToolRegistry, SkillLibrary, FunctionConnector, PermissionManager, audit logging | 19 |
| `tests/test_global_agent_manager.py` | Agent registration, discovery, health state, task capability matching | 14 |
| `tests/test_goal_runtime.py` | Goal lifecycle (create, update, pause, resume, cancel, complete, replan) | 11 |
| `tests/test_intent_parser.py` | NLP intent classification, prompt injection filters, ambiguity scoring | 10 |
| `tests/test_intent_router.py` | Routing intents to target agents via Agent Bus | 8 |
| `tests/test_kernel_intelligence.py` | Telemetry collection, bounded scheduler, workload prediction, policy rollback | 17 |
| `tests/test_memory_knowledge.py` | Episodic memory, vector embeddings, similarity search, deletion verification | 12 |
| `tests/test_performance.py` | Latency thresholds, concurrency throughput, telemetry sampling SLA | 5 |
| `tests/test_prompt_workflow.py` | Prompt to workflow execution pipeline, task graph generation | 8 |
| `tests/test_reliability.py` | Failure injection (killed agents, unauthorized calls, path traversal, malicious injection) | 7 |
| `tests/test_system_services.py` | System information adapter, directory creation, capability bindings | 6 |
| `tests/test_workflow_runtime.py` | Workflow DAG execution, dependency resolution, task retries, error recovery | 37 |

---

## 3. Performance Benchmarks

Run the automated performance benchmarks:
```powershell
python benchmarks/run_benchmarks.py
```

### Measured Performance Gates

| Benchmark Metric | Measured Value | SLA Target | Status |
|---|---|---|---|
| **Agent Bus Latency** | 4.85 μs / message | < 1,000 μs | **PASS** |
| **Intent Parser Latency** | 16.91 μs / prompt | < 5,000 μs | **PASS** |
| **End-to-End Pipeline Latency** | 3.33 ms / workflow | < 50.0 ms | **PASS** |
| **Kernel Telemetry Sampling** | 202.96 ms / sample | Informational (< 500 ms in test suite) | **PASS** |

---

## 4. Demonstrations

AgenticOS includes 13 standalone runnable demonstrations in `demos/`. All demos include direct project-root `sys.path` resolution and run with exit status 0:

### Primary Deliverable Demos

1. **Krithikesh Deliverables Verification Demo**:
   ```powershell
   python demos/demo_krithikesh_ecosystem.py
   ```
   *Exercises*: 9-agent discovery, sub-millisecond bus messaging, sandboxed File Agent operations (with blocked `../` traversal), Application Agent dispatch, Knowledge Layer (remember, retrieve, vector search, delete, verify), and Security Agent permission enforcement (denial + grant).

2. **Complete 10-Layer Architecture Demo**:
   ```powershell
   python demos/demo_full_architecture_chain.py
   ```
   *Exercises*: End-to-end prompt processing across the entire vertical stack: Human Prompt → Intent Intelligence → Goal Runtime → Workflow Runtime → Global Agent Manager → Agent Runtime → Capability Layer → System Services → Kernel Intelligence → Live Telemetry & Result Verification.

3. **User Journey & Prompt Shell Demo**:
   ```powershell
   python demos/demo_user_journey_ui.py
   ```
   *Exercises*: End-to-end user experience, interactive ASCII prompt shell rendering, multi-step progress logging.

### Component-Specific Demos

```powershell
python demos/demo_agent_bus.py                  # Agent bus registration and messaging
python demos/demo_agent_platform_integration.py # Platform orchestration
python demos/demo_applications_system.py        # Applications and OS adapters
python demos/demo_capability_layer.py           # Tool registry and skill library
python demos/demo_global_agent_manager.py       # Global agent discovery and registry
python demos/demo_goal_runtime.py               # Goal lifecycle state machine
python demos/demo_intent_routing.py             # Intent routing over bus
python demos/demo_memory_knowledge.py           # Episodic & vector memory lifecycle
python demos/demo_open_browser.py               # Browser dispatch workflow
python demos/demo_workflow_runtime.py           # Workflow DAG task execution
```

---

## 5. Security & Boundary Verification

The test suite validates the following security boundaries:

1. **Workspace Boundary**:
   - `FileAgent` restricts operations strictly to the designated `workspace_root`.
   - Absolute paths (e.g. `C:\Windows`, `/etc/passwd`) are rejected with `ValueError`.
   - Relative traversal attempts (e.g. `../../secret.txt`) are rejected with `ValueError`.
   - Tested in `tests/test_reliability.py` and `tests/test_agents.py`.

2. **Default-Deny Permission Gate**:
   - `PermissionManager` enforces default-deny: operations require explicit `grant()`.
   - Revoking a capability causes immediate `PermissionError`.
   - Tested in `tests/test_capability_layer.py` and `tests/test_reliability.py`.

3. **Prompt Injection Defense**:
   - Malicious commands (`rm -rf /`, formatting drives, "ignore previous instructions") are classified as high risk and blocked with `PermissionError`.
   - Tested in `tests/test_reliability.py` and `tests/test_intent_parser.py`.

4. **Lifecycle & State Isolation**:
   - Messages sent to stopped or unregistered agents fail safely with `RuntimeError` or `ValueError`.
   - Tested in `tests/test_agent_bus.py` and `tests/test_reliability.py`.
