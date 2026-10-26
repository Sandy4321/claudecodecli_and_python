"""Your own Python functions as tools that Claude calls directly: no skills, no shell (Lesson 6, Part 2).

WHAT
    Gives Claude three Python functions as tools: convert_units, weekday and add_business_days. They are
    the same functions the converting-units and calculating-dates skills run. The program prints each
    tool call with the values Claude chose ([tool] mcp__tutor__weekday({'date': '2026-12-25'})), and
    then the answer.

WHY
    A second way to connect Claude to your Python. A skill makes Claude run a command and read printed
    text; a tool lets Claude call your function directly, with checked parameter types. Use tools for
    single exact actions, and skills for jobs with several steps and know-how (Lesson 6, Step 8).

TWO WAYS TO REACH CLAUDE, ONE PROGRAM
    Tools come from a "tool server" that speaks MCP (the standard way to give Claude extra tools).
    Claude Code names its tools mcp__tutor__<name>. Both ways allow only those tools, remove the
    built-in tools (Read, Bash, ...) and load no skills, so Claude can use only your functions.
    1. The Agent SDK (the default): sdk_tool_server() turns each async function into a tool with
       @tool(name, description, parameters), and create_sdk_mcp_server() collects them. The server
       runs inside this Python program; the SDK passes the calls through to it.
       Options: mcp_servers={"tutor": ...}, allowed_tools=["mcp__tutor__*"], tools=[], setting_sources=[].
    2. claude -p (add --cli): claude -p can't reach functions inside this program, so the tools are
       served by a separate program, agent/tutor_mcp_server.py, which Claude Code starts itself:
           claude -p "<question>" --output-format stream-json --verbose
                  --mcp-config '{"mcpServers": {"tutor": {"command": "<python>", "args": ["agent/tutor_mcp_server.py"]}}}'
                  --strict-mcp-config --allowedTools "mcp__tutor__*" --tools "" --setting-sources "" ...
       Needs only the standard library: the server is plain Python, with no SDK and no mcp package.

WHEN TO USE WHICH
    The SDK: the tools can use your program's data and objects directly, and need no second program.
    claude -p: the tool server is a stand-alone program, so the interactive claude window, Claude
    Desktop or any other MCP client can use the same tools (add it to .mcp.json or with `claude mcp add`).

HOW TO RUN  (in cmd, from the project folder, with the venv activated)
    python agent/custom_tools_agent.py "How many km is 26.2 miles, and what weekday is 2026-12-25?"
    python agent/custom_tools_agent.py --cli "How many km is 26.2 miles, and what weekday is 2026-12-25?"
    python agent/custom_tools_agent.py          (asks that same demo question)

OPTIONS
    QUESTION         the words of the question (default: the demo question above)
    --cli            use claude -p with the tool server tutor_mcp_server.py instead of the Agent SDK

NEEDS
    For the SDK way claude-agent-sdk (python -m pip install -r agent/requirements.txt).
    Uses some Pro allowance.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k custom_tools_agent -k tutor_mcp_server
       Expected (2 tests; the time differs):
           ..
           ----------------------------------------------------------------------
           Ran 2 tests in 0.401s

           OK
       What they check: that --cli starts tutor_mcp_server.py with only its tools allowed and no built-
       in tools, and that the server answers MCP messages. Add -v to see the name of each test.
    2. With Claude: uses a little Pro allowance.
           python agent/custom_tools_agent.py
           python agent/custom_tools_agent.py --cli
               Expected, both ways (the demo question; real runs, about 8 seconds each):
                   [init] auth: claude.ai subscription
                   [tool] mcp__tutor__convert_units({'value': 26.2, 'from_unit': 'mi', 'to_unit': 'km'})
                   [tool] mcp__tutor__weekday({'date': '2026-12-25'})
                   - 26.2 miles is about 42.16 km ...
                   - 2026-12-25 is a Friday, in ISO week 52.
               ('mile' instead of 'mi' is fine too.) A very simple question ("How many km is 1 mile?") is often
               answered without any tool: Haiku knows it.

IF SOMETHING GOES WRONG
    - "The SDK way needs claude-agent-sdk": install it (python -m pip install -r agent/requirements.txt),
      or add --cli.
    - With --cli Claude says it has no tools: the server did not start. Try it by hand (HOW TO TEST in
      tutor_mcp_server.py).

FILES IT READS AND WRITES
    Claude Code saves each run as a session in your user folder, in .claude/projects (both ways).

SEE ALSO
    tutor_mcp_server.py; the skill scripts convert.py and dates.py (the same functions); Lesson 6, Steps
    7 and 8.
"""

import argparse
import asyncio
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILLS_DIR = Path(__file__).resolve().parent.parent / ".claude" / "skills"
SERVER_SCRIPT = Path(__file__).with_name("tutor_mcp_server.py")
DEMO_QUESTION = "How many km is 26.2 miles, and what weekday is 2026-12-25?"


