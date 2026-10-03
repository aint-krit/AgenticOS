from src.agents.application_agent import ApplicationAgent
from src.agents.executor_agent import ExecutorAgent
from src.agents.file_agent import FileAgent
from src.agents.memory_agent import MemoryAgent
from src.agents.monitor_agent import MonitorAgent
from src.agents.planner_agent import PlannerAgent
from src.agents.security_agent import SecurityAgent
from src.agent_runtime.agent import Agent


def create_core_agents() -> list[Agent]:
    """
    Create the complete v0.1 core + specialized agent set.
    """

    return [
        PlannerAgent(),
        ExecutorAgent(),
        MonitorAgent(),
        MemoryAgent(),
        SecurityAgent(),
        ApplicationAgent(),
        FileAgent(),
    ]