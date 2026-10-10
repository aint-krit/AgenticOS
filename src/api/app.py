from typing import Any

from fastapi import Body, Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from src.api.dependencies import (
    get_runtime,
    get_system_info_service,
)
from src.api.runtime import AgenticOSRuntime
from src.api.schemas import (
    AgentResponse,
    CapabilityResponse,
    CreateFileRequest,
    DeleteFileRequest,
    FileResponse,
    HealthResponse,
    PromptRequest,
    PromptResponse,
    SystemResponse,
    WriteFileRequest,
)
from src.ui.dashboard import get_dashboard_html

app = FastAPI(
    title="AgenticOS API",
    description="API layer for the AgenticOS agent runtime.",
    version="0.1.0",
)


@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse(content=get_dashboard_html(), status_code=200)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="AgenticOS",
        version=app.version,
    )


@app.get("/api/system", response_model=SystemResponse)
def system_info() -> SystemResponse:
    return SystemResponse(
        **get_system_info_service().snapshot()
    )


@app.get("/api/agents", response_model=list[AgentResponse])
def list_agents() -> list[AgentResponse]:
    runtime = get_runtime()
    agents = runtime.agent_manager.discover_agents()
    return [AgentResponse(**agent) for agent in agents]


@app.get("/api/agents/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: str) -> AgentResponse:
    runtime = get_runtime()
    try:
        agent = runtime.agent_manager.get_agent(agent_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return AgentResponse(**agent)


@app.get("/api/capabilities", response_model=CapabilityResponse)
def list_capabilities() -> CapabilityResponse:
    runtime = get_runtime()
    return CapabilityResponse(
        capabilities=runtime.capability_registry.discover_capabilities(),
        tools=runtime.capability_registry.discover_tools(),
    )


def _execute_file_intent(
    runtime: AgenticOSRuntime,
    intent: str,
    description: str,
    payload: dict[str, Any],
) -> FileResponse:
    path = payload.get("path")
    if not isinstance(path, str) or not path.strip():
        raise HTTPException(
            status_code=400,
            detail="A non-empty file path is required.",
        )

    try:
        result = runtime.platform.execute_intent(
            intent=intent,
            description=description,
            payload=payload,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        msg = str(exc)
        msg_lower = msg.lower()
        if "already exists" in msg_lower:
            status_code = 409
        elif "does not exist" in msg_lower:
            status_code = 404
        elif (
            "absolute path" in msg_lower
            or "workspace" in msg_lower
            or "non-empty" in msg_lower
            or "not a file" in msg_lower
            or "unsupported file operation" in msg_lower
        ):
            status_code = 400
        else:
            status_code = 400
        raise HTTPException(
            status_code=status_code,
            detail=msg,
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except FileExistsError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except IsADirectoryError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    task_results = result.get("results", {})
    if not task_results:
        raise HTTPException(
            status_code=500,
            detail="No result returned from agent execution.",
        )

    first_response = next(iter(task_results.values()))
    response_payload = first_response.get("payload", {})

    return FileResponse(
        status=response_payload.get("status", "ok"),
        path=response_payload.get("path", path),
        content=response_payload.get("content"),
    )


@app.post("/api/files", response_model=FileResponse)
def create_file(
    request: CreateFileRequest,
    runtime: AgenticOSRuntime = Depends(get_runtime),
) -> FileResponse:
    return _execute_file_intent(
        runtime=runtime,
        intent="create_file",
        description=f"Create file {request.path}",
        payload={"path": request.path, "content": request.content},
    )


@app.get("/api/files", response_model=FileResponse)
def read_file(
    path: str = Query(..., description="Relative file path inside workspace"),
    runtime: AgenticOSRuntime = Depends(get_runtime),
) -> FileResponse:
    return _execute_file_intent(
        runtime=runtime,
        intent="read_file",
        description=f"Read file {path}",
        payload={"path": path},
    )


@app.get("/api/files/{file_path:path}", response_model=FileResponse)
def read_file_path(
    file_path: str,
    runtime: AgenticOSRuntime = Depends(get_runtime),
) -> FileResponse:
    return _execute_file_intent(
        runtime=runtime,
        intent="read_file",
        description=f"Read file {file_path}",
        payload={"path": file_path},
    )


@app.put("/api/files", response_model=FileResponse)
def write_file(
    request: WriteFileRequest,
    runtime: AgenticOSRuntime = Depends(get_runtime),
) -> FileResponse:
    return _execute_file_intent(
        runtime=runtime,
        intent="write_file",
        description=f"Write file {request.path}",
        payload={"path": request.path, "content": request.content},
    )


@app.delete("/api/files", response_model=FileResponse)
def delete_file(
    request: DeleteFileRequest | None = Body(default=None),
    path: str | None = Query(default=None),
    runtime: AgenticOSRuntime = Depends(get_runtime),
) -> FileResponse:
    target_path = (request.path if request else None) or path
    if not target_path or not target_path.strip():
        raise HTTPException(
            status_code=400,
            detail="A non-empty file path is required.",
        )
    return _execute_file_intent(
        runtime=runtime,
        intent="delete_file",
        description=f"Delete file {target_path}",
        payload={"path": target_path},
    )


@app.delete("/api/files/{file_path:path}", response_model=FileResponse)
def delete_file_path(
    file_path: str,
    runtime: AgenticOSRuntime = Depends(get_runtime),
) -> FileResponse:
    return _execute_file_intent(
        runtime=runtime,
        intent="delete_file",
        description=f"Delete file {file_path}",
        payload={"path": file_path},
    )


@app.post("/api/prompt", response_model=PromptResponse)
def execute_user_prompt(
    request: PromptRequest,
    runtime: AgenticOSRuntime = Depends(get_runtime),
) -> PromptResponse:
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(
            status_code=400,
            detail="Prompt must be a non-empty string.",
        )

    try:
        result = runtime.platform.execute_prompt(request.prompt)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return PromptResponse(
        status=result.get("status", "completed"),
        request_id=result.get("request_id", ""),
        prompt=result.get("prompt", request.prompt),
        verified=result.get("verified", False),
        clarification_prompt=result.get("clarification_prompt"),
        goal=result.get("goal"),
        workflow=result.get("workflow"),
        intents=result.get("intents", []),
        results=result.get("results", {}),
        trace=result.get("trace", []),
    )

