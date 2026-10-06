import os
import platform
from typing import Any


class SystemInfoService:
    """
    Provides basic AgenticOS system information.

    v0.1 deliberately uses Python's standard library only.
    """

    @staticmethod
    def cpu_info() -> dict[str, Any]:
        logical_cpus = os.cpu_count()

        return {
            "logical_cpus": logical_cpus,
            "architecture": platform.machine(),
            "processor": platform.processor(),
        }

    @staticmethod
    def memory_info() -> dict[str, Any]:
        """
        Return memory information when available.

        Windows support uses GlobalMemoryStatusEx through ctypes.
        """

        if os.name != "nt":
            return {
                "available": False,
                "reason": "Memory information is currently "
                "implemented for Windows.",
            }

        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(
            MEMORYSTATUSEX
        )

        result = ctypes.windll.kernel32.GlobalMemoryStatusEx(
            ctypes.byref(status)
        )

        if not result:
            return {
                "available": False,
                "reason": "Unable to query system memory.",
            }

        total_gb = (
            status.ullTotalPhys
            / (1024 ** 3)
        )

        available_gb = (
            status.ullAvailPhys
            / (1024 ** 3)
        )

        used_gb = total_gb - available_gb

        return {
            "available": True,
            "memory_load_percent": status.dwMemoryLoad,
            "total_gb": round(total_gb, 2),
            "available_gb": round(available_gb, 2),
            "used_gb": round(used_gb, 2),
        }

    @classmethod
    def snapshot(cls) -> dict[str, Any]:
        """
        Return a combined CPU + memory snapshot.
        """

        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "cpu": cls.cpu_info(),
            "memory": cls.memory_info(),
        }