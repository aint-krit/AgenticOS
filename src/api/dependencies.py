from functools import lru_cache

from src.api.runtime import AgenticOSRuntime, create_runtime
from src.system_services.system_info import SystemInfoService


@lru_cache(maxsize=1)
def get_system_info_service() -> SystemInfoService:
    return SystemInfoService()


@lru_cache(maxsize=1)
def get_runtime() -> AgenticOSRuntime:
    return create_runtime()
