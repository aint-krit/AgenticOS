
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.agent_runtime.agent import Agent
from src.capability.permissions import PermissionManager


class FileAgent(Agent):
    """File operations with permission enforcement."""

    OPERATION_CAPABILITIES = {
        "CREATE_FILE": "create_file",
        "READ_FILE": "read_file",
        "WRITE_FILE": "write_file",
        "DELETE_FILE": "delete_file",
    }

    def __init__(
        self,
        agent_id: str = "file-agent",
        permission_manager: PermissionManager | None = None,
        workspace_root: str | Path | None = None,
    ):
        super().__init__(
            agent_id=agent_id,
            name="File Agent",
            agent_type="specialized",
            capabilities=[
                "create_file",
                "read_file",
                "write_file",
                "delete_file",
            ],
        )

        self.permission_manager = permission_manager
        self.workspace_root = (
            Path(workspace_root).resolve()
            if workspace_root is not None
            else None
        )

    def set_permission_manager(
        self,
        permission_manager: PermissionManager,
    ) -> None:
        self.permission_manager = permission_manager

    def _require_permission(self, capability: str) -> None:
        # Preserve legacy direct calls when no manager is configured.
        # Once a manager is attached, authorization is mandatory.
        if self.permission_manager is not None:
            self.permission_manager.require_permission(
                self.agent_id,
                capability,
            )

    def _require_message_permission(self, capability: str) -> None:
        # Message execution always fails closed without a manager.
        if self.permission_manager is None:
            raise PermissionError(
                "FileAgent has no permission manager configured."
            )

        self.permission_manager.require_permission(
            self.agent_id,
            capability,
        )

    def _validate_path(self, path: str) -> Path:
        if not isinstance(path, str) or not path.strip():
            raise ValueError("A non-empty file path is required.")

        candidate = Path(path)

        # Preserve existing standalone FileAgent behaviour.
        if self.workspace_root is None:
            return candidate

        # When confined to a workspace, only relative paths are allowed.
        if candidate.is_absolute():
            raise ValueError("Absolute paths are not allowed.")

        resolved = (self.workspace_root / candidate).resolve()

        if not resolved.is_relative_to(self.workspace_root):
            raise ValueError(
                "Path must remain inside the AgenticOS workspace."
            )

        return resolved

    def _create_file(
        self,
        path: str,
        content: str = "",
    ) -> dict[str, Any]:
        file_path = self._validate_path(path)

        if file_path.exists():
            raise FileExistsError(f"File already exists: {path}")

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return {
            "status": "created",
            "path": str(file_path),
        }

    def _read_file(self, path: str) -> dict[str, Any]:
        file_path = self._validate_path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")

        if not file_path.is_file():
            raise IsADirectoryError(f"Path is not a file: {path}")

        return {
            "status": "read",
            "path": str(file_path),
            "content": file_path.read_text(encoding="utf-8"),
        }

    def _write_file(
        self,
        path: str,
        content: str,
    ) -> dict[str, Any]:
        file_path = self._validate_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return {
            "status": "written",
            "path": str(file_path),
        }

    def _delete_file(self, path: str) -> dict[str, Any]:
        file_path = self._validate_path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")

        if not file_path.is_file():
            raise IsADirectoryError(f"Path is not a file: {path}")

        file_path.unlink()

        return {
            "status": "deleted",
            "path": str(file_path),
        }

    def create_file(
        self,
        path: str,
        content: str = "",
    ) -> dict[str, Any]:
        self._require_permission("create_file")
        return self._create_file(path, content)

    def read_file(self, path: str) -> dict[str, Any]:
        self._require_permission("read_file")
        return self._read_file(path)

    def write_file(
        self,
        path: str,
        content: str,
    ) -> dict[str, Any]:
        self._require_permission("write_file")
        return self._write_file(path, content)

    def delete_file(self, path: str) -> dict[str, Any]:
        self._require_permission("delete_file")
        return self._delete_file(path)

    def receive_message(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        payload = message.get("payload", {})
        operation = payload.get("operation")
        capability = self.OPERATION_CAPABILITIES.get(operation)

        try:
            if capability is None:
                raise ValueError(
                    f"Unsupported file operation: {operation!r}"
                )

            self._require_message_permission(capability)
            path = payload.get("path")

            if operation == "CREATE_FILE":
                result = self._create_file(
                    path,
                    payload.get("content", ""),
                )
            elif operation == "READ_FILE":
                result = self._read_file(path)
            elif operation == "WRITE_FILE":
                result = self._write_file(
                    path,
                    payload.get("content", ""),
                )
            else:
                result = self._delete_file(path)

            response_type = "RESPONSE"

        except Exception as error:
            result = {
                "status": "error",
                "error_type": type(error).__name__,
                "error": str(error),
            }
            response_type = "ERROR"

        self.received_messages.append(dict(message))

        return {
            "message_id": message.get("message_id"),
            "request_id": message.get("request_id"),
            "sender": self.agent_id,
            "receiver": message.get("sender"),
            "message_type": response_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": result,
        }