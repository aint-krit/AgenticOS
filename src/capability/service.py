from typing import Any

from src.capability.connector import Connector
from src.capability.registry import CapabilityRegistry
from src.capability.skill import SkillLibrary


class CapabilityService:
    """
    High-level Capability Layer orchestration.

    Execution chain:

        Agent
          ↓
        Skill / Capability
          ↓
        Capability Registry
          ↓
        Permission Check
          ↓
        Tool
          ↓
        Connector
          ↓
        Execute
          ↓
        Verify
    """

    def __init__(
        self,
        registry: CapabilityRegistry,
        skill_library: SkillLibrary | None = None,
    ):
        self.registry = registry
        self.skill_library = (
            skill_library or SkillLibrary()
        )

        self.connectors: dict[str, Connector] = {}

    def register_connector(
        self,
        connector: Connector,
    ) -> dict[str, Any]:
        if connector.connector_id in self.connectors:
            raise ValueError(
                f"Connector '{connector.connector_id}' "
                "is already registered."
            )

        self.connectors[
            connector.connector_id
        ] = connector

        return {
            "status": "registered",
            "connector": connector.health(),
        }

    def unregister_connector(
        self,
        connector_id: str,
    ) -> dict[str, Any]:
        if connector_id not in self.connectors:
            raise ValueError(
                f"Connector '{connector_id}' is not registered."
            )

        del self.connectors[connector_id]

        return {
            "status": "unregistered",
            "connector_id": connector_id,
        }

    def discover_connectors(
        self,
    ) -> list[dict[str, Any]]:
        return [
            connector.health()
            for connector in self.connectors.values()
        ]

    def execute_capability(
        self,
        agent_id: str,
        capability: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a single capability through the registry.
        """

        return self.registry.execute(
            agent_id=agent_id,
            capability=capability,
            **kwargs,
        )

    def execute_skill(
        self,
        agent_id: str,
        skill_id: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute every capability belonging to a skill.

        v0.1 executes the capabilities sequentially.
        """

        capabilities = (
            self.skill_library.resolve_capabilities(
                skill_id
            )
        )

        results = []

        for capability in capabilities:
            result = self.execute_capability(
                agent_id=agent_id,
                capability=capability,
                **kwargs,
            )

            results.append(result)

        return {
            "status": "completed",
            "agent_id": agent_id,
            "skill_id": skill_id,
            "results": results,
            "verified": all(
                result["verified"]
                for result in results
            ),
        }

    def execute_connector(
        self,
        agent_id: str,
        capability: str,
        connector_id: str,
        operation: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a connector operation after the normal
        capability permission check.
        """

        # Resolve the capability first.
        self.registry.get_tool_for_capability(
            capability
        )

        # Check permission before touching the connector.
        self.registry.permission_manager.require_permission(
            agent_id,
            capability,
        )

        if connector_id not in self.connectors:
            raise ValueError(
                f"Connector '{connector_id}' is not registered."
            )

        connector = self.connectors[connector_id]

        result = connector.execute(
            operation=operation,
            **kwargs,
        )

        return {
            "status": "completed",
            "agent_id": agent_id,
            "capability": capability,
            "connector_id": connector_id,
            "operation": operation,
            "result": result,
            "verified": result is not None,
        }