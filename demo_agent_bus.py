from src.agent_bus.bus import AgentBus
from src.agent_runtime.agent import Agent


def main():
    bus = AgentBus()

    planner = Agent(
        agent_id="planner-agent",
        name="Planner Agent",
        agent_type="core",
        capabilities=["planning"],
    )

    executor = Agent(
        agent_id="executor-agent",
        name="Executor Agent",
        agent_type="core",
        capabilities=["execution"],
    )

    planner.start()
    executor.start()

    print("=== AgenticOS Agent Bus Demo ===")
    print()

    # Register agents
    bus.register_agent(planner)
    bus.register_agent(executor)

    print("Registered agents:")
    for agent in bus.discover_agents():
        print(f"  - {agent['agent_id']} [{agent['status']}]")

    print()
    print("Sending message...")
    
    response = bus.send_message(
        sender_id="planner-agent",
        receiver_id="executor-agent",
        message={
            "message_id": "msg-demo-001",
            "request_id": "req-demo-001",
            "message_type": "REQUEST",
            "timestamp": "2026-09-28T00:00:00Z",
            "payload": {
                "action": "execute_task",
                "task": "Create AgenticOS project folder",
            },
        },
    )

    print("Message delivered.")
    print(f"  Sender: {response['receiver']}")
    print(f"  Receiver: {response['sender']}")
    print(f"  Request ID: {response['request_id']}")
    print(f"  Status: {response['payload']['status']}")

    print()
    print("=== Communication successful ===")


if __name__ == "__main__":
    main()