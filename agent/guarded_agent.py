"""An agent whose shell commands and file changes your Python rules allow or refuse (Lesson 6, Part 4, Step 15).

WHAT
    Runs the skills agent, but before every Bash, PowerShell, Write and Edit call, the rules in
    guard.py decide: ALLOW or DENY, with a reason. Each decision is printed as a [guard] line, and
    Claude reads the reason of a refusal and tries another way.

WHY
    allowed_tools and --allowedTools are fixed lists, written before Claude starts. Real programs often
    need rules with judgment and memory: "only skill scripts", "only files in data/", "at most 6
    commands per run". The rules are in guard.py, as plain Python, so the tests can check them.

TWO WAYS TO REACH CLAUDE, ONE PROGRAM
    Both ways use a PreToolUse hook: Claude Code asks it before each matching tool call, also before
    the python commands that a skill's allowed-tools would approve by itself. Both use the same Guard
    rules and print the same [guard] lines. The difference is where the hook lives:
    1. The Agent SDK (the default): check_tool() is a function inside this program.
       HookMatcher(matcher="Bash|PowerShell|Write|Edit") registers it. One Guard object lives for the
       whole run, in memory, so counting commands is just a number in Python.
    2. claude -p (add --cli): the hook is a separate program, agent/guard_hook.py. This program
       switches it on with --settings (JSON with the hook) and adds --include-hook-events, so the
       hook's [guard] lines come back as JSON lines. Claude Code starts the hook once per tool call,
       with the call as JSON on stdin; it shares no memory with this program, so the command count
       is kept in a temporary file (the environment variable GUARD_STATE names it).
    Why not can_use_tool (SDK) or --permission-prompt-tool (claude -p)? Claude Code asks them only
    about calls that no allow rule covers, and a skill's allowed-tools is such a rule, so the skill's
    commands would never reach them.

WHEN TO USE WHICH
    The SDK: rules that need your program's state (a database, the user who is logged in, earlier
    decisions); the hook is ordinary Python, and fast.
    claude -p: rules that stand alone. The same kind of hook script also works in .claude/settings.json
    for the interactive claude window (Lesson 9, Exercise 8).

HOW TO RUN  (in cmd, from the project folder, with the venv activated)
    python agent/guarded_agent.py --model haiku "Which region sold the most in data/sales.csv? Save the answer in report.txt."
    python agent/guarded_agent.py --cli --model haiku "Which region sold the most in data/sales.csv? Save the answer in report.txt."
    Afterwards delete the practice file report.txt from the data folder.

OPTIONS
    --cli            use claude -p with the hook script guard_hook.py instead of the Agent SDK
    --model NAME     haiku, sonnet, opus, or a full id; default: your Claude Code default

NEEDS
    For the SDK way claude-agent-sdk (python -m pip install -r agent/requirements.txt).
    Uses some Pro allowance.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k guard -k AgentGuard
       Expected (7 tests; the time differs):
           .......
           ----------------------------------------------------------------------
           Ran 7 tests in 1.122s

           OK
       What they check: the Guard rules (AgentGuard), the hook script guard_hook.py with its command
       counter, and that --cli switches that hook on for the four tools. Add -v to see the name of each
       test.
    2. With Claude: uses a little Pro allowance.
           python agent/guarded_agent.py --model haiku "Which region sold the most in data/sales.csv? Save the answer in report.txt."
           python agent/guarded_agent.py --cli --model haiku "Which region sold the most in data/sales.csv? Save the answer in report.txt."
           Expected, both ways: a [guard] DENY line for the Write of report.txt in the project folder, then a
           [guard] ALLOW line for data/report.txt, and an answer that says why the file went to data/. Delete
           data/report.txt afterwards.

IF SOMETHING GOES WRONG
    - "The 'claude' command was not found": install Claude Code, or open a new cmd window so PATH is
      read again.
    - "The SDK way needs claude-agent-sdk": install it (python -m pip install -r agent/requirements.txt),
      or add --cli.
    - With --cli there are no [guard] lines: the hook did not start. Try it by hand (HOW TO TEST in
      guard_hook.py), and check that the venv's python runs it.
    - "PreToolUse:Write hook error: ..." lines are normal: that is how Claude Code reports a DENY.

FILES IT READS AND WRITES
    Claude may write data/report.txt (the practice file). The --cli way keeps the command count in a
    temporary file, deleted after the run. Claude Code saves each run as a session in your user folder,
    in .claude/projects (both ways).

SEE ALSO
    guard.py (the rules); guard_hook.py (the --cli hook); tools/hooks/only_data_folder.py; Lesson 6,
    Step 15; Lesson 9, Exercise 8.
"""

import argparse
import asyncio
import os
import sys
import tempfile
from pathlib import Path

from guard import Guard
from run_agent import build_cli_command, build_options, find_claude, hook_settings, print_message, run_cli

HOOK_SCRIPT = Path(__file__).with_name("guard_hook.py")
GUARDED_TOOLS = "Bash|PowerShell|Write|Edit"


def build_guarded_options(model: str | None, guard: Guard):
    from claude_agent_sdk import HookMatcher

    async def check_tool(hook_input, tool_use_id, context):
        tool_name, tool_input = hook_input["tool_name"], hook_input["tool_input"]
        allowed, reason = guard.check(tool_name, tool_input)
        detail = tool_input.get("command") or tool_input.get("file_path") or ""
        print(f"[guard] {'ALLOW' if allowed else 'DENY '} {tool_name}: {detail}  ({reason})")
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow" if allowed else "deny",   # deny: the call doesn't run
                "permissionDecisionReason": reason,                      # Claude reads why
            }
        }

    options = build_options("all", model)
    options.hooks = {"PreToolUse": [HookMatcher(matcher=GUARDED_TOOLS, hooks=[check_tool])]}
    return options


async def run(prompt: str, model: str | None) -> None:
    from claude_agent_sdk import query

    async for message in query(prompt=prompt, options=build_guarded_options(model, Guard())):
        print_message(message)


def run_cli_way(prompt: str, model: str | None) -> dict:
    """The --cli way: the same rules, as the hook script guard_hook.py that Claude Code starts."""
    with tempfile.TemporaryDirectory() as folder:
        env = {**os.environ, "GUARD_STATE": str(Path(folder) / "guard_state.txt")}   # a new count per run
        settings = hook_settings(HOOK_SCRIPT, matcher=GUARDED_TOOLS)
        return run_cli(build_cli_command(find_claude(), prompt, "all", model, settings=settings), env=env)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    parser = argparse.ArgumentParser(description="Run an agent whose tool calls your Python rules approve.")
    parser.add_argument("prompt")
    parser.add_argument("--cli", action="store_true", help="use claude -p and the hook script guard_hook.py")
    parser.add_argument("--model", help="model alias or id, e.g. haiku (default: your Claude Code default)")
    args = parser.parse_args()
    if args.cli:
        result = run_cli_way(args.prompt, args.model)
        return 0 if result and not result.get("is_error") else 1
    try:
        asyncio.run(run(args.prompt, args.model))
    except ImportError:
        print("The SDK way needs claude-agent-sdk: python -m pip install -r agent/requirements.txt (or add --cli)")
        return 1
    except Exception as error:
        print(f"Agent stopped with an error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
