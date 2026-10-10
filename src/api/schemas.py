from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class AgentResponse(BaseModel):
    agent_id: str
    name: str
    version: str
    type: str
    status: str
    capabilities: list[str] = Field(default_factory=list)


class CapabilityResponse(BaseModel):
    capabilities: list[str]
    tools: list[dict[str, Any]]


class SystemResponse(BaseModel):
    platform: str
    platform_version: str
    cpu: dict[str, Any]
    memory: dict[str, Any]


class CreateFileRequest(BaseModel):
    path: str
    content: str = ""


class WriteFileRequest(BaseModel):
    path: str
    content: str = ""


class DeleteFileRequest(BaseModel):
    path: str


class FileResponse(BaseModel):
    status: str
    path: str
    content: str | None = None


# Compatibility aliases
FileCreateRequest = CreateFileRequest
FileWriteRequest = WriteFileRequest
FileDeleteRequest = DeleteFileRequest