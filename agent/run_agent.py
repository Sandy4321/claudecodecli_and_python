"""Your own agent program that uses the project's skills, and shows every step (Lesson 6, Part 1).

WHAT
    Asks Claude one question with all 9 skills of this project available, and prints each step as
    it happens: the login and model ([init]), the skill Claude chose ([skill]), each command or file
    it used ([tool]), refused tool calls ([refused]), Claude's text ([claude]), and the end with the
    number of turns and a cost estimate ([done]).

WHY
    To see that your own Python program gets the same skill choice and the same script runs as the
    interactive claude window, and receives every step as data it can use. The other agent programs
    reuse its functions.

TWO WAYS TO REACH CLAUDE, ONE PROGRAM
    Both ways run the same agent and print the same labelled steps.
    1. The Agent SDK (the default). build_options() sets ClaudeAgentOptions: cwd = the project folder
       (where .claude/skills is), setting_sources=["project"], skills, allowed_tools (Skill, Read,
       and python commands with Bash or PowerShell, because nobody can answer permission questions
       in a program), max_turns=15, model and effort. query() starts claude.exe and yields each step
       as a Python object; print_message() prints it.
    2. claude -p (add --cli). build_cli_command() writes the same settings as command-line flags:
           claude -p "<question>" --output-format stream-json --verbose --system-prompt ""
                  --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)" --max-turns 15
                  --setting-sources project [--model ...] [--effort ...]
       These are the flags the SDK itself passes to claude.exe (tools/show_sdk_command.py prints
       them). run_cli() runs the command with subprocess, reads one JSON line per step, and
       print_event() prints it. Needs only the standard library: no SDK.
    The one difference is --skills. The SDK tells claude.exe in its start-up message to offer only
    the listed skills, and claude -p has no flag for that. With --cli, Claude still sees all skills,
    only the listed ones are pre-approved (Skill(name) rules), and Claude Code refuses the others.

WHEN TO USE WHICH
    The SDK: when your program is Python and wants the steps as objects, or needs conversations,
    hooks or tools written in Python (see chat_agent.py, guarded_agent.py, custom_tools_agent.py).
    claude -p: when you want no extra package, or run from a .bat file, a scheduler or another
    language, where each step as a JSON line is enough (Lesson 6, Part 4).

HOW TO RUN  (in cmd, from the project folder, with the venv activated)
    python -m pip install -r agent/requirements.txt          (once: installs claude-agent-sdk)
    python agent/run_agent.py --model haiku "Which region sold the most in data/sales.csv?"
    python agent/run_agent.py --cli --model haiku "Which region sold the most in data/sales.csv?"
    python agent/run_agent.py --skills converting-units,calculating-dates "How many km is a marathon?"
    python agent/run_agent.py --model opus --effort low "Convert 26.2 miles to kilometers."

OPTIONS
    --cli            use claude -p instead of the Agent SDK
    --skills LIST    "all" (the default) or comma-separated skill names that Claude is offered
    --model NAME     haiku, sonnet, opus, or a full id; default: your Claude Code default
    --effort LEVEL   low, medium, high, xhigh or max; default: the model's default

NEEDS
    The activated venv (the Excel and chart skills need its packages), and for the SDK way
    claude-agent-sdk. Each run uses some of your Pro allowance; the [done] line shows its size as
    an API-price estimate.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k run_agent -k need_no_sdk
       Expected (4 tests; the time differs):
           ....
           ----------------------------------------------------------------------
           Ran 4 tests in 0.489s

           OK
       What they check: the claude -p command has the flags the SDK passes, the skill list, --resume and
       hook settings, the steps printed from a fake claude, and that the --cli way works with every SDK
       import blocked. Add -v to see the name of each test.
    2. By hand: free.
           python tools/show_sdk_command.py
               (free: the command the SDK way starts; compare it with build_cli_command() in this file)
    3. With Claude: uses a little Pro allowance.
           python agent/run_agent.py --model haiku "Build a pivot of amount by region and product from data/sales.xlsx."
           python agent/run_agent.py --cli --model haiku "Build a pivot of amount by region and product from data/sales.xlsx."
               Expected, both ways (real runs, about 18 seconds each):
                   [skill] Claude picked: analyzing-excel
                   [tool]  Bash: python ".../analyzing-excel/scripts/excel_tool.py" sheets data/sales.xlsx
                   [tool]  Bash: python ".../analyzing-excel/scripts/excel_tool.py" pivot data/sales.xlsx --sheet Sales ...
                   [claude] ...a table with the Total 4630...
                   [done] success, turns=5, ...
               A very simple question ("Convert 1 mile to km.") is often answered without any skill: Haiku knows it.

IF SOMETHING GOES WRONG
    - "The 'claude' command was not found": install Claude Code, or open a new cmd window so PATH is
      read again.
    - "The SDK way needs claude-agent-sdk": install it (python -m pip install -r agent/requirements.txt),
      or add --cli.
    - [init] auth shows something other than "claude.ai subscription": the environment variable
      ANTHROPIC_API_KEY is set, and that API account pays. Remove it to use your Pro plan.
    - Claude answered without [skill]: that is Claude's choice, the same in both ways (Lesson 6,
      Step 11). The Excel question of Step 11 usually needs it: an .xlsx file can't be read as text.
    - "Agent stopped with an error: ... max turns": raise max_turns in build_options() (15).

FILES IT READS AND WRITES
    Reads the skills in .claude/skills. Claude Code saves each run as a session in your user folder, in
    .claude/projects (both ways).

SEE ALSO
    chat_agent.py, guarded_agent.py, effort_probe.py (they reuse its functions);
    tools/show_sdk_command.py; Lesson 6, Steps 4 to 6 and 11.
"""

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def describe_auth(api_key_source: str | None) -> str:
    """'none' means no API key: Claude Code uses your claude.ai login (Pro/Max subscription)."""
    if api_key_source in (None, "none"):
        return "claude.ai subscription (Pro/Max usage, no API billing)"
    return f"{api_key_source} - billed per token to that API account! Unset it to use your subscription."


