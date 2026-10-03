from datetime import datetime, timezone

from src.agent_bus.bus import AgentBus
from src.agents.ecosystem import create_core_agents
from src.global_agent_manager.manager import GlobalAgentManager
from src.intent.router import IntentRouter


def main() -> None:
    print("=" * 60)
    print("AgenticOS v0.1 - Open Browser Demo")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Create Agent Bus and Global Agent Manager
    # ---------------------------------------------------------

    bus = AgentBus()
    manager = GlobalAgentManager(bus)

    # ---------------------------------------------------------
    # 2. Create and register the complete agent ecosystem
    # ---------------------------------------------------------

    print("\n[1] Registering agents...")

    agents = create_core_agents()

    for agent in agents:
        manager.register_agent(agent)
        agent.start()

        print(
            f"    ✓ {agent.name} "
            f"({agent.agent_id})"
        )

    # ---------------------------------------------------------
    # 3. Create the Intent Router
    # ---------------------------------------------------------

    router = IntentRouter(bus)

    # ---------------------------------------------------------
    # 4. Create an intent message
    # ---------------------------------------------------------

    intent_message = {
        "message_id": "msg-open-browser-demo",
        "request_id": "req-open-browser-demo",
        "message_type": "REQUEST",
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "payload": {
            "intent": "open_browser",
            "operation": "OPEN_BROWSER",
            "url": "https://www.google.com",
        },
    }

    print("\n[2] User intent:")
    print("    Open browser")

    # ---------------------------------------------------------
    # 5. Resolve the intent
    # ---------------------------------------------------------

    target_agent = router.resolve(
        intent_message["payload"]["intent"]
    )

    print("\n[3] Intent Router:")
    print(
        f"    Target agent: {target_agent}"
    )

    # ---------------------------------------------------------
    # 6. Route through Agent Bus
    # ---------------------------------------------------------

    print("\n[4] Routing through Agent Bus...")

    response = router.route(
        message=intent_message,
        sender_id="planner-agent",
    )

    # ---------------------------------------------------------
    # 7. Display result
    # ---------------------------------------------------------

    print("\n[5] Agent response:")

    print(
        f"    Message type: "
        f"{response['message_type']}"
    )

    print(
        f"    Sender: "
        f"{response['sender']}"
    )

    print(
        f"    Receiver: "
        f"{response['receiver']}"
    )

    print(
        f"    Status: "
        f"{response['payload'].get('status')}"
    )

    if response["message_type"] == "RESPONSE":
        print(
            f"    Action: "
            f"{response['payload'].get('action')}"
        )

        print(
            f"    URL: "
            f"{response['payload'].get('url')}"
        )

    print("\n" + "=" * 60)
    print("Open Browser workflow completed.")
    print("=" * 60)


if __name__ == "__main__":
    main()