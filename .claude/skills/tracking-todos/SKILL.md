---
name: tracking-todos
description: Keeps a persistent to-do list for this project in data/todos.json - adds tasks with optional due date and priority, lists open or all tasks, and marks tasks done. Use when the user says "remind me to", "add a task", "what's on my list", "what's due", or "mark X as done".
allowed-tools:
  - Bash(python *)
  - PowerShell(python *)
effort: low
---

# Tracking to-dos

The list lives in `data/todos.json` (relative to the project root). The script creates it if missing.
Run commands from the project root.

| Action | Command |
|---|---|
| Add | `python "${CLAUDE_SKILL_DIR}/scripts/todo.py" add "Send the Q3 report" --due 2026-10-20 --priority high` |
| List open tasks | `python "${CLAUDE_SKILL_DIR}/scripts/todo.py" list` |
| List everything | `python "${CLAUDE_SKILL_DIR}/scripts/todo.py" list --all` |
| Mark done | `python "${CLAUDE_SKILL_DIR}/scripts/todo.py" done 3` |

- `--priority` is `high`, `normal` (default) or `low`. `--due` is `YYYY-MM-DD`; resolve "Friday" or
  "tomorrow" to a real date first.
- To mark a task done by its text, run `list` first to find its `id`.
- `list` sorts by priority, then due date, and flags `"overdue": true`. Mention overdue tasks first.

Deleting tasks is deliberately **not** part of this skill. If the user wants the list cleared,
tell them to run `/clear-todos` themselves.
