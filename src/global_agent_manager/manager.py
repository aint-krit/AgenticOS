from datetime import datetime, timezone
from typing import Any

from src.agent_bus.bus import AgentBus
from src.agent_runtime.agent import Agent


class GlobalAgentManager:
    """
    Maintains the live registry of agents and provides
    discovery, registration, health, and communication
    management across the AgenticOS agent ecosystem.
    """

    def __init__(
        self,
        bus: AgentBus,
        manager_agent_id: str = "global-agent-manager",
    ):
        self.bus = bus
        self.manager_agent_id = manager_agent_id
        self.registry: dict[str, dict[str, Any]] = {}

    def register_agent(
        self,
        agent: Agent,
    ) -> dict[str, Any]:
        """
        Register an agent with both the Agent Bus and
        the Global Agent Manager registry.
        """

        if agent.agent_id in self.registry:
            raise ValueError(
                f"Agent '{agent.agent_id}' is already registered."
            )

        self.bus.register_agent(agent)

        registration = agent.get_registration()

        self.registry[agent.agent_id] = {
            **registration,
            "registered_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "last_heartbeat": None,
        }

        return self.registry[agent.agent_id].copy()

    def unregister_agent(
        self,
        agent_id: str,
    ) -> dict[str, Any]:
        """
        Remove an agent from the live registry and
        Agent Bus.
        """

        if agent_id not in self.registry:
            raise ValueError(
                f"Agent '{agent_id}' is not registered."
            )

        self.bus.unregister_agent(agent_id)

        registration = self.registry.pop(agent_id)

        return {
            "status": "unregistered",
            "agent_id": agent_id,
            "agent": registration,
        }

    def discover_agents(
        self,
    ) -> list[dict[str, Any]]:
        """
        Return the current live agent registry.
        """

        return [
            registration.copy()
            for registration in self.registry.values()
        ]

    def get_agent(
        self,
        agent_id: str,
    ) -> dict[str, Any]:
        """
        Return information about a registered agent.
        """

        if agent_id not in self.registry:
            raise ValueError(
                f"Agent '{agent_id}' is not registered."
            )

        return self.registry[agent_id].copy()

    def discover_by_capability(
        self,
        capability: str,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        """Return registered agents that advertise a capability."""
        if not isinstance(capability, str) or not capability.strip():
            raise ValueError("capability must be a non-empty string.")

        matches = []
        for registration in self.registry.values():
            if capability not in registration.get("capabilities", []):
                continue
            if active_only and registration.get("status") != "active":
                continue
            matches.append(registration.copy())
        return matches

    def select_agent(
        self,
        capability: str,
    ) -> dict[str, Any]:
        """Select an active registered agent that provides a capability."""
        matches = self.discover_by_capability(capability)
        if not matches:
            raise ValueError(
                f"No active agent provides capability '{capability}'."
            )
        return matches[0].copy()

    def get_agent_status(
        self,
        agent_id: str,
    ) -> str:
        """
        Return the current status of an agent.
        """

        agent = self._get_bus_agent(agent_id)

        return agent.status

    def update_agent_status(
        self,
        agent_id: str,
        status: str,
    ) -> dict[str, Any]:
        """
        Update an agent's lifecycle status.
        """

        if agent_id not in self.registry:
            raise ValueError(
                f"Agent '{agent_id}' is not registered."
            )

        if status not in Agent.VALID_STATUSES:
            raise ValueError(
                f"Invalid agent status: {status}"
            )

        agent = self._get_bus_agent(agent_id)

        if status == "active":
            agent.start()

        elif status == "paused":
            agent.pause()

        elif status == "stopped":
            agent.stop()

        elif status == "starting":
            agent.status = "starting"

        elif status == "busy":
            agent.status = "busy"

        elif status == "unhealthy":
            agent.status = "unhealthy"

        self.registry[agent_id]["status"] = agent.status

        return self.registry[agent_id].copy()

    def heartbeat(
        self,
        agent_id: str,
    ) -> dict[str, Any]:
        """
        Record a heartbeat from an agent.
        """

        if agent_id not in self.registry:
            raise ValueError(
                f"Agent '{agent_id}' is not registered."
            )

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        agent = self._get_bus_agent(agent_id)

        self.registry[agent_id]["status"] = agent.status
        self.registry[agent_id]["last_heartbeat"] = timestamp

        return {
            "status": "healthy",
            "agent_id": agent_id,
            "agent_status": agent.status,
            "timestamp": timestamp,
        }

    def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Route communication between registered agents
        through the Agent Bus.
        """

        self._require_registered(sender_id)
        self._require_registered(receiver_id)

        return self.bus.send_message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message=message,
        )

    def _get_bus_agent(
        self,
        agent_id: str,
    ) -> Agent:
        if agent_id not in self.bus.agents:
            raise ValueError(
                f"Agent '{agent_id}' is not registered with the Agent Bus."
            )

        return self.bus.agents[agent_id]

    def _require_registered(
        self,
        agent_id: str,
    ) -> None:
        if agent_id not in self.registry:
            raise ValueError(
                f"Agent '{agent_id}' is not registered."
            )