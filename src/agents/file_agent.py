from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.agent_runtime.agent import Agent


class FileAgent(Agent):
    """
    Handles basic file operations.

    v0.1 keeps file operations explicit and path-based.
    Permission enforcement will be expanded by the
    Capability/Security layer.
    """

    def __init__(
        self,
        agent_id: str = "file-agent",
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

    def create_file(
        self,
        path: str,
        content: str = "",
    ) -> dict[str, Any]:
        file_path = Path(path)

        if file_path.exists():
            raise FileExistsError(
                f"File already exists: {path}"
            )

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path.write_text(
            content,
            encoding="utf-8",
        )

        return {
            "status": "created",
            "path": str(file_path),
        }

    def read_file(
        self,
        path: str,
    ) -> dict[str, Any]:
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"File does not exist: {path}"
            )

        return {
            "status": "read",
            "path": str(file_path),
            "content": file_path.read_text(
                encoding="utf-8"
            ),
        }

    def write_file(
        self,
        path: str,
        content: str,
    ) -> dict[str, Any]:
        file_path = Path(path)

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path.write_text(
            content,
            encoding="utf-8",
        )

        return {
            "status": "written",
            "path": str(file_path),
        }

    def delete_file(
        self,
        path: str,
    ) -> dict[str, Any]:
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"File does not exist: {path}"
            )

        file_path.unlink()

        return {
            "status": "deleted",
            "path": str(file_path),
        }

    def receive_message(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        self.received_messages.append(message)

        payload = message.get("payload", {})
        operation = payload.get("operation")
        path = payload.get("path", "")

        if operation == "CREATE_FILE":
            result = self.create_file(
                path=path,
                content=payload.get(
                    "content",
                    "",
                ),
            )

        elif operation == "READ_FILE":
            result = self.read_file(
                path=path,
            )

        elif operation == "WRITE_FILE":
            result = self.write_file(
                path=path,
                content=payload.get(
                    "content",
                    "",
                ),
            )

        elif operation == "DELETE_FILE":
            result = self.delete_file(
                path=path,
            )

        else:
            result = {
                "status": "unsupported_operation",
                "operation": operation,
            }

        return {
            "message_id": message.get("message_id"),
            "request_id": message.get("request_id"),
            "sender": self.agent_id,
            "receiver": message.get("sender"),
            "message_type": "RESPONSE",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "payload": result,
        }