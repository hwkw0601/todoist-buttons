"""Local web backend for the Todoist button app.

Acts as an MCP *client*: it launches the existing Todoist MCP server
(../todoist-mcp/server.py) over stdio and calls its tools when the browser asks.
It never talks to the Todoist API directly and never reads or stores the token —
server.py reads TODOIST_API_TOKEN from its own .env (because we launch it with
cwd set to the MCP project).

Run:  uv run app.py   →  http://127.0.0.1:8000
"""

import asyncio
import logging
import sys
from pathlib import Path

import uvicorn
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("todoist-buttons")

UV = "/Users/hyowonkwon/.local/bin/uv"
MCP_PROJECT = "/Users/hyowonkwon/Desktop/todoist-mcp"
STATIC = Path(__file__).parent / "static"

# One MCP client over stdio. keep_alive=True reuses a single server subprocess
# across calls; a lock serializes access (one stdio session at a time).
_transport = StdioTransport(
    command=UV,
    args=["run", "server.py"],
    cwd=MCP_PROJECT,
    keep_alive=True,
)
_client = Client(_transport)
_lock = asyncio.Lock()


def _result_text(result) -> str:
    """Pull the plain-text return out of an MCP call result."""
    data = getattr(result, "data", None)
    if isinstance(data, str):
        return data
    content = getattr(result, "content", None) or []
    texts = [getattr(b, "text", "") for b in content if getattr(b, "type", "") == "text"]
    if texts:
        return "\n".join(texts)
    return "" if data is None else str(data)


async def _call(name: str, args: dict) -> str:
    async with _lock:
        async with _client:
            result = await _client.call_tool(name, args)
    return _result_text(result)


async def index(request: Request):
    return FileResponse(STATIC / "index.html")


async def tools(request: Request):
    try:
        async with _lock:
            async with _client:
                tool_list = await _client.list_tools()
        return JSONResponse({"ok": True, "tools": [t.name for t in tool_list]})
    except Exception as exc:  # noqa: BLE001 - surface a readable error to the UI
        logger.exception("list_tools failed")
        return JSONResponse({"ok": False, "error": f"MCP server error: {type(exc).__name__}"})


async def list_active_tasks(request: Request):
    try:
        text = await _call("list_active_tasks", {})
        return JSONResponse({"ok": True, "text": text})
    except Exception as exc:  # noqa: BLE001
        logger.exception("list_active_tasks failed")
        return JSONResponse({"ok": False, "error": f"Could not list tasks: {type(exc).__name__}"})


async def list_completed_tasks(request: Request):
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    days = body.get("days", 7)
    try:
        text = await _call("list_completed_tasks", {"days": days})
        return JSONResponse({"ok": True, "text": text})
    except Exception as exc:  # noqa: BLE001
        logger.exception("list_completed_tasks failed")
        return JSONResponse(
            {"ok": False, "error": f"Could not list completed tasks: {type(exc).__name__}"}
        )


async def create_task(request: Request):
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": "Invalid request body."})
    content = (body.get("content") or "").strip()
    if not content:
        return JSONResponse({"ok": False, "error": "Please enter a task name."})
    args: dict = {"content": content}
    if body.get("due_datetime"):
        args["due_datetime"] = body["due_datetime"]
    elif body.get("due_date"):
        args["due_date"] = body["due_date"]
    labels = body.get("labels")
    if labels:
        args["labels"] = labels if isinstance(labels, list) else [labels]
    try:
        text = await _call("create_task", args)
        return JSONResponse({"ok": True, "text": text})
    except Exception as exc:  # noqa: BLE001
        logger.exception("create_task failed")
        return JSONResponse({"ok": False, "error": f"Could not create task: {type(exc).__name__}"})


async def set_task_status(request: Request):
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": "Invalid request body."})
    task_id = (body.get("task_id") or "").strip()
    if not task_id:
        return JSONResponse({"ok": False, "error": "Pick a task first."})
    done = bool(body.get("done"))
    try:
        text = await _call("set_task_status", {"task_id": task_id, "done": done})
        return JSONResponse({"ok": True, "text": text})
    except Exception as exc:  # noqa: BLE001
        logger.exception("set_task_status failed")
        return JSONResponse({"ok": False, "error": f"Could not update task: {type(exc).__name__}"})


app = Starlette(
    routes=[
        Route("/", index),
        Route("/api/tools", tools),
        Route("/api/list_active_tasks", list_active_tasks, methods=["POST"]),
        Route("/api/list_completed_tasks", list_completed_tasks, methods=["POST"]),
        Route("/api/create_task", create_task, methods=["POST"]),
        Route("/api/set_task_status", set_task_status, methods=["POST"]),
    ]
)


if __name__ == "__main__":
    logger.info("Starting todoist-buttons on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