# ---------------------------------------------------------------- the Agent SDK way

def build_options(skills: str | list[str], model: str | None = None, effort: str | None = None) -> "ClaudeAgentOptions":
    from claude_agent_sdk import ClaudeAgentOptions     # imported here, so the --cli way needs no SDK

    return ClaudeAgentOptions(
        cwd=str(PROJECT_ROOT),          # skills are found in <cwd>/.claude/skills
        setting_sources=["project"],    # load only this project's skills/settings, not ~/.claude
        skills=skills,                  # "all", or a list of names Claude may invoke
        allowed_tools=[                 # pre-approved, so no permission prompts in a script
            "Skill",
            "Read",
            "Bash(python *)",
            "PowerShell(python *)",
        ],
        max_turns=15,
        model=model,                    # None = your Claude Code default; "haiku" uses less of your plan
        effort=effort,                  # None = the model's default; "low" thinks less, "high" more
    )


def print_message(message, show_init: bool = True) -> None:
    """Print one step of Claude's work with a label. chat_agent.py and guarded_agent.py reuse it."""
    from claude_agent_sdk import (AssistantMessage, ResultMessage, SystemMessage, TextBlock, ToolResultBlock,
                                  ToolUseBlock, UserMessage)

    if isinstance(message, SystemMessage) and message.subtype == "init":
        if show_init:
            print(f"[init] auth: {describe_auth(message.data.get('apiKeySource'))}")
            print(f"[init] model: {message.data.get('model')}")
            print(f"[init] skills discovered: {message.data.get('skills')}\n")
    elif isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, ToolUseBlock) and block.name == "Skill":
                print(f"[skill] Claude picked: {block.input.get('skill')}")
            elif isinstance(block, ToolUseBlock):
                detail = block.input.get("command") or block.input.get("file_path") or block.input
                print(f"[tool]  {block.name}: {detail}")
            elif isinstance(block, TextBlock) and block.text.strip():
                print(f"[claude] {block.text.strip()}")
    elif isinstance(message, UserMessage) and isinstance(message.content, list):
        # Tool results come back as user messages; show failures such as a skill
        # that is not in the allowlist, or a denied command.
        for block in message.content:
            if isinstance(block, ToolResultBlock) and block.is_error:
                text = block.content if isinstance(block.content, str) else str(block.content)
                print(f"[refused] {text.strip()[:200]}")
    elif isinstance(message, ResultMessage):
        # total_cost_usd is computed locally at API list price. On a Pro/Max
        # subscription nothing is charged; read it as relative usage.
        cost = f"cost≈${message.total_cost_usd:.4f} (API list-price estimate)" if message.total_cost_usd is not None else "cost n/a"
        print(f"\n[done] {message.subtype}, turns={message.num_turns}, {cost}")


async def run(prompt: str, skills: str | list[str], model: str | None = None, effort: str | None = None) -> None:
    from claude_agent_sdk import query

    async for message in query(prompt=prompt, options=build_options(skills, model, effort)):
        print_message(message)


# ---------------------------------------------------------------- the claude -p way (--cli)

def find_claude() -> str:
    claude = shutil.which("claude")
    if not claude:
        raise SystemExit("The 'claude' command was not found. Install Claude Code and log in once.")
    return claude