def load_module(skill: str, filename: str):
    """Import a script from a skill folder (folder names have hyphens, so no normal import)."""
    scripts_dir = SKILLS_DIR / skill / "scripts"
    sys.path.insert(0, str(scripts_dir))  # lets dates.py find its sibling fncli.py
    spec = importlib.util.spec_from_file_location(filename.removesuffix(".py"), scripts_dir / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


convert_module = load_module("converting-units", "convert.py")
dates_module = load_module("calculating-dates", "dates.py")


def as_result(data: dict) -> dict[str, Any]:
    result = {"content": [{"type": "text", "text": json.dumps(data, default=str)}]}
    if "error" in data:
        result["is_error"] = True
    return result


# ---------------------------------------------------------------- the Agent SDK way

def sdk_tool_server():
    """The three tools as an in-process MCP server: they run inside this Python program."""
    from claude_agent_sdk import create_sdk_mcp_server, tool     # imported here, so --cli needs no SDK

    @tool(
        "convert_units",
        "Convert a number between units of length, mass, volume, speed, temperature or data size.",
        {"value": float, "from_unit": str, "to_unit": str},
    )
    async def convert_units(args: dict[str, Any]) -> dict[str, Any]:
        return as_result(convert_module.convert(args["value"], args["from_unit"], args["to_unit"]))

    @tool(
        "weekday",
        "Day of the week and ISO week number for an ISO date (YYYY-MM-DD).",
        {"date": str},
    )
    async def weekday(args: dict[str, Any]) -> dict[str, Any]:
        try:
            return as_result(dates_module.weekday(args["date"]))
        except ValueError as error:
            return as_result({"error": str(error)})

    @tool(
        "add_business_days",
        "Add Mon-Fri business days to an ISO date, optionally skipping comma-separated holiday dates.",
        {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Start date, YYYY-MM-DD"},
                "days": {"type": "integer", "minimum": 0},
                "holidays": {"type": "string", "description": "Comma-separated YYYY-MM-DD dates"},
            },
            "required": ["date", "days"],
        },
    )
    async def add_business_days(args: dict[str, Any]) -> dict[str, Any]:
        try:
            return as_result(dates_module.add_business_days(args["date"], args["days"], args.get("holidays", "")))
        except ValueError as error:
            return as_result({"error": str(error)})

    return create_sdk_mcp_server(name="tutor", version="1.0.0", tools=[convert_units, weekday, add_business_days])


async def run(prompt: str) -> None:
    from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, SystemMessage, ToolUseBlock, query

    options = ClaudeAgentOptions(
        mcp_servers={"tutor": sdk_tool_server()},
        allowed_tools=["mcp__tutor__*"],   # tool names are mcp__<server>__<tool>
        tools=[],                          # no built-in tools: Claude can only use ours
        setting_sources=[],                # ignore skills and settings on disk for this demo
        max_turns=8,
    )
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, SystemMessage) and message.subtype == "init":
            source = message.data.get("apiKeySource")
            print("[init] auth:", "claude.ai subscription" if source in (None, "none") else f"{source} (API billing!)")
        elif isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[tool] {block.name}({block.input})")
        elif isinstance(message, ResultMessage) and message.subtype == "success":
            print(f"\n{message.result}")


# ---------------------------------------------------------------- the claude -p way (--cli)

def build_cli_command(claude: str, prompt: str) -> list[str]:
    """The same run as the SDK way, as one claude -p command; the tools come from tutor_mcp_server.py."""
    server = {"command": sys.executable, "args": [str(SERVER_SCRIPT)]}   # Claude Code starts this program
    return [
        claude, "-p", prompt,
        "--output-format", "stream-json", "--verbose",                   # one JSON line per step
        "--mcp-config", json.dumps({"mcpServers": {"tutor": server}}),   # mcp_servers={"tutor": ...}
        "--strict-mcp-config",                # no MCP servers from settings files
        "--allowedTools", "mcp__tutor__*",    # allowed_tools=["mcp__tutor__*"]
        "--tools", "",                        # tools=[]: no built-in tools
        "--setting-sources", "",              # setting_sources=[]: no skills, no settings files
        "--system-prompt", "",                # what the SDK sends by default
        "--max-turns", "8",
    ]


def run_cli_way(prompt: str) -> int:
    claude = shutil.which("claude")
    if not claude:
        print("The 'claude' command was not found. Install Claude Code and log in once.")
        return 1
    ok = False
    with subprocess.Popen(build_cli_command(claude, prompt), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          text=True, encoding="utf-8", errors="replace") as proc:     # closes the pipe at the end
        for line in proc.stdout:
            if not line.startswith("{"):
                continue
            event = json.loads(line)
            if event.get("type") == "system" and event.get("subtype") == "init":
                source = event.get("apiKeySource")
                print("[init] auth:", "claude.ai subscription" if source in (None, "none") else f"{source} (API billing!)")
            elif event.get("type") == "assistant":
                for block in event["message"]["content"]:
                    if block["type"] == "tool_use":
                        print(f"[tool] {block['name']}({block['input']})")
            elif event.get("type") == "result" and event.get("subtype") == "success":
                ok = not event.get("is_error")
                print(f"\n{event.get('result')}")
    return 0 if ok else 1


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    parser = argparse.ArgumentParser(description="Give Claude your own Python functions as tools.")
    parser.add_argument("question", nargs="*", help="the question (default: a demo question)")
    parser.add_argument("--cli", action="store_true", help="use claude -p and the tool server tutor_mcp_server.py")
    args = parser.parse_args()
    prompt = " ".join(args.question) or DEMO_QUESTION
    if args.cli:
        return run_cli_way(prompt)
    try:
        asyncio.run(run(prompt))
    except ImportError:
        print("The SDK way needs claude-agent-sdk: python -m pip install -r agent/requirements.txt (or add --cli)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
