from abc import ABC, abstractmethod
from typing import Any


class Connector(ABC):
    """
    Interface for external or system-level capability connectors.
    """

    def __init__(
        self,
        connector_id: str,
        name: str,
    ):
        self.connector_id = connector_id
        self.name = name
        self.connected = False

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def execute(
        self,
        operation: str,
        **kwargs: Any,
    ) -> Any:
        pass

    def health(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "name": self.name,
            "connected": self.connected,
        }


class FunctionConnector(Connector):
    """
    Simple local connector backed by registered Python functions.

    Useful for v0.1 because it lets the Capability Layer use
    the same connector contract without requiring external services.
    """

    def __init__(
        self,
        connector_id: str,
        name: str,
    ):
        super().__init__(
            connector_id=connector_id,
            name=name,
        )

        self.operations: dict[str, Any] = {}

    def connect(self) -> None:
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def register_operation(
        self,
        operation: str,
        handler: Any,
    ) -> None:
        if not operation.strip():
            raise ValueError(
                "operation must be a non-empty string."
            )

        if not callable(handler):
            raise ValueError(
                "handler must be callable."
            )

        self.operations[operation] = handler

    def execute(
        self,
        operation: str,
        **kwargs: Any,
    ) -> Any:
        if not self.connected:
            raise RuntimeError(
                f"Connector '{self.connector_id}' is not connected."
            )

        if operation not in self.operations:
            raise ValueError(
                f"Operation '{operation}' is not registered."
            )

        return self.operations[operation](**kwargs)
    