"""Prints the reasoning effort in effect before each tool call: the hook of effort_probe.py (Lesson 6, Part 6).

WHAT
    effort_line(hook_input) turns the input of a PreToolUse hook into one line, for example
        [effort] low    before Bash: python ".../convert.py" convert 26.2 mi km
    Both ways of effort_probe.py use it:
      - the SDK way calls effort_line() from its hook function, inside the program;
      - the claude -p way (effort_probe.py --cli) has Claude Code run this file as a hook script.

WHY
    The effort level is not in Claude's answer or in the usage numbers. Claude Code puts it into the
    input of every hook, as "effort": {"level": "low"}, so a hook is the place to see it.

HOW IT WORKS  (as a hook script)
    Claude Code sends the planned tool call as JSON on stdin, with the effort level in it. The script
    writes the line to stderr, and nothing to stdout: no decision, so the normal permission rules
    apply. effort_probe.py --cli adds --include-hook-events, so Claude Code passes the stderr text
    back as a JSON line, and the program prints it.

WHICH WAY TO REACH CLAUDE
    None: it never calls Claude. Claude Code (or effort_probe.py) calls it.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k effort_hook
       Expected (1 test; the time differs):
           .
           ----------------------------------------------------------------------
           Ran 1 test in 0.124s

           OK
       What it checks: the line goes to stderr and stdout stays empty, and the subagent name and a
       missing level are shown. Add -v to see the name of each test.
    2. By hand: free.
           echo {"tool_name": "Read", "tool_input": {"file_path": "a.txt"}, "effort": {"level": "high"}, "agent_type": "Explore"} | python agent/effort_hook.py
               [effort] high   before Read (in subagent Explore): a.txt

IF SOMETHING GOES WRONG
    - "(not reported)" instead of a level: that Claude Code version doesn't put the effort into hook input.
      Update Claude Code (claude update).

FILES IT READS AND WRITES
    None.

SEE ALSO
    effort_probe.py (uses it both ways); Lesson 6, Steps 22 to 24.
"""

import json
import sys


def effort_line(hook_input: dict) -> str:
    level = (hook_input.get("effort") or {}).get("level", "(not reported)")
    tool_input = hook_input.get("tool_input") or {}
    detail = tool_input.get("skill") or tool_input.get("command") or tool_input.get("file_path") or ""
    # agent_type is only set when a subagent runs the tool, for example a skill with context: fork.
    where = f" (in subagent {hook_input['agent_type']})" if hook_input.get("agent_type") else ""
    return f"[effort] {level:6} before {hook_input['tool_name']}{where}: {str(detail)[:80]}"


if __name__ == "__main__":
    sys.stderr.reconfigure(encoding="utf-8")
    print(effort_line(json.load(sys.stdin)), file=sys.stderr)     # stderr: for you; stdout stays empty
