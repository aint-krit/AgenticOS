import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agent_bus.bus import AgentBus
from src.agent_runtime.agent import Agent
from src.agents.file_agent import FileAgent
from src.capability.registry import CapabilityRegistry
from src.global_agent_manager.manager import GlobalAgentManager
from src.goal_runtime.manager import GoalManager
from src.agent_platform.orchestrator import AgentPlatform
from src.workflow_runtime.manager import WorkflowManager


def main() -> None:
    with TemporaryDirectory(prefix="agenticos-integration-") as temp_dir:
        bus = AgentBus()
        global_manager = GlobalAgentManager(bus)
        goal_manager = GoalManager(bus)
        workflow_manager = WorkflowManager(bus)
        capability_registry = CapabilityRegistry()

        coordinator = Agent("agent-platform", "Agent Platform", agent_type="core")
        file_agent = FileAgent()
        coordinator.start()
        file_agent.start()

        global_manager.register_agent(coordinator)
        global_manager.register_agent(file_agent)

        platform = AgentPlatform(
            bus=bus,
            agent_manager=global_manager,
            goal_manager=goal_manager,
            workflow_manager=workflow_manager,
            capability_registry=capability_registry,
        )

        for capability, operation in {
            "create_file": "CREATE_FILE",
            "read_file": "READ_FILE",
            "write_file": "WRITE_FILE",
            "delete_file": "DELETE_FILE",
        }.items():
            platform.register_capability_route(
                "file-agent",
                capability,
                operation,
            )
            platform.grant_capability(
                "file-agent",
                capability,
            )

        target = Path(temp_dir) / "AgenticOS" / "integration.txt"

        result = platform.execute_intent(
            intent="create_file",
            description="Create an AgenticOS integration verification file.",
            payload={
                "path": str(target),
                "content": "AgenticOS integration PASS",
            },
            request_id="demo-integration-001",
        )

        assert result["verified"] is True
        assert target.read_text(encoding="utf-8") == "AgenticOS integration PASS"

        print("AgenticOS vertical integration: PASS")
        print(f"Request ID: {result['request_id']}")
        print(f"Goal: {result['goal']['status']}")
        print(f"Workflow: {result['workflow']['status']}")
        print(f"Verified: {result['verified']}")
        print("Trace:")
        for item in result["trace"]:
            print(f"  {item['stage']}: {item['status']}")


if __name__ == "__main__":
    main()
