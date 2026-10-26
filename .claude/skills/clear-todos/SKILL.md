---
name: clear-todos
description: Deletes tasks from data/todos.json - finished tasks only by default, or every task with the "all" argument.
argument-hint: "[done|all]"
disable-model-invocation: true
allowed-tools:
  - Bash(python *)
  - PowerShell(python *)
effort: low
---

# Clear to-dos (manual only)

Claude never loads this skill on its own (`disable-model-invocation: true`), because deleting
data should happen only when the user types `/clear-todos`.

The user's argument was: "$ARGUMENTS"

1. If the argument is `all`, run:
   ```bash
   python "${CLAUDE_SKILL_DIR}/../tracking-todos/scripts/todo.py" clear --all
   ```
   Otherwise (empty or `done`), run:
   ```bash
   python "${CLAUDE_SKILL_DIR}/../tracking-todos/scripts/todo.py" clear --done-only
   ```
2. Report how many tasks were removed and how many remain.
