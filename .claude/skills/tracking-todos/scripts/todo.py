"""A to-do list that is kept between conversations, in a JSON file. The script of the tracking-todos and clear-todos skills (Lesson 3, Pattern D).

WHAT
    Four commands:
        add "TEXT" [--due YYYY-MM-DD] [--priority high|normal|low]   adds a task, and prints it with its id
        list [--all]                                 the open tasks (with --all also the finished ones),
                                                     high priority and earliest due date first, each
                                                     with "overdue": true or false
        done ID                                      marks a task as finished
        clear --done-only | --all                    deletes the finished tasks, or all tasks
    The list is kept in data/todos.json. Another file: --file PATH (before the command), or the
    environment variable TODO_FILE.

WHY
    Claude forgets everything when a conversation ends. A file keeps the list, and the script keeps
    it valid JSON with unique ids, so Claude never edits the file by hand.

HOW CLAUDE USES IT
    The tracking-todos SKILL.md lets Claude add, list and finish tasks. Deleting is only in the
    clear-todos skill, which has disable-model-invocation: true: Claude can't start it, only you can,
    by typing /clear-todos (Lesson 3, Step D5). Both skills run this same script (Lesson 4, Step 4).

HOW TO RUN IT YOURSELF  (in cmd, from the project folder; a practice file keeps your real list safe)
    python .claude/skills/tracking-todos/scripts/todo.py --file data/practice_todos.json add "Send report" --due 2026-10-30 --priority high
        {"added": {"id": 1, "text": "Send report", "priority": "high", "due": "2026-10-30", "done": false,
         "created": "2026-10-25"}}
    python .claude/skills/tracking-todos/scripts/todo.py --file data/practice_todos.json list
    python .claude/skills/tracking-todos/scripts/todo.py --file data/practice_todos.json done 1
    python .claude/skills/tracking-todos/scripts/todo.py --file data/practice_todos.json clear --done-only

ERRORS
    A wrong priority, date or id prints {"error": ...} with exit code 1, for example
        {"error": "priority must be one of ['high', 'normal', 'low'], got 'urgent'."}

NEEDS
    Only the standard library. It never calls Claude.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k TrackingTodos
       Expected (2 tests; the time differs):
           ..
           ----------------------------------------------------------------------
           Ran 2 tests in 1.190s

           OK
       What they check: add, list, done and clear on a temporary list (never your real one), and the
       error for a wrong priority. Add -v to see the name of each test.
    2. By hand: free.
           python .claude/skills/tracking-todos/scripts/todo.py --file data/practice_todos.json add "Check the tests" --priority high
               {"added": {"id": 1, "text": "Check the tests", "priority": "high", "due": null, "done": false, "created": "2026-10-25"}}
           python .claude/skills/tracking-todos/scripts/todo.py --file data/practice_todos.json done 1
               {"done": {"id": 1, "text": "Check the tests", "priority": "high", "due": null, "done": true, "created": "2026-10-25"}}
           python .claude/skills/tracking-todos/scripts/todo.py --file data/practice_todos.json clear --done-only
               {"removed": 1, "remaining": 0}
           Then delete data/practice_todos.json. ("created" is the date of your run.)
    3. With Claude: uses a little Pro allowance.
           set TODO_FILE=data/practice_todos.json             (so the task goes into a practice list, not your real one)
           claude -p "Remind me to check the tests by 2026-10-30." --model haiku --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)"
           type data/practice_todos.json
               Expected: a task "Check the tests" with "due": "2026-10-30" (the real run gave it id 1, priority
               normal). Then delete data/practice_todos.json, and run: set TODO_FILE=

IF SOMETHING GOES WRONG
    - {"error": "No task with id 9. Existing ids: [...]"}: list --all shows every id.
    - A new, empty list appeared somewhere else: data/todos.json is relative to the current folder, so run
      the command (and claude) from the project folder.

FILES IT READS AND WRITES
    Reads and writes data/todos.json (or the --file file, or TODO_FILE). The tests use temporary files.

SEE ALSO
    tracking-todos/SKILL.md and clear-todos/SKILL.md (both run this script); Lesson 3, Pattern D; Lesson
    4, Step 4.
"""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}
DEFAULT_FILE = "data/todos.json"


def store_path(explicit: str | None = None) -> Path:
    return Path(explicit or os.environ.get("TODO_FILE") or DEFAULT_FILE)


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else []


def save(path: Path, todos: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(todos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def add(path: Path, text: str, due: str | None = None, priority: str = "normal") -> dict:
    if not text.strip():
        raise ValueError("Task text is empty.")
    if priority not in PRIORITY_ORDER:
        raise ValueError(f"priority must be one of {list(PRIORITY_ORDER)}, got '{priority}'.")
    if due:
        try:
            date.fromisoformat(due)
        except ValueError:
            raise ValueError(f"--due must be YYYY-MM-DD, got '{due}'.") from None
    todos = load(path)
    task = {
        "id": max((t["id"] for t in todos), default=0) + 1,
        "text": text.strip(),
        "priority": priority,
        "due": due,
        "done": False,
        "created": date.today().isoformat(),
    }
    todos.append(task)
    save(path, todos)
    return {"added": task}


def list_tasks(path: Path, include_done: bool = False, today: date | None = None) -> dict:
    today = today or date.today()
    tasks = [t for t in load(path) if include_done or not t["done"]]
    for task in tasks:
        task["overdue"] = bool(task["due"] and not task["done"] and date.fromisoformat(task["due"]) < today)
    tasks.sort(key=lambda t: (t["done"], PRIORITY_ORDER[t["priority"]], t["due"] or "9999-12-31", t["id"]))
    return {"file": str(path), "count": len(tasks), "tasks": tasks}


def mark_done(path: Path, task_id: int) -> dict:
    todos = load(path)
    for task in todos:
        if task["id"] == task_id:
            task["done"] = True
            save(path, todos)
            return {"done": task}
    raise ValueError(f"No task with id {task_id}. Existing ids: {[t['id'] for t in todos]}")


def clear(path: Path, done_only: bool) -> dict:
    todos = load(path)
    kept = [t for t in todos if not t["done"]] if done_only else []
    save(path, kept)
    return {"removed": len(todos) - len(kept), "remaining": len(kept)}


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="Persistent to-do list.")
    parser.add_argument("--file", help=f"JSON store (default: $TODO_FILE or {DEFAULT_FILE})")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add")
    p_add.add_argument("text")
    p_add.add_argument("--due")
    p_add.add_argument("--priority", default="normal")

    p_list = sub.add_parser("list")
    p_list.add_argument("--all", action="store_true", help="include finished tasks")

    p_done = sub.add_parser("done")
    p_done.add_argument("id", type=int)

    p_clear = sub.add_parser("clear")
    group = p_clear.add_mutually_exclusive_group(required=True)
    group.add_argument("--done-only", action="store_true")
    group.add_argument("--all", action="store_true")

    args = parser.parse_args(argv)
    path = store_path(args.file)
    try:
        if args.command == "add":
            result = add(path, args.text, args.due, args.priority)
        elif args.command == "list":
            result = list_tasks(path, args.all)
        elif args.command == "done":
            result = mark_done(path, args.id)
        else:
            result = clear(path, done_only=args.done_only)
    except (ValueError, json.JSONDecodeError) as err:
        print(json.dumps({"error": str(err)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
