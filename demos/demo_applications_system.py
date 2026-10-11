import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.ecosystem import create_core_agents
from src.agent_bus.bus import AgentBus
from src.capability.registry import CapabilityRegistry
from src.capability.service import CapabilityService
from src.capability.tool import Tool
from src.global_agent_manager.manager import GlobalAgentManager
from src.system_services.capabilities import (
    create_agenticos_directory,
    get_system_snapshot,
)


def main() -> None:
    print("=" * 70)
    print("AgenticOS Applications + System Services Demo")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Agent ecosystem
    # ---------------------------------------------------------

    bus = AgentBus()
    manager = GlobalAgentManager(bus)

    agents = create_core_agents()

    for agent in agents:
        manager.register_agent(agent)
        agent.start()

    print("\n[1] Agent ecosystem")
    print(
        "Registered agents:",
        len(manager.discover_agents()),
    )

    # ---------------------------------------------------------
    # 2. Capability Registry
    # ---------------------------------------------------------

    registry = CapabilityRegistry()

    create_directory_tool = Tool(
        tool_id="directory-create-tool",
        name="Directory Creation Tool",
        description="Creates the AgenticOS project directory.",
        handler=create_agenticos_directory,
        capabilities=["create_agenticos_directory"],
    )

    system_snapshot_tool = Tool(
        tool_id="system-info-tool",
        name="System Information Tool",
        description="Returns CPU and memory information.",
        handler=get_system_snapshot,
        capabilities=["system_information"],
    )

    registry.register_tool(
        create_directory_tool
    )

    registry.register_tool(
        system_snapshot_tool
    )

    # ---------------------------------------------------------
    # 3. Permission setup
    # ---------------------------------------------------------

    registry.grant_permission(
        "file-agent",
        "create_agenticos_directory",
    )

    registry.grant_permission(
        "monitor-agent",
        "system_information",
    )

    service = CapabilityService(
        registry=registry
    )

    print("\n[2] Capability layer")
    print(
        "Capabilities:",
        registry.discover_capabilities(),
    )

    # ---------------------------------------------------------
    # 4. Create Documents/AgenticOS
    #
    # Use a temporary Documents directory for the demo so
    # the demonstration does not modify the user's real
    # Documents folder.
    # ---------------------------------------------------------

    with TemporaryDirectory(
        prefix="agenticos-documents-"
    ) as temp_documents:

        directory_result = service.execute_capability(
            agent_id="file-agent",
            capability="create_agenticos_directory",
            base_directory=temp_documents,
        )

        created_path = Path(
            directory_result["result"]["path"]
        )

        print("\n[3] File/Application integration")
        print(
            "AgenticOS directory:",
            created_path,
        )

        assert created_path.exists()
        assert created_path.is_dir()
        assert directory_result["verified"] is True

    # ---------------------------------------------------------
    # 5. System information
    # ---------------------------------------------------------

    system_result = service.execute_capability(
        agent_id="monitor-agent",
        capability="system_information",
    )

    snapshot = system_result["result"]

    print("\n[4] System information")

    print(
        "Platform:",
        snapshot["platform"],
    )

    print(
        "CPU:",
        snapshot["cpu"],
    )

    print(
        "Memory:",
        snapshot["memory"],
    )

    assert system_result["verified"] is True

    # ---------------------------------------------------------
    # 6. Final verification
    # ---------------------------------------------------------

    assert len(manager.discover_agents()) == 9

    print("\n" + "=" * 70)
    print(
        "Applications + System Services workflow "
        "completed successfully."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()