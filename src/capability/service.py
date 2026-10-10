
from typing import Any

from src.capability.connector import Connector
from src.capability.registry import CapabilityRegistry
from src.capability.skill import SkillLibrary


class CapabilityService:
    """Orchestrate capabilities, skills, and connectors with auditing."""

    def __init__(
        self,
        registry: CapabilityRegistry,
        skill_library: SkillLibrary | None = None,
    ):
        self.registry = registry
        self.skill_library = (
            skill_library if skill_library is not None else SkillLibrary()
        )
        self.connectors: dict[str, Connector] = {}

    def _audit_failure(
        self,
        *,
        request_id: str | None,
        agent_id: str,
        capability: str,
        error: Exception,
        tool_id: str | None = None,
    ) -> None:
        """Record a service-level failure without masking the original error."""
        outcome = (
            "denied"
            if isinstance(error, PermissionError)
            else "rejected"
            if isinstance(error, (ValueError, KeyError))
            else "failed"
        )

        self.registry.record_audit(
            request_id=request_id,
            agent_id=agent_id,
            capability=capability,
            tool_id=tool_id,
            outcome=outcome,
            error_type=type(error).__name__,
            error=str(error),
        )

    def register_connector(
        self,
        connector: Connector,
    ) -> dict[str, Any]:
        if connector.connector_id in self.connectors:
            raise ValueError(
                f"Connector '{connector.connector_id}' is already registered."
            )

        self.connectors[connector.connector_id] = connector
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

    def discover_connectors(self) -> list[dict[str, Any]]:
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
        # The registry owns capability execution and its audit records.
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
        """Preflight every capability before performing skill side effects."""
        request_id = kwargs.get("request_id")

        try:
            capabilities = self.skill_library.resolve_capabilities(skill_id)
        except Exception as error:
            self._audit_failure(
                request_id=request_id,
                agent_id=agent_id,
                capability=f"skill:{skill_id}",
                error=error,
            )
            raise

        # Phase 1: validate the complete skill before any operation executes.
        for capability in capabilities:
            tool_id = None
            try:
                tool = self.registry.get_tool_for_capability(capability)
                tool_id = getattr(tool, "tool_id", None)
                self.registry.permission_manager.require_permission(
                    agent_id,
                    capability,
                )
            except Exception as error:
                self._audit_failure(
                    request_id=request_id,
                    agent_id=agent_id,
                    capability=capability,
                    tool_id=tool_id,
                    error=error,
                )
                raise

        # Phase 2: execute only after the complete preflight succeeds.
        results = []
        for capability in capabilities:
            results.append(
                self.execute_capability(
                    agent_id=agent_id,
                    capability=capability,
                    **kwargs,
                )
            )

        return {
            "status": "completed",
            "agent_id": agent_id,
            "skill_id": skill_id,
            "results": results,
            "verified": all(
                result["verified"] for result in results
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
        """Authorize and audit connector execution."""
        request_id = kwargs.pop("request_id", None)
        tool_id = None
        try:
            tool = self.registry.get_tool_for_capability(capability)
            tool_id = getattr(tool, "tool_id", None)

            self.registry.permission_manager.require_permission(
                agent_id,
                capability,
            )

            if connector_id not in self.connectors:
                raise ValueError(
                    f"Connector '{connector_id}' is not registered."
                )

        except Exception as error:
            self._audit_failure(
                request_id=request_id,
                agent_id=agent_id,
                capability=capability,
                tool_id=tool_id,
                error=error,
            )
            raise

        connector = self.connectors[connector_id]
 
       
        try:
            result = connector.execute(operation=operation, **kwargs)
        except Exception as error:
            self._audit_failure(
                request_id=request_id,
                agent_id=agent_id,
                capability=capability,
                tool_id=tool_id,
                error=error,
            )
            raise
       

        self.registry.record_audit(
            request_id=request_id,
            agent_id=agent_id,
            capability=capability,
            tool_id=tool_id,
            outcome="success" if result is not None else "unverified",
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