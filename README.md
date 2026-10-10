# AgenticOS v0.1 Alpha

AgenticOS is an autonomous agent operating system architecture designed to translate human natural language into structured goals, multi-agent workflows, and authorized operating system actions.

---

## Architecture Overview

AgenticOS operates across a 10-layer vertical pipeline:

```text
USER (Human Interface: Chat / Voice / GUI / CLI)
  │
  ▼
Intent Intelligence (NLP / Intent Parser / Safety Guard)
  │
  ▼
Goal Runtime (Goal Manager / Lifecycle / Constraints)
  │
  ▼
Workflow Runtime (Task Graph / Dependency DAG / Retries)
  │
  ▼
Global Agent Manager (Discovery / Capability Matching / Health)
  │
  ▼
Agent Runtime (Planner, Executor, File, App, Memory, Monitor, Security, Web, Kernel)
  │
  ▼
Knowledge & Capability Layer (Tool Registry / Skill Library / Permission Gates)
  │
  ▼
Applications & System Services (Filesystem, Browser, Telemetry, OS Adapters)
  │
  ▼
Kernel Intelligence (Workload Prediction, Adaptive Policy, Resource Monitoring)
  │
  ▼
OS Foundation (Host OS / Linux / System Services)
```

Security, governance, observability, and failure recovery apply across all layers.

---

## Features

- **Prompt Intelligence & Safety**: Natural language understanding converting prompts into structured intents (`create_file`, `open_browser`, `system_info`, `remember`, etc.) with prompt-injection defense and ambiguity resolution.
- **Dynamic Task Graphs**: Automatic workflow decomposition with dependency execution and failure recovery.
- **Capability Authorization Gate**: All agent actions are strictly mediated by the `CapabilityRegistry` and `PermissionManager`.
- **Confined Workspace**: Filesystem modifications are isolated to the relative `workspace/` boundary, blocking path traversal and unauthorized absolute paths.
- **System Telemetry & Monitoring**: Live CPU and RAM collection backed by `psutil` and Kernel Intelligence.
- **Dual Human Interface**:
  - Interactive ASCII prompt shell (`python -m src.ui.cli`)
  - Web dashboard (`http://127.0.0.1:8001/`)

---

## Installation & Setup

### Prerequisites
- Python 3.12+
- Windows or Linux

### Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## Running AgenticOS

### 1. Interactive Terminal Shell
Launch the interactive prompt shell:
```powershell
python -m src.ui.cli
```

Or execute a single prompt directly:
```powershell
python -m src.ui.cli "Open Chrome and create file notes.txt with content Hello World"
```

### 2. Web UI & REST API Server
Start the Uvicorn server:
```powershell
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8001 --reload
```

- **Interactive Web Dashboard**: `http://127.0.0.1:8001/` or `http://127.0.0.1:8001/ui`
- **Swagger / OpenAPI Documentation**: `http://127.0.0.1:8001/docs`

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web UI Dashboard |
| `GET` | `/api/health` | Health check (`status`, `service`, `version`) |
| `GET` | `/api/system` | Live telemetry snapshot (CPU %, RAM MB, platform) |
| `GET` | `/api/agents` | Discover all active registered agents |
| `GET` | `/api/agents/{agent_id}` | Detailed status of a specific agent |
| `GET` | `/api/capabilities` | List registered capabilities and tools |
| `POST` | `/api/prompt` | Execute end-to-end prompt through vertical stack |
| `POST` | `/api/files` | Create a file inside workspace |
| `GET` | `/api/files?path=...` | Read a file inside workspace |
| `PUT` | `/api/files` | Update/overwrite a file inside workspace |
| `DELETE` | `/api/files?path=...` | Delete a file inside workspace |

---

## Demos

Run the vertical integration and user journey demonstrations:
```powershell
# Complete user journey & multimodal prompt shell demo
python demos/demo_user_journey_ui.py

# End-to-end platform orchestration demo
python demos/demo_agent_platform_integration.py

# Applications & system services demo
python demos/demo_applications_system.py
```

---

## Testing

Run the full automated test suite:
```powershell
python -m pytest -q
```
All 200+ unit and integration tests verify agent communication, capability gates, workspace isolation, prompt parsing, and end-to-end workflows.
