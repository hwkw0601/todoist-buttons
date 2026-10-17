# todoist-buttons

A tiny **local web app with buttons** for the Todoist tasks exposed by the
[`todoist-mcp`](../todoist-mcp) server — so you can list, add, and complete/reopen tasks by
clicking instead of chatting.

A browser can't speak stdio, so this app's small Python backend acts as the **MCP client**: it
launches `../todoist-mcp/server.py` over stdio and calls its three tools. It never calls the
Todoist API directly and **never sees the token** — `server.py` reads `TODOIST_API_TOKEN` from its
own `.env` (the backend launches it with that project as the working directory).

## Requirements
- The `todoist-mcp` project next door, working, with its `.env` token set.
- [uv](https://docs.astral.sh/uv/).

## Run
```bash
uv run app.py
```
Then open **http://127.0.0.1:8000**. Logs go to stderr; Ctrl-C to stop.

## Buttons
- **내 할 일 불러오기** → `list_active_tasks` — shows your open tasks and fills the picker below.
- **할 일 추가** → `create_task` — name, optional date and time (time → a specific time in your
  Asia/Seoul timezone), optional label.
- **완료 / 되돌리기** → `set_task_status` — pick a task from the list, then complete or reopen it.

Each button shows the tool's plain-text result, or a clear error message.

## How it connects
`app.py` uses FastMCP's client:
```python
StdioTransport(command="uv", args=["run", "server.py"],
               cwd="/Users/hyowonkwon/Desktop/todoist-mcp", keep_alive=True)
```
One shared client, one reused server subprocess, calls serialized with a lock.

## Scope
Just the three buttons — no timetable, no drag-and-drop, no persistence. The MCP server is reused
as-is and never modified.