def build_cli_command(claude: str, prompt: str, skills: str | list[str] = "all", model: str | None = None,
                      effort: str | None = None, resume: str | None = None, settings: str | None = None) -> list[str]:
    """The agent of build_options() as one `claude -p` command, with the flags the SDK passes to claude.exe."""
    # The SDK offers only the listed skills (it says so in its start-up message); claude -p has no flag
    # for that, so here the listed skills are pre-approved one by one, and Claude Code refuses the others.
    skill_rules = ["Skill"] if skills == "all" else [f"Skill({name})" for name in skills]
    cmd = [
        claude, "-p", prompt,
        "--output-format", "stream-json", "--verbose",   # one JSON line per step: the SDK's messages, as text
        "--system-prompt", "",                           # like the SDK: no Claude Code coding instructions
        "--allowedTools", ",".join(skill_rules + ["Read", "Bash(python *)", "PowerShell(python *)"]),
        "--max-turns", "15",
        "--setting-sources", "project",                  # setting_sources=["project"]
    ]
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
    if resume:
        cmd += ["--resume", resume]                      # continue a saved conversation (chat_agent.py)
    if settings:
        cmd += ["--settings", settings,                  # extra settings as JSON, for example hooks
                "--include-hook-events"]                 # and the hooks' output as JSON lines too
    return cmd


def hook_settings(script: Path, matcher: str | None = None) -> str:
    """Settings JSON for --settings: run `python <script>` before each tool call (a PreToolUse hook)."""
    command = f'"{Path(sys.executable).as_posix()}" "{script.as_posix()}"'     # the venv's python
    entry = {"hooks": [{"type": "command", "command": command}]}
    if matcher:
        entry["matcher"] = matcher                       # only before these tools; without it: every tool
    return json.dumps({"hooks": {"PreToolUse": [entry]}})


def print_event(event: dict, show_init: bool = True) -> None:
    """print_message() for the --cli way: the same labels, from one JSON line that claude -p printed."""
    kind = event.get("type")
    if kind == "system" and event.get("subtype") == "init":
        if show_init:
            print(f"[init] auth: {describe_auth(event.get('apiKeySource'))}")
            print(f"[init] model: {event.get('model')}")
            print(f"[init] skills discovered: {event.get('skills')}\n")
    elif kind == "system" and event.get("subtype") == "hook_response":
        # What a hook script wrote to stderr: guard_hook.py and effort_hook.py write their line there.
        for line in (event.get("stderr") or "").splitlines():
            if line.strip():
                print(line.rstrip())
    elif kind == "assistant":
        for block in event["message"]["content"]:
            if block["type"] == "tool_use" and block["name"] == "Skill":
                print(f"[skill] Claude picked: {block['input'].get('skill')}")
            elif block["type"] == "tool_use":
                detail = block["input"].get("command") or block["input"].get("file_path") or block["input"]
                print(f"[tool]  {block['name']}: {detail}")
            elif block["type"] == "text" and block["text"].strip():
                print(f"[claude] {block['text'].strip()}")
    elif kind == "user" and isinstance(event["message"].get("content"), list):
        for block in event["message"]["content"]:
            if block.get("type") == "tool_result" and block.get("is_error"):
                content = block.get("content")
                text = content if isinstance(content, str) else str(content)
                print(f"[refused] {text.strip()[:200]}")
    elif kind == "result":
        cost = event.get("total_cost_usd")
        cost = f"cost≈${cost:.4f} (API list-price estimate)" if cost is not None else "cost n/a"
        print(f"\n[done] {event.get('subtype')}, turns={event.get('num_turns')}, {cost}")


def run_cli(cmd: list[str], show_init: bool = True, env: dict | None = None) -> dict:
    """Run one claude -p command from the project folder; print each JSON line as it arrives.
    Returns the last line, the "result" (answer, session_id, usage)."""
    result = {}
    with subprocess.Popen(cmd, cwd=PROJECT_ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          text=True, encoding="utf-8", errors="replace", env=env) as proc:   # closes the pipe at the end
        for line in proc.stdout:
            if line.startswith("{"):
                event = json.loads(line)
                print_event(event, show_init)
                if event.get("type") == "result":
                    result = event
    return result


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Claude's answers often contain non-ASCII text
    except AttributeError:
        pass
    parser = argparse.ArgumentParser(description="Run an agent that uses this project's skills.")
    parser.add_argument("prompt")
    parser.add_argument("--cli", action="store_true", help="use claude -p instead of the Agent SDK")
    parser.add_argument("--skills", default="all", help='"all" or comma-separated skill names')
    parser.add_argument("--model", help="model alias or id, e.g. haiku, sonnet, opus (default: your Claude Code default)")
    parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"],
                        help="reasoning effort (default: the model's default)")
    args = parser.parse_args()
    skills = "all" if args.skills == "all" else [s.strip() for s in args.skills.split(",") if s.strip()]
    if args.cli:
        result = run_cli(build_cli_command(find_claude(), args.prompt, skills, args.model, args.effort))
        return 0 if result and not result.get("is_error") else 1
    try:
        asyncio.run(run(args.prompt, skills, args.model, args.effort))
    except ImportError:
        print("The SDK way needs claude-agent-sdk: python -m pip install -r agent/requirements.txt (or add --cli)")
        return 1
    except Exception as error:  # query() raises after an error result (e.g. max turns)
        print(f"Agent stopped with an error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
