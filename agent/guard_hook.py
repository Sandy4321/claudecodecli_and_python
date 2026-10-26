"""The rules of guard.py as a hook script, for the claude -p way of guarded_agent.py (Lesson 6, Part 4, Step 15).

WHAT
    Claude Code runs this script before each Bash, PowerShell, Write and Edit call. It decides with
    the same Guard rules as the SDK way (guard.py), prints the decision for Claude Code on stdout,
    and a [guard] line for you on stderr.

WHY
    With claude -p, a hook can't be a function inside your program: it must be a separate program
    that Claude Code starts. guarded_agent.py --cli switches it on with --settings.

HOW IT WORKS
    Claude Code sends the planned tool call as JSON on stdin:
        {"tool_name": "Bash", "tool_input": {"command": "python ..."}, "effort": {"level": "low"}, ...}
    The script answers on stdout with the same JSON the SDK hook returns:
        {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow" or "deny",
                                "permissionDecisionReason": "..."}}
    Each tool call starts a new process, so nothing stays in memory between calls. The count of
    commands (at most 6 per run) is kept in the file named by the environment variable GUARD_STATE;
    guarded_agent.py creates a new file for each run. Without GUARD_STATE every call counts from 0.
    The [guard] line on stderr reaches your program because guarded_agent.py adds
    --include-hook-events: Claude Code then prints each hook's output as a JSON line too.

WHICH WAY TO REACH CLAUDE
    None: it never calls Claude. Claude Code calls it.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k guard_hook
       Expected (2 tests; the time differs):
           ..
           ----------------------------------------------------------------------
           Ran 2 tests in 1.089s

           OK
       What they check: 7 calls with one state file give 6 allows and then a deny (the limit), the
       [guard] line on stderr, and that guarded_agent.py --cli switches this hook on. Add -v to see the
       name of each test.
    2. By hand: free.
           echo {"tool_name": "Write", "tool_input": {"file_path": "data/report.txt"}} | python agent/guard_hook.py
               [guard] ALLOW Write: data/report.txt  (writing inside data/ is allowed)
               {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "permissionDecisionReason": "writing inside data/ is allowed"}}
           echo {"tool_name": "Write", "tool_input": {"file_path": "report.txt"}} | python agent/guard_hook.py
               [guard] DENY  Write: report.txt  (files may only be written inside data/, not report.txt)
               {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", ...}}
           Both end with exit code 0: the decision is in the JSON, not in the exit code.

IF SOMETHING GOES WRONG
    - "ModuleNotFoundError: No module named 'guard'": start the script by its path (agent/guard_hook.py);
      Python then also finds guard.py in that folder.
    - Claude Code reads stdout as the decision, so print nothing else there; use stderr for your own lines.

FILES IT READS AND WRITES
    Reads and writes the file named by GUARD_STATE (the command count of one run), if it is set.

SEE ALSO
    guard.py; guarded_agent.py; tools/hooks/only_data_folder.py (a hook that answers with exit codes
    instead); Lesson 6, Step 15.
"""

import json
import os
import sys
from pathlib import Path

from guard import Guard      # guard.py is in the same folder, which Python searches first

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    event = json.load(sys.stdin)
    state = os.environ.get("GUARD_STATE")              # a file that remembers the command count of this run
    guard = Guard()
    if state and Path(state).exists():
        guard.commands_run = int(Path(state).read_text(encoding="utf-8") or 0)
    tool_name, tool_input = event["tool_name"], event.get("tool_input") or {}
    allowed, reason = guard.check(tool_name, tool_input)
    if state:
        Path(state).write_text(str(guard.commands_run), encoding="utf-8")
    detail = tool_input.get("command") or tool_input.get("file_path") or ""
    print(f"[guard] {'ALLOW' if allowed else 'DENY '} {tool_name}: {detail}  ({reason})", file=sys.stderr)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow" if allowed else "deny",   # deny: the call doesn't run
            "permissionDecisionReason": reason,                      # Claude reads why
        }
    }))
