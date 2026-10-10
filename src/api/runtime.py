
from dataclasses import dataclass
from pathlib import Path

from src.agent_bus.bus import AgentBus
from src.agent_platform.orchestrator import AgentPlatform
from src.agents.ecosystem import create_core_agents
from src.agents.file_agent import FileAgent
from src.agent_runtime.agent import Agent
from src.capability.registry import CapabilityRegistry
from src.global_agent_manager.manager import GlobalAgentManager
from src.goal_runtime.manager import GoalManager
from src.workflow_runtime.manager import WorkflowManager


@dataclass
class AgenticOSRuntime:
    bus: AgentBus
    agent_manager: GlobalAgentManager
    goal_manager: GoalManager
    workflow_manager: WorkflowManager
    capability_registry: CapabilityRegistry
    platform: AgentPlatform
    workspace: Path | None = None


def create_runtime() -> AgenticOSRuntime:
    bus = AgentBus()
    agent_manager = GlobalAgentManager(bus)
    goal_manager = GoalManager(bus)
    workflow_manager = WorkflowManager(bus)
    capability_registry = CapabilityRegistry()

    # Restrict API-created file operations to the project workspace.
    workspace = (Path.cwd() / "workspace").resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    coordinator = Agent(
        "agent-platform",
        "Agent Platform",
        agent_type="core",
    )

    agents = [coordinator, *create_core_agents()]

    # Replace the default FileAgent with a workspace-restricted instance.
    agents = [
        FileAgent(workspace_root=workspace)
        if agent.agent_id == "file-agent"
        else agent
        for agent in agents
    ]

    for agent in agents:
        agent.start()
        agent_manager.register_agent(agent)

    platform = AgentPlatform(
        bus=bus,
        agent_manager=agent_manager,
        goal_manager=goal_manager,
        workflow_manager=workflow_manager,
        capability_registry=capability_registry,
    )

    # Register the supported file capabilities once.
    

    # Register the supported file capabilities once.
    for capability, operation in (
        ("create_file", "CREATE_FILE"),
        ("read_file", "READ_FILE"),
        ("write_file", "WRITE_FILE"),
        ("delete_file", "DELETE_FILE"),
    ):
        platform.register_capability_route(
            "file-agent",
            capability,
            operation,
        )
        platform.grant_capability("file-agent", capability)

    return AgenticOSRuntime(
        bus=bus,
        agent_manager=agent_manager,
        goal_manager=goal_manager,
        workflow_manager=workflow_manager,
        capability_registry=capability_registry,
        platform=platform,
        workspace=workspace,
    )