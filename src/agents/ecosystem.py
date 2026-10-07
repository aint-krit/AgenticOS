from src.agents.application_agent import ApplicationAgent
from src.agents.executor_agent import ExecutorAgent
from src.agents.file_agent import FileAgent
from src.agents.memory_agent import MemoryAgent
from src.agents.monitor_agent import MonitorAgent
from src.agents.planner_agent import PlannerAgent
from src.agents.security_agent import SecurityAgent
from src.agents.web_agent import WebAgent
from src.agent_runtime.agent import Agent
from src.kernel_intelligence.agent import KernelIntelligenceAgent


def create_core_agents() -> list[Agent]:
    return [
        PlannerAgent(),
        ExecutorAgent(),
        MonitorAgent(),
        MemoryAgent(),
        SecurityAgent(),
        ApplicationAgent(),
        FileAgent(),
        WebAgent(),
        KernelIntelligenceAgent(),
    ]
