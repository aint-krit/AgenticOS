from src.agent_bus.bus import AgentBus
from src.agent_runtime.agent import Agent
from src.goal_runtime.manager import GoalManager


def main():
    print("=== AgenticOS Goal Runtime Demo ===")

    # ---------------------------------------------------------
    # 1. Create Agent Bus
    # ---------------------------------------------------------

    bus = AgentBus()

    planner = Agent(
        agent_id="planner-agent",
        name="Planner Agent",
        agent_type="core",
        capabilities=["plan_goal"],
    )

    goal_manager_agent = Agent(
        agent_id="goal-manager-agent",
        name="Goal Manager Agent",
        agent_type="core",
        capabilities=[
            "create_goal",
            "update_goal",
            "pause_goal",
            "cancel_goal",
            "complete_goal",
            "fail_goal",
            "replan_goal",
        ],
    )

    planner.start()
    goal_manager_agent.start()

    bus.register_agent(planner)
    bus.register_agent(goal_manager_agent)

    manager = GoalManager(
        bus=bus,
        manager_agent_id="goal-manager-agent",
    )

    # ---------------------------------------------------------
    # 2. Create Goal
    # ---------------------------------------------------------

    print("\n[1] Creating goal...")

    goal = manager.create_goal(
        goal_id="goal-demo-001",
        description="Build AgenticOS Agent Runtime",
        priority="high",
    )

    print(f"  Goal ID: {goal.goal_id}")
    print(f"  Description: {goal.description}")
    print(f"  Priority: {goal.priority}")
    print(f"  Status: {goal.status}")

    # ---------------------------------------------------------
    # 3. Activate Goal through Agent Bus
    # ---------------------------------------------------------

    print("\n[2] Activating goal through Agent Bus...")

    response = manager.send_goal_message(
        sender_id="planner-agent",
        receiver_id="goal-manager-agent",
        operation="ACTIVATE",
        goal_id="goal-demo-001",
        request_id="req-goal-demo-001",
        message_id="msg-goal-demo-001",
    )

    print(f"  Message status: {response['payload']['status']}")

    received_message = (
        bus.agents["goal-manager-agent"]
        .received_messages[-1]
    )

    print(
        f"  Request ID: "
        f"{received_message['request_id']}"
    )

    # ---------------------------------------------------------
    # 4. Process the received goal message
    # ---------------------------------------------------------

    print("\n[3] Processing goal message...")

    processed_response = manager.handle_goal_message(
        received_message
    )

    print(
        f"  Response type: "
        f"{processed_response['message_type']}"
    )

    print(
        f"  Operation: "
        f"{processed_response['payload']['operation']}"
    )

    print(
        f"  Goal status: "
        f"{processed_response['payload']['goal']['status']}"
    )

    # ---------------------------------------------------------
    # 5. Update Goal
    # ---------------------------------------------------------

    print("\n[4] Updating goal...")

    update_message = {
        "message_id": "msg-goal-demo-002",
        "request_id": "req-goal-demo-002",
        "message_type": "REQUEST",
        "timestamp": "2026-09-30T10:00:00Z",
        "sender": "planner-agent",
        "payload": {
            "operation": "UPDATE",
            "goal_id": "goal-demo-001",
            "description": "Build AgenticOS Agent Bus and Runtime",
            "priority": "critical",
        },
    }

    update_response = manager.handle_goal_message(
        update_message
    )

    print(
        f"  Status: "
        f"{update_response['payload']['status']}"
    )

    print(
        f"  New description: "
        f"{update_response['payload']['goal']['description']}"
    )

    print(
        f"  New priority: "
        f"{update_response['payload']['goal']['priority']}"
    )

    # ---------------------------------------------------------
    # 6. Pause Goal
    # ---------------------------------------------------------

    print("\n[5] Pausing goal...")

    pause_message = {
        "message_id": "msg-goal-demo-003",
        "request_id": "req-goal-demo-003",
        "message_type": "REQUEST",
        "timestamp": "2026-09-30T10:00:00Z",
        "sender": "planner-agent",
        "payload": {
            "operation": "PAUSE",
            "goal_id": "goal-demo-001",
        },
    }

    pause_response = manager.handle_goal_message(
        pause_message
    )

    print(
        f"  Goal status: "
        f"{pause_response['payload']['goal']['status']}"
    )

    # ---------------------------------------------------------
    # 7. Replan Goal
    # ---------------------------------------------------------

    print("\n[6] Replanning goal...")

    replan_message = {
        "message_id": "msg-goal-demo-004",
        "request_id": "req-goal-demo-004",
        "message_type": "REQUEST",
        "timestamp": "2026-09-30T10:00:00Z",
        "sender": "planner-agent",
        "payload": {
            "operation": "REPLAN",
            "goal_id": "goal-demo-001",
        },
    }

    replan_response = manager.handle_goal_message(
        replan_message
    )

    print(
        f"  Goal status: "
        f"{replan_response['payload']['goal']['status']}"
    )

    # ---------------------------------------------------------
    # 8. Activate Again
    # ---------------------------------------------------------

    print("\n[7] Reactivating goal...")

    activate_message = {
        "message_id": "msg-goal-demo-005",
        "request_id": "req-goal-demo-005",
        "message_type": "REQUEST",
        "timestamp": "2026-09-30T10:00:00Z",
        "sender": "planner-agent",
        "payload": {
            "operation": "ACTIVATE",
            "goal_id": "goal-demo-001",
        },
    }

    activate_response = manager.handle_goal_message(
        activate_message
    )

    print(
        f"  Goal status: "
        f"{activate_response['payload']['goal']['status']}"
    )

    # ---------------------------------------------------------
    # 9. Complete Goal
    # ---------------------------------------------------------

    print("\n[8] Completing goal...")

    complete_message = {
        "message_id": "msg-goal-demo-006",
        "request_id": "req-goal-demo-006",
        "message_type": "REQUEST",
        "timestamp": "2026-09-30T10:00:00Z",
        "sender": "planner-agent",
        "payload": {
            "operation": "COMPLETE",
            "goal_id": "goal-demo-001",
        },
    }

    complete_response = manager.handle_goal_message(
        complete_message
    )

    final_goal = complete_response["payload"]["goal"]

    print(
        f"  Final status: "
        f"{final_goal['status']}"
    )

    # ---------------------------------------------------------
    # 10. Show Lifecycle History
    # ---------------------------------------------------------

    print("\n[9] Goal lifecycle history:")

    for transition in final_goal["history"]:
        print(
            f"  {transition['from']}"
            f" -> "
            f"{transition['to']}"
        )

    print("\n=== Goal Runtime Demo Complete ===")


if __name__ == "__main__":
    main()