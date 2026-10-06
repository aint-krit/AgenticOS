from typing import Any

from src.capability.permissions import PermissionManager
from src.capability.tool import Tool


class CapabilityRegistry:
    """
    Central registry for AgenticOS tools and capabilities.

    Execution flow:

        Agent
          ↓
        Capability Registry
          ↓
        Permission Check
          ↓
        Tool
          ↓
        Execute
          ↓
        Verify
    """

    def __init__(
        self,
        permission_manager: PermissionManager | None = None,
    ):
        self.tools: dict[str, Tool] = {}
        self.capabilities: dict[str, str] = {}

        self.permission_manager = (
            permission_manager
            or PermissionManager()
        )

    def register_tool(
        self,
        tool: Tool,
    ) -> dict[str, Any]:
        """
        Register a tool and its capabilities.
        """

        if tool.tool_id in self.tools:
            raise ValueError(
                f"Tool '{tool.tool_id}' is already registered."
            )

        self.tools[tool.tool_id] = tool

        for capability in tool.capabilities:
            if capability in self.capabilities:
                raise ValueError(
                    f"Capability '{capability}' is already "
                    f"registered."
                )

            self.capabilities[capability] = tool.tool_id

        return {
            "status": "registered",
            "tool": tool.get_registration(),
        }

    def unregister_tool(
        self,
        tool_id: str,
    ) -> dict[str, Any]:
        """
        Remove a tool and its capability mappings.
        """

        if tool_id not in self.tools:
            raise ValueError(
                f"Tool '{tool_id}' is not registered."
            )

        tool = self.tools.pop(tool_id)

        for capability in tool.capabilities:
            self.capabilities.pop(
                capability,
                None,
            )

        return {
            "status": "unregistered",
            "tool_id": tool_id,
        }

    def discover_tools(self) -> list[dict[str, Any]]:
        """
        Return all registered tools.
        """

        return [
            tool.get_registration()
            for tool in self.tools.values()
        ]

    def discover_capabilities(self) -> list[str]:
        """
        Return all registered capabilities.
        """

        return sorted(
            self.capabilities.keys()
        )

    def get_tool_for_capability(
        self,
        capability: str,
    ) -> Tool:
        """
        Resolve a capability to its registered tool.
        """

        if capability not in self.capabilities:
            raise ValueError(
                f"Capability '{capability}' is not registered."
            )

        tool_id = self.capabilities[capability]

        return self.tools[tool_id]

    def grant_permission(
        self,
        agent_id: str,
        capability: str,
    ) -> None:
        """
        Grant an agent access to a capability.
        """

        if capability not in self.capabilities:
            raise ValueError(
                f"Capability '{capability}' is not registered."
            )

        self.permission_manager.grant(
            agent_id,
            capability,
        )

    def revoke_permission(
        self,
        agent_id: str,
        capability: str,
    ) -> None:
        """
        Revoke an agent's capability permission.
        """

        self.permission_manager.revoke(
            agent_id,
            capability,
        )

    def execute(
        self,
        agent_id: str,
        capability: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a capability through the complete
        authorization and tool execution pipeline.
        """

        # 1. Resolve capability.
        tool = self.get_tool_for_capability(
            capability
        )

        # 2. Check permission.
        self.permission_manager.require_permission(
            agent_id,
            capability,
        )

        # 3. Execute tool.
        result = tool.execute(
            **kwargs
        )

        # 4. Verify execution result.
        verified = result is not None

        return {
            "status": "completed",
            "agent_id": agent_id,
            "capability": capability,
            "tool_id": tool.tool_id,
            "result": result,
            "verified": verified,
        }