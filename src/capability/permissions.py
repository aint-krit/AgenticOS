class PermissionManager:
    """
    Controls which agents are allowed to use which capabilities.
    """

    def __init__(self):
        self.permissions: dict[str, set[str]] = {}

    def grant(
        self,
        agent_id: str,
        capability: str,
    ) -> None:
        """
        Grant an agent permission to use a capability.
        """

        if not agent_id.strip():
            raise ValueError(
                "agent_id must be a non-empty string."
            )

        if not capability.strip():
            raise ValueError(
                "capability must be a non-empty string."
            )

        self.permissions.setdefault(
            agent_id,
            set(),
        ).add(capability)

    def revoke(
        self,
        agent_id: str,
        capability: str,
    ) -> None:
        """
        Revoke a capability from an agent.
        """

        if agent_id not in self.permissions:
            return

        self.permissions[agent_id].discard(
            capability
        )

    def is_allowed(
        self,
        agent_id: str,
        capability: str,
    ) -> bool:
        """
        Check whether an agent is authorized.
        """

        return capability in self.permissions.get(
            agent_id,
            set(),
        )

    def require_permission(
        self,
        agent_id: str,
        capability: str,
    ) -> None:
        """
        Raise PermissionError when access is denied.
        """

        if not self.is_allowed(
            agent_id,
            capability,
        ):
            raise PermissionError(
                f"Agent '{agent_id}' is not authorized "
                f"to use capability '{capability}'."
            )

    def get_permissions(
        self,
        agent_id: str,
    ) -> list[str]:
        """
        Return capabilities granted to an agent.
        """

        return sorted(
            self.permissions.get(
                agent_id,
                set(),
            )
        )
    