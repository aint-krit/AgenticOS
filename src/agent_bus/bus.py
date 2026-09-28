from typing import Any

from src.agent_runtime.agent import Agent


class AgentBus:
    REQUIRED_MESSAGE_FIELDS = {
        "message_id",
        "request_id",
        "message_type",
        "timestamp",
        "payload",
    }

    VALID_MESSAGE_TYPES = {
        "REGISTER",
        "UNREGISTER",
        "HEARTBEAT",
        "REQUEST",
        "RESPONSE",
        "EVENT",
        "ERROR",
    }

    def __init__(self):
        self.agents: dict[str, Agent] = {}

    def register_agent(self, agent: Agent) -> dict[str, Any]:
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
        return [
            agent.get_registration()
            for agent in self.agents.values()
        ]

    def validate_message(self, message: dict[str, Any]) -> None:
        if not isinstance(message, dict):
            raise ValueError("Message must be a dictionary.")

        missing_fields = self.REQUIRED_MESSAGE_FIELDS - message.keys()

        if missing_fields:
            raise ValueError(
                f"Message is missing required fields: "
                f"{sorted(missing_fields)}"
            )

        if message["message_type"] not in self.VALID_MESSAGE_TYPES:
            raise ValueError(
                f"Invalid message type: {message['message_type']}"
            )

        if not isinstance(message["payload"], dict):
            raise ValueError(
                "Message payload must be a dictionary."
            )

    def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        message: dict[str, Any],
    ) -> dict[str, Any]:

        self.validate_message(message)

        if sender_id not in self.agents:
            raise ValueError(
                f"Sender '{sender_id}' is not registered."
            )

        if receiver_id not in self.agents:
            raise ValueError(
                f"Receiver '{receiver_id}' is not registered."
            )

        sender = self.agents[sender_id]
        receiver = self.agents[receiver_id]

        if sender.status != "active":
            raise RuntimeError(
                f"Sender '{sender_id}' is not active."
            )

        if receiver.status != "active":
            raise RuntimeError(
                f"Receiver '{receiver_id}' is not active."
            )

        message["sender"] = sender_id
        message["receiver"] = receiver_id

        return receiver.receive_message(message)