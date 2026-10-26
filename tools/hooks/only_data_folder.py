"""A hook script for Claude Code: Write and Edit may only change files inside data/ (Lesson 9, Exercise 8).

WHAT
    Claude Code runs this script just before each Write or Edit tool call (a PreToolUse hook). The
    script allows the call when the file is inside the project's data folder, and blocks it otherwise.

WHY
    A rule that Claude Code itself enforces, whatever Claude decides. It works in the interactive
    claude window and with claude -p, without changing any program. It is the settings-file version
    of the Python hook in agent/guarded_agent.py.

HOW IT WORKS
    Claude Code sends the planned tool call as JSON on stdin, for example
        {"tool_name": "Write", "tool_input": {"file_path": ".../notes.txt", ...}, "cwd": ".../claudecodecli_and_python"}
    The script checks that file_path lies inside <cwd>/data, and then ends with:
        exit code 0  ->  Claude Code runs the tool call;
        exit code 2  ->  Claude Code blocks it, and shows Claude the text printed on stderr.

HOW TO SWITCH IT ON
    Put this into .claude/settings.json of the project, then start claude again:
        {"hooks": {"PreToolUse": [{"matcher": "Write|Edit",
            "hooks": [{"type": "command", "command": "python tools/hooks/only_data_folder.py"}]}]}}
    To switch it off again, delete that settings file (the exercise does this at the end).

WHICH WAY TO REACH CLAUDE
    None: it never calls Claude. Claude Code calls it.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k only_data_folder
       Expected (1 test; the time differs):
           .
           ----------------------------------------------------------------------
           Ran 1 test in 0.384s

           OK
       What it checks: exit code 0 for a file inside data/, and exit code 2 with the message for a file
       outside, also for data/../. Add -v to see the name of each test.
    2. By hand: free.
           echo {"tool_input": {"file_path": "notes.txt"}, "cwd": "."} | python tools/hooks/only_data_folder.py
               Blocked by hook: files may only be written inside data        (exit code 2)
           echo {"tool_input": {"file_path": "data/notes.txt"}, "cwd": "."} | python tools/hooks/only_data_folder.py
               (prints nothing: exit code 0)
           echo %errorlevel% shows the exit code of the last command.
    3. With Claude: uses a little Pro allowance.
           Switch the hook on (HOW TO SWITCH IT ON), start claude, and ask: "Save the word hello in notes.txt".
           Claude's Write is blocked with the message above, and Claude offers data/notes.txt instead
           (Lesson 9, Exercise 8).

IF SOMETHING GOES WRONG
    - The hook doesn't run: Claude Code reads settings when it starts, so exit claude and start it again.
    - Everything is blocked: "cwd" in the input decides where data/ is; start claude in the project folder.

FILES IT READS AND WRITES
    None.

SEE ALSO
    agent/guard_hook.py (a hook that answers with JSON instead of exit codes); Lesson 9, Exercise 8.
"""
import json
import sys
from pathlib import Path

event = json.load(sys.stdin)                      # Claude Code sends the planned tool call as JSON
target = Path(event["tool_input"].get("file_path", ""))
allowed = Path(event["cwd"]) / "data"
try:
    target.resolve().relative_to(allowed.resolve())
except ValueError:
    print(f"Blocked by hook: files may only be written inside {allowed}", file=sys.stderr)
    sys.exit(2)                                   # exit code 2 = block the tool call
sys.exit(0)                                       # exit code 0 = allow it
