from src.agent_bus.bus import AgentBus
from src.agent_runtime.agent import Agent
from src.intent.router import IntentRouter


def main():
    bus = AgentBus()

    planner = Agent(
        agent_id="planner-agent",
        name="Planner Agent",
    )

    application = Agent(
        agent_id="application-agent",
        name="Application Agent",
    )

    planner.start()
    application.start()

    bus.register_agent(planner)
    bus.register_agent(application)

    router = IntentRouter(bus)

    message = {
        "message_id": "msg-intent-demo-001",
        "request_id": "req-intent-demo-001",
        "message_type": "REQUEST",
        "timestamp": "2026-09-29T10:00:00Z",
        "payload": {
            "intent": "open_browser",
        },
    }

    print("=== AgenticOS Intent Routing Demo ===")
    print()
    print("Incoming intent:")
    print("  open_browser")
    print()
    print("Resolved target:")
    print(f"  {router.resolve('open_browser')}")
    print()
    print("Routing through Agent Bus...")

    response = router.route(
        message,
        sender_id="planner-agent",
    )

    print("Intent delivered.")
    print(f"  Sender: {response['sender']}")
    print(f"  Request ID: {response['request_id']}")
    print(f"  Status: {response['payload']['status']}")
    print()
    print("=== Intent routing successful ===")


if __name__ == "__main__":
    main()