# AgenticOS v0.1 Alpha — Architecture Audit

## Purpose and Scope

This document maps the ten proposed AgenticOS architecture layers to their source components and associated test suites. It summarizes the available automated test and benchmark results.

A source-to-test mapping does not establish complete implementation, production readiness, or formal verification. Linux deployment configuration has been reviewed, but deployment on a supported Linux distribution has not yet been demonstrated by the evidence recorded here.

## Architecture Layer Mapping

| Layer | Architecture Layer       | Source Components                                                                  | Related Tests / Evidence                                                                                        |
| ----- | ------------------------ | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| 1     | Human Interface          | `src/ui/cli.py`, `src/ui/prompt_shell.py`, `src/ui/dashboard.py`                   | `tests/test_api.py`; coverage should be confirmed against the individual interfaces                             |
| 2     | Intent Intelligence      | `src/intent/parser.py`                                                             | `tests/test_intent_parser.py`, `tests/test_prompt_workflow.py`                                                  |
| 3     | Goal Runtime             | `src/goal_runtime/`                                                                | `tests/test_goal_runtime.py`                                                                                    |
| 4     | Workflow Runtime         | `src/workflow_runtime/`                                                            | `tests/test_workflow_runtime.py`                                                                                |
| 5     | Global Agent Manager     | `src/global_agent_manager/`                                                        | `tests/test_global_agent_manager.py`                                                                            |
| 6     | Agent Runtime and Bus    | `src/agent_runtime/`, `src/agent_bus/`                                             | `tests/test_agent_bus.py`, `tests/test_agents.py`                                                               |
| 7     | Knowledge and Capability | `src/capability/`, `src/memory_knowledge/`                                         | `tests/test_capability_layer.py`, `tests/test_memory_knowledge.py`                                              |
| 8     | System Services          | `src/system_services/`                                                             | `tests/test_system_services.py`                                                                                 |
| 9     | Kernel Intelligence      | `src/kernel_intelligence/`                                                         | `tests/test_kernel_intelligence.py`                                                                             |
| 10    | Linux and Deployment     | `packaging/install.sh`, `packaging/agenticos.service`, `packaging/README_LINUX.md` | Configuration review only; Linux installation and runtime behavior require validation on a supported Linux host |

## Latest Recorded Test Results

The most recent recorded full test run completed with **215 passed and 1 warning**. Rerun the suite before treating this result as the final result for a commit.

The warning concerned Starlette's `TestClient` integration with `httpx`. It did not cause the recorded tests to fail.

## Performance Benchmark Results

The latest recorded benchmark run reported:

| Measurement                |           Recorded Result |         Defined Benchmark Limit |
| -------------------------- | ------------------------: | ------------------------------: |
| Agent Bus latency          | 5.08 microseconds/message |              1,000 microseconds |
| Intent Parser latency      | 17.11 microseconds/prompt |              5,000 microseconds |
| End-to-end prompt workflow |         3.10 milliseconds |                 50 milliseconds |
| Kernel telemetry sampling  |   203 milliseconds/sample | No benchmark-script SLA defined |

The first three measurements passed their benchmark-script limits in that run. These are observed measurements, not guarantees of performance on other machines or under different loads. Kernel telemetry is informational in the benchmark script; the performance test suite separately checks that an individual telemetry collection completes in under 0.5 seconds.

## Reliability Test Scope

The reliability tests include checks for:

* Requests to stopped or unregistered agents.
* Revoked capabilities.
* Selected path-traversal and malicious-prompt cases.
* Unrecognized prompts and missing files.

These tests cover selected failure cases. They do not establish comprehensive security, eliminate all prompt-injection risks, or prove that every unauthorized operation is blocked.

## Linux Deployment Review

The installer and systemd service have been reviewed as configuration files. The installer includes dependency installation, service-account creation, file deployment, virtual-environment setup, and systemd service configuration.

The installer has been updated to validate project files, copy selected project components, check systemd service startup, and make the CLI launcher fail explicitly when its installed Python environment is missing.

These changes have not yet been validated through an actual Linux installation. The service is configured for loopback access on `127.0.0.1:8001`; this is consistent with a local-only deployment, but it does not itself provide application authentication or prove API health.

## Verification Status

* **Automated tests:** 215 passed in the last recorded run; rerun before committing.
* **Performance benchmarks:** Three defined limits passed in the last recorded run.
* **Reliability:** Selected failure cases are covered by automated tests.
* **Linux deployment:** Configuration reviewed; real installation and runtime validation remain outstanding.

This audit is a summary of recorded evidence, not a claim of formal verification or complete production readiness.
