from typing import Any

from src.agent_runtime.agent import Agent


class AgentBus:
    """
    Agent Bus for registering agents and routing messages.
    """

    def __init__(self):
        self.agents: dict[str, Agent] = {}

    def register_agent(self, agent: Agent) -> dict[str, Any]:
        """Register an agent with the bus."""

        if agent.agent_id in self.agents:
            raise ValueError(
                f"Agent '{agent.agent_id}' is already registered."
            )

        self.agents[agent.agent_id] = agent

        return {
            "status": "registered",
            "agent": agent.get_registration(),
        }

    def unregister_agent(self, agent_id: str) -> dict[str, Any]:
        """Remove an agent from the bus."""

        if agent_id not in self.agents:
            raise ValueError(
                f"Agent '{agent_id}' is not registered."
            )

        del self.agents[agent_id]

        return {
            "status": "unregistered",
            "agent_id": agent_id,
        }

    def discover_agents(self) -> list[dict[str, Any]]:
        """Return registration information for all registered agents."""

        return [
            agent.get_registration()
            for agent in self.agents.values()
        ]

    def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        """Send a message from one registered agent to another."""

        if sender_id not in self.agents:
            raise ValueError(
                f"Sender '{sender_id}' is not registered."
            )

        if receiver_id not in self.agents:
            raise ValueError(
                f"Receiver '{receiver_id}' is not registered."
            )

        message["sender"] = sender_id
        message["receiver"] = receiver_id

        receiver = self.agents[receiver_id]

        return receiver.receive_message(message)