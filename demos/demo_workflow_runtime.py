from src.agent_bus.bus import AgentBus
from src.agent_runtime.agent import Agent
from src.workflow_runtime.manager import WorkflowManager
from src.workflow_runtime.task import Task


def main():
    print("=== Workflow Runtime Demo ===")

    # ---------------------------------------------------------
    # 1. Create Agent Bus and participating agents
    # ---------------------------------------------------------

    bus = AgentBus()

    workflow_agent = Agent(
        agent_id="workflow-manager-agent",
        name="Workflow Manager",
        agent_type="core",
        capabilities=[
            "workflow_execution",
            "task_dispatch",
        ],
    )

    executor_agent = Agent(
        agent_id="executor-agent",
        name="Executor Agent",
        agent_type="specialized",
        capabilities=[
            "task_execution",
        ],
    )

    workflow_agent.start()
    executor_agent.start()

    bus.register_agent(workflow_agent)
    bus.register_agent(executor_agent)

    print("Agents registered.")

    # ---------------------------------------------------------
    # 2. Create Workflow Manager
    # ---------------------------------------------------------

    manager = WorkflowManager(
        bus=bus,
        manager_agent_id="workflow-manager-agent",
    )

    workflow = manager.create_workflow(
        workflow_id="workflow-demo-001",
        goal_id="goal-demo-001",
        description="Open browser and process webpage",
    )

    # ---------------------------------------------------------
    # 3. Create a three-step workflow
    # ---------------------------------------------------------

    task_1 = Task(
        task_id="task-001",
        description="Open browser",
    )

    task_2 = Task(
        task_id="task-002",
        description="Navigate to website",
        dependencies=["task-001"],
    )

    task_3 = Task(
        task_id="task-003",
        description="Extract webpage information",
        dependencies=["task-002"],
    )

    manager.add_task(
        "workflow-demo-001",
        task_1,
    )

    manager.add_task(
        "workflow-demo-001",
        task_2,
    )

    manager.add_task(
        "workflow-demo-001",
        task_3,
    )

    print("Three tasks added.")

    # ---------------------------------------------------------
    # 4. Start workflow
    # ---------------------------------------------------------

    ready_tasks = manager.start_workflow(
        "workflow-demo-001"
    )

    print(
        "Initial ready tasks:",
        [task.task_id for task in ready_tasks],
    )

    # ---------------------------------------------------------
    # 5. Execute Task 1
    # ---------------------------------------------------------

    manager.dispatch_task(
        workflow_id="workflow-demo-001",
        task_id="task-001",
        sender_id="workflow-manager-agent",
        receiver_id="executor-agent",
        request_id="req-demo-001",
        message_id="msg-demo-001",
    )

    print("Task 1 dispatched.")

    ready_tasks = manager.complete_task(
        "workflow-demo-001",
        "task-001",
        result="Browser opened",
    )

    print(
        "Task 1 completed.",
        "New ready tasks:",
        [task.task_id for task in ready_tasks],
    )

    # ---------------------------------------------------------
    # 6. Execute Task 2
    # ---------------------------------------------------------

    manager.dispatch_task(
        workflow_id="workflow-demo-001",
        task_id="task-002",
        sender_id="workflow-manager-agent",
        receiver_id="executor-agent",
        request_id="req-demo-002",
        message_id="msg-demo-002",
    )

    print("Task 2 dispatched.")

    ready_tasks = manager.complete_task(
        "workflow-demo-001",
        "task-002",
        result="Website loaded",
    )

    print(
        "Task 2 completed.",
        "New ready tasks:",
        [task.task_id for task in ready_tasks],
    )

    # ---------------------------------------------------------
    # 7. Execute Task 3
    # ---------------------------------------------------------

    manager.dispatch_task(
        workflow_id="workflow-demo-001",
        task_id="task-003",
        sender_id="workflow-manager-agent",
        receiver_id="executor-agent",
        request_id="req-demo-003",
        message_id="msg-demo-003",
    )

    print("Task 3 dispatched.")

    manager.complete_task(
        "workflow-demo-001",
        "task-003",
        result="Webpage information extracted",
    )

    # ---------------------------------------------------------
    # 8. Display final workflow state
    # ---------------------------------------------------------

    workflow = manager.get_workflow(
        "workflow-demo-001"
    )

    print()
    print("Final workflow status:", workflow.status)

    for task in workflow.tasks.values():
        print(
            f"{task.task_id}: "
            f"{task.status} "
            f"-> {task.result}"
        )

    print()
    print("=== Workflow Runtime Demo Complete ===")


if __name__ == "__main__":
    main()