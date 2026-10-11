import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agent_runtime.agent import Agent
from src.agent_bus.bus import AgentBus
from src.global_agent_manager.manager import GlobalAgentManager


def create_agent(
    agent_id: str,
    name: str,
    agent_type: str,
    capabilities: list[str],
) -> Agent:
    agent = Agent(
        agent_id=agent_id,
        name=name,
        agent_type=agent_type,
        capabilities=capabilities,
    )

    agent.start()

    return agent


def main():
    print("=== Global Agent Manager Demo ===")
    print()

    # ---------------------------------------------------------
    # 1. Create Agent Bus and Global Agent Manager
    # ---------------------------------------------------------

    bus = AgentBus()

    global_manager = GlobalAgentManager(
        bus=bus,
        manager_agent_id="global-agent-manager",
    )

    print("Global Agent Manager initialized.")
    print()

    # ---------------------------------------------------------
    # 2. Create system agents
    # ---------------------------------------------------------

    planner = create_agent(
        "planner-agent",
        "Planner Agent",
        "core",
        ["planning", "task_decomposition"],
    )

    executor = create_agent(
        "executor-agent",
        "Executor Agent",
        "specialized",
        ["task_execution"],
    )

    memory = create_agent(
        "memory-agent",
        "Memory Agent",
        "specialized",
        ["memory_read", "memory_write"],
    )

    # ---------------------------------------------------------
    # 3. Register agents
    # ---------------------------------------------------------

    global_manager.register_agent(planner)
    global_manager.register_agent(executor)
    global_manager.register_agent(memory)

    print("Registered agents:")

    for agent in global_manager.discover_agents():
        print(
            f"  - {agent['agent_id']} "
            f"| {agent['name']} "
            f"| status={agent['status']} "
            f"| capabilities={agent['capabilities']}"
        )

    print()

    # ---------------------------------------------------------
    # 4. Agent discovery
    # ---------------------------------------------------------

    discovered = global_manager.discover_agents()

    print(
        f"Agent discovery found {len(discovered)} agents."
    )
    print()

    # ---------------------------------------------------------
    # 5. Health / heartbeat
    # ---------------------------------------------------------

    print("Sending heartbeats:")

    for agent_id in [
        "planner-agent",
        "executor-agent",
        "memory-agent",
    ]:
        heartbeat = global_manager.heartbeat(
            agent_id
        )

        print(
            f"  {heartbeat['agent_id']}: "
            f"{heartbeat['status']} "
            f"({heartbeat['agent_status']})"
        )

    print()

    # ---------------------------------------------------------
    # 6. Status management
    # ---------------------------------------------------------

    print("Pausing Executor Agent...")

    global_manager.update_agent_status(
        "executor-agent",
        "paused",
    )

    print(
        "  Executor status:",
        global_manager.get_agent_status(
            "executor-agent"
        ),
    )

    print("Resuming Executor Agent...")

    global_manager.update_agent_status(
        "executor-agent",
        "active",
    )

    print(
        "  Executor status:",
        global_manager.get_agent_status(
            "executor-agent"
        ),
    )

    print()

    # ---------------------------------------------------------
    # 7. Agent-to-agent communication
    # ---------------------------------------------------------

    message = {
        "message_id": "msg-global-demo-001",
        "request_id": "req-global-demo-001",
        "message_type": "REQUEST",
        "timestamp": "2026-10-02T10:00:00Z",
        "payload": {
            "operation": "EXECUTE_TASK",
            "task_id": "task-demo-001",
            "description": "Execute demo task",
        },
    }

    response = global_manager.send_message(
        sender_id="planner-agent",
        receiver_id="executor-agent",
        message=message,
    )

    print("Agent communication:")
    print(
        f"  {response['sender']} responded to "
        f"request {response['request_id']}"
    )

    print()

    # ---------------------------------------------------------
    # 8. Final live registry
    # ---------------------------------------------------------

    print("Final live agent registry:")

    for agent in global_manager.discover_agents():
        print(
            f"  - {agent['agent_id']}: "
            f"{agent['status']} "
            f"| last_heartbeat="
            f"{agent['last_heartbeat']}"
        )

    print()
    print("=== Global Agent Manager Demo Complete ===")


if __name__ == "__main__":
    main()