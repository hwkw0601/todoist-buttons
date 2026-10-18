# Weekly Planner (Todoist-synced)

A **local weekly timetable planner that syncs two-way with Todoist**. Drag tasks onto the timetable,
check them off, and manage recurring tasks and a fixed class/work schedule. Every Todoist operation
goes through a locally-run MCP server, so **your API token never leaves your computer.**

> Switch the UI with the **EN / 한국어** button in the header (English / Korean).

---

## How it fits together

```
Browser (planner UI)  →  Local backend (MCP client)  →  Todoist MCP server (stdio)  →  Todoist
```

- The browser never calls Todoist directly — it only calls the backend (HTTP).
- The backend reaches Todoist **only through the MCP server's tools.**
- The token lives **only in the MCP server's `.env`.**

It's made of two folders (repos):

| Folder | Role |
|--------|------|
| `todoist-mcp` | The MCP server that talks to the Todoist API (Python + FastMCP). 6 tools |
| `todoist-buttons` | The planner web app — backend (MCP client) + UI. The folder this file is in |

MCP server tools: `list_active_tasks`, `create_task`, `set_task_status`, `update_task`,
`list_completed_tasks`, `delete_task`.

---

## Requirements

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** (Python package/run tool)
- A **Todoist account** and a **personal API token**

### Getting your Todoist API token
In Todoist, go to **Settings → Integrations → Developer → "API token"** and copy it.

> ⚠️ A personal token **cannot be scoped.** A single token grants **read/write/delete** over your
> entire account. Put it only in the `.env` file below (never commit it) and never share it.

---

## Install & run

1. Get both folders (clone from GitHub or download).
   ```
   todoist-mcp/
   todoist-buttons/
   ```

2. **Add your token** — inside `todoist-mcp`:
   ```bash
   cp .env.example .env
   # open .env and paste: TODOIST_API_TOKEN=your_token_here
   ```
   `.env` is git-ignored (never committed).

3. **Install dependencies** — in each folder:
   ```bash
   cd todoist-mcp && uv sync
   cd ../todoist-buttons && uv sync
   ```

4. **Fix the paths (required on a different machine)** — edit the two lines at the top of
   `todoist-buttons/app.py` to match your environment:
   ```python
   UV = "/absolute/path/to/uv"                 # result of `which uv`
   MCP_PROJECT = "/absolute/path/to/todoist-mcp"  # absolute path of the todoist-mcp folder
   ```

5. **Run** — inside `todoist-buttons`:
   ```bash
   uv run app.py
   ```

6. Open **http://127.0.0.1:8000** in your browser.
   > Always open this **address**. Double-clicking `index.html` directly breaks the Todoist sync and
   > uses a separate storage (your data can look mixed up). **Always use a single tab.**

On first open, your active Todoist tasks load automatically. Try creating one task (see "Add a task"
below) and check that it shows up in the Todoist mobile app.

---

## Main features

### 1. Idea Dump (top)
- A pool of undated tasks, sorted by **closest deadline first** (D-day).
- **All / by-category** toggle.
- **Click** an empty spot, or the **+** button (bottom right), to add quickly.
- Cards are color-coded by category, with a **round checkbox** to complete.

### 2. Weekly timetable (center)
- Mon–Sun for one week. Default 08:00–24:00 (adjustable in settings).
- **Drag** an idea onto the timetable to turn it into a task. Overlaps are rejected (shown in red).
- **Click** an empty slot to open quick-add preset to that time (snaps to 30 min).
- **Fixed blocks** (classes/shifts) repeat every week and hide on holidays / outside the term.
  - Solid grey block = **not placeable**; dashed grey block = **placeable** (you can drop a task inside).
- Task block: name, time, duration, place, deadline (D-day). **When completed**, it switches to an
  outline + check.

### 3. Per-date ideas (below the timetable, scrolls together with it)
- Tasks that have a date but no time yet. Drag one up into the timetable to turn it into a task.

### 4. Add / edit a task
- Name, category, date, **duration (up to 12 hours)**, start time (5-min steps), **deadline**, **place**.
- **Event** checkbox → classified as an "event" with no completion checkbox, and **not pushed to Todoist**.
- **Weekly repeat** checkbox → repeats on that weekday every week. You can also set a **repeat end date**.

### 5. Fixed schedule
- Add/edit from the **Fixed schedule** button. Overlapping times are blocked.
- Click a fixed block in the timetable to **delete just that day** (confirm popup → undo toast).

### 6. Todoist auto-sync (two-way)
- Reads: on load + automatically **every 60 seconds** (so changes made on your phone show up). Click
  the status chip for an immediate refresh.
- Writes: giving a date creates it; checking complete → close; unchecking → reopen; changing
  date/time → update; deleting → delete in Todoist too.
- **Weekly-repeat** tasks are created in Todoist as **recurring** tasks (like `every monday at 15:30`,
  with `until <date>` for an end date).

### 7. Settings / language
- **Settings**: timetable start/end, term name and start/end dates, holidays, reset everything.
- **EN / 한국어** button switches the whole UI (the text of items you entered stays as-is).

---

## Data & caveats

- Planner-only data (placements, fixed schedule, categories, etc.) is stored in **browser
  localStorage** — never sent to a server. Todoist only holds **name, due, labels, and completion
  status** (place, deadline, and weekday placement are planner-only).
- localStorage is **separate per address (origin) and per browser.** Always work in a single tab at
  `http://127.0.0.1:8000` (mixing tabs / a file preview can cause confusing overwrites).
- A recurring Todoist task, once completed, **rolls over to the next week and stays active** (normal
  recurring behavior).

## Security

- The token lives only in `todoist-mcp/.env`. By design it is **never exposed** in logs, the screen,
  or error messages.
- Create/complete/delete change your **live account**. If you need narrower access, you'd have to use
  OAuth scopes (`data:read`, `task:add`, etc.) instead of a personal token — but this app assumes a
  personal token.

## Troubleshooting

- **UI looks broken or stale** → hard refresh (⌘/Ctrl + Shift + R).
- **Todoist sync fails** → check the token in `.env`, and that you ran `uv sync` in `todoist-mcp`.
- **`uv: command not found`** → set `UV` in `app.py` to the result of `which uv`.
- **Backend won't start** → check that `MCP_PROJECT` in `app.py` is the correct path.
