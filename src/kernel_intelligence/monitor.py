from __future__ import annotations

import os
import platform
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ResourceSnapshot:
    timestamp: float
    platform: str
    logical_cpus: int
    cpu_percent: float | None
    memory_total_mb: float | None
    memory_available_mb: float | None
    memory_percent: float | None
    load_average: tuple[float, ...] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResourceMonitor:
    """
    Read-only resource monitoring interface.

    The monitor collects observations but does not modify system resources.
    A custom provider can be injected for Linux integration, hardware agents,
    deterministic tests, or future telemetry collectors.
    """

    def __init__(
        self,
        provider: Callable[[], dict[str, Any]] | None = None,
    ) -> None:
        self.provider = provider
        self._last_cpu_times: tuple[float, float] | None = None

    def collect(self) -> ResourceSnapshot:
        if self.provider is not None:
            data = self.provider()
            return ResourceSnapshot(
                timestamp=float(data.get("timestamp", time.time())),
                platform=str(
                    data.get("platform", platform.system())
                ),
                logical_cpus=int(
                    data.get("logical_cpus", os.cpu_count() or 1)
                ),
                cpu_percent=self._optional_float(
                    data.get("cpu_percent")
                ),
                memory_total_mb=self._optional_float(
                    data.get("memory_total_mb")
                ),
                memory_available_mb=self._optional_float(
                    data.get("memory_available_mb")
                ),
                memory_percent=self._optional_float(
                    data.get("memory_percent")
                ),
                load_average=self._load_average(
                    data.get("load_average")
                ),
            )

        return self._collect_local()

    def _collect_local(self) -> ResourceSnapshot:
        memory = self._memory_info()

        load_average: tuple[float, ...] | None = None
        try:
            values = os.getloadavg()
            load_average = tuple(float(value) for value in values)
        except (AttributeError, OSError):
            pass

        return ResourceSnapshot(
            timestamp=time.time(),
            platform=platform.system(),
            logical_cpus=os.cpu_count() or 1,
            cpu_percent=None,
            memory_total_mb=memory["total_mb"],
            memory_available_mb=memory["available_mb"],
            memory_percent=memory["percent"],
            load_average=load_average,
        )

    @staticmethod
    def _memory_info() -> dict[str, float | None]:
        if platform.system() == "Windows":
            try:
                import ctypes

                class MemoryStatus(ctypes.Structure):
                    _fields_ = [
                        ("length", ctypes.c_ulong),
                        ("memory_load", ctypes.c_ulong),
                        ("total_physical", ctypes.c_ulonglong),
                        ("available_physical", ctypes.c_ulonglong),
                        ("total_page_file", ctypes.c_ulonglong),
                        ("available_page_file", ctypes.c_ulonglong),
                        ("total_virtual", ctypes.c_ulonglong),
                        ("available_virtual", ctypes.c_ulonglong),
                        ("available_extended", ctypes.c_ulonglong),
                    ]

                status = MemoryStatus()
                status.length = ctypes.sizeof(MemoryStatus)

                if ctypes.windll.kernel32.GlobalMemoryStatusEx(
                    ctypes.byref(status)
                ):
                    return {
                        "total_mb": status.total_physical / (1024 * 1024),
                        "available_mb": (
                            status.available_physical
                            / (1024 * 1024)
                        ),
                        "percent": float(status.memory_load),
                    }
            except (AttributeError, OSError):
                pass

        return {
            "total_mb": None,
            "available_mb": None,
            "percent": None,
        }

    @staticmethod
    def _optional_float(value: Any) -> float | None:
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _load_average(
        value: Any,
    ) -> tuple[float, ...] | None:
        if value is None:
            return None

        try:
            return tuple(float(item) for item in value)
        except (TypeError, ValueError):
            return None
