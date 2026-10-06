from typing import Any, Callable


class Tool:
    """
    Represents an executable capability tool.
    """

    def __init__(
        self,
        tool_id: str,
        name: str,
        description: str,
        handler: Callable[..., Any],
        capabilities: list[str] | None = None,
    ):
        if not tool_id.strip():
            raise ValueError("tool_id must be a non-empty string.")

        if not name.strip():
            raise ValueError("name must be a non-empty string.")

        if not callable(handler):
            raise ValueError("handler must be callable.")

        self.tool_id = tool_id
        self.name = name
        self.description = description
        self.handler = handler
        self.capabilities = capabilities or []

    def execute(self, **kwargs: Any) -> Any:
        """
        Execute the underlying tool handler.
        """

        return self.handler(**kwargs)

    def get_registration(self) -> dict[str, Any]:
        """
        Return the tool registration metadata.
        """

        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
        }