from pathlib import Path
from typing import Any

from src.system_services.system_info import SystemInfoService


def create_agenticos_directory(
    base_directory: str | None = None,
) -> dict[str, Any]:
    """
    Create Documents/AgenticOS.
    """

    if base_directory is None:
        documents = Path.home() / "Documents"
    else:
        documents = Path(base_directory)

    agenticos_directory = (
        documents / "AgenticOS"
    )

    agenticos_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return {
        "path": str(agenticos_directory),
        "exists": agenticos_directory.exists(),
        "created": True,
    }


def get_cpu_information() -> dict[str, Any]:
    return SystemInfoService.cpu_info()


def get_memory_information() -> dict[str, Any]:
    return SystemInfoService.memory_info()


def get_system_snapshot() -> dict[str, Any]:
    return SystemInfoService.snapshot()