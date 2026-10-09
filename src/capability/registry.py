
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.capability.permissions import PermissionManager
from src.capability.tool import Tool


class CapabilityRegistry:
    """Central registry, authorization gate, and execution audit log."""

    def __init__(
        self,
        permission_manager: PermissionManager | None = None,
    ):
        self.tools: dict[str, Tool] = {}
        self.capabilities: dict[str, str] = {}
        self.permission_manager = (
            permission_manager
            if permission_manager is not None
            else PermissionManager()
        )
        self.audit_log: list[dict[str, Any]] = []

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def record_audit(
        self,
        *,
        request_id: str | None,
        agent_id: str,
        capability: str,
        outcome: str,
        tool_id: str | None = None,
        error_type: str | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Record a capability execution or authorization outcome."""
        event = {
            "timestamp": self._timestamp(),
            "request_id": (
                request_id
                if isinstance(request_id, str) and request_id.strip()
                else f"audit-{uuid4().hex}"
            ),
            "agent_id": agent_id,
            "capability": capability,
            "tool_id": tool_id,
            "outcome": outcome,
            "error_type": error_type,
            "error": error,
        }
        self.audit_log.append(event)
        return dict(event)

    def get_audit_log(
        self,
        request_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return copies of audit events, optionally filtered by request."""
        events = self.audit_log
        if request_id is not None:
            events = [
                event for event in events
                if event["request_id"] == request_id
            ]
        return [dict(event) for event in events]

    def register_tool(self, tool: Tool) -> dict[str, Any]:
        if tool.tool_id in self.tools:
            raise ValueError(
                f"Tool '{tool.tool_id}' is already registered."
            )

        # Validate everything before mutating either registry.
        for capability in tool.capabilities:
            if capability in self.capabilities:
                raise ValueError(
                    f"Capability '{capability}' is already registered."
                )

        self.tools[tool.tool_id] = tool
        for capability in tool.capabilities:
            self.capabilities[capability] = tool.tool_id

        return {
            "status": "registered",
            "tool": tool.get_registration(),
        }

    def unregister_tool(self, tool_id: str) -> dict[str, Any]:
        if tool_id not in self.tools:
            raise ValueError(
                f"Tool '{tool_id}' is not registered."
            )

        tool = self.tools.pop(tool_id)
        for capability in tool.capabilities:
            if self.capabilities.get(capability) == tool_id:
                del self.capabilities[capability]

        return {"status": "unregistered", "tool_id": tool_id}

    def discover_tools(self) -> list[dict[str, Any]]:
        return [
            tool.get_registration()
            for tool in self.tools.values()
        ]

    def discover_capabilities(self) -> list[str]:
        return sorted(self.capabilities)

    def get_tool_for_capability(self, capability: str) -> Tool:
        if capability not in self.capabilities:
            raise ValueError(
                f"Capability '{capability}' is not registered."
            )
        return self.tools[self.capabilities[capability]]

    def grant_permission(
        self,
        agent_id: str,
        capability: str,
    ) -> None:
        self.get_tool_for_capability(capability)
        self.permission_manager.grant(agent_id, capability)

    def revoke_permission(
        self,
        agent_id: str,
        capability: str,
    ) -> None:
        self.permission_manager.revoke(agent_id, capability)

    def execute(
        self,
        agent_id: str,
        capability: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Authorize, execute, and audit a capability invocation."""
        request_id = kwargs.get("request_id")
        tool_id: str | None = None

        try:
            tool = self.get_tool_for_capability(capability)
            tool_id = tool.tool_id

            self.permission_manager.require_permission(
                agent_id,
                capability,
            )

            result = tool.execute(**kwargs)

            verified = result is not None
            self.record_audit(
                request_id=request_id,
                agent_id=agent_id,
                capability=capability,
                tool_id=tool_id,
                outcome="success" if verified else "unverified",
            )

            return {
                "status": "completed",
                "agent_id": agent_id,
                "capability": capability,
                "tool_id": tool_id,
                "result": result,
                "verified": verified,
            }

        except Exception as error:
            if isinstance(error, PermissionError):
                outcome = "denied"
            elif isinstance(error, ValueError) and tool_id is None:
                outcome = "rejected"
            else:
                outcome = "failed"

            self.record_audit(
                request_id=request_id,
                agent_id=agent_id,
                capability=capability,
                tool_id=tool_id,
                outcome=outcome,
                error_type=type(error).__name__,
                error=str(error),
            )
            raise