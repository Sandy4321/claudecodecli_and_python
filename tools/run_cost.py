"""Where do the tokens of one Claude Code run go? (Lesson 6, Part 6, Step 28)

WHAT
    Runs one prompt with the project's skills and prints:
      - each step, with the model that did it (thinks, Skill converting-units, PowerShell: python ...,
        writes the answer);
      - the tokens per model: the context Claude read again from the cache, the new context written
        to the cache, the output (with the thinking inside it), and a cost estimate;
      - the start of the answer.

WHY
    To see what a skill's `model:` and `effort:` lines change, and that most tokens of a short job are
    the context (Claude Code's instructions and the skill list), not the answer. If a step runs on
    another model, for example a skill with `model: haiku` started with /skill-name, the steps and
    the token lines show it.

TWO WAYS TO REACH CLAUDE, ONE PROGRAM
    Both ways make the same run (the same instructions, settings and allowed tools) and print the
    same report, so you can compare their numbers.
    1. claude -p (the default): runs, from the project folder,
           claude -p "<prompt>" --output-format stream-json --verbose
                  --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)" --no-session-persistence
       and reads one JSON line per step. Needs only the standard library.
    2. The Agent SDK (add --sdk): query() with ClaudeAgentOptions set to what claude -p does by
       default: system_prompt={"type": "preset", "preset": "claude_code"} (Claude Code's own
       instructions; without it the SDK sends none), setting_sources=["user", "project", "local"]
       (all settings files), and the same allowed tools. events_from_sdk() turns each SDK message
       into the JSON line claude -p would have printed, so one summarize() serves both ways.
    The steps are the "assistant" lines (messages); the tokens per model are in modelUsage of the
    final "result" line (ResultMessage.model_usage in the SDK).
    Expect the same steps, but not exactly the same token numbers: the SDK starts its own claude.exe
    from the pip package, which can be another Claude Code version than your claude command (2.1.301
    against 2.1.308 on the course machine), with slightly different built-in instructions; and a
    cold cache shows up as more "new context" and less "context re-read".

WHEN TO USE WHICH
    claude -p for a quick measurement: nothing to install. The SDK when the measurement is part of a
    bigger Python program, and you want the messages as objects.

HOW TO RUN  (in cmd, from the project folder, with the venv activated)
    python tools/run_cost.py "Convert 26.2 miles to kilometers." --model sonnet
    python tools/run_cost.py "Convert 26.2 miles to kilometers." --model sonnet --sdk
    python tools/run_cost.py "/converting-units 26.2 mi km" --model sonnet --effort low

OPTIONS
    PROMPT           the prompt, in quotes; a /skill-name prompt starts that skill directly
    --sdk            use the Agent SDK instead of claude -p
    --model NAME     the session model: haiku, sonnet, opus, or a full id; default: your Claude Code default
    --effort LEVEL   the session effort: low, medium, high, xhigh or max

OUTPUT  (a real run, Lesson 6, Step 28)
    Steps:
      1. claude-sonnet-5-5  thinks
      2. claude-sonnet-5-5  Skill converting-units
      3. claude-sonnet-5-5  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/converting-units/sc
      4. claude-sonnet-5-5  writes the answer
    Tokens per model:
      claude-sonnet-5-5: context re-read 110,413, new context 10,929, output 269 (thinking 31), cost≈$0.0575
    The cost is an API list-price estimate; on Pro nothing is charged. Uses a little Pro allowance.

NEEDS
    For the SDK way claude-agent-sdk (python -m pip install -r agent/requirements.txt).

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k run_cost
       Expected (2 tests; the time differs):
           ..
           ----------------------------------------------------------------------
           Ran 2 tests in 2.234s

           OK
       What they check: the steps with their models from JSON lines, the --model and --effort flags, and
       that the SDK options make the same run as claude -p. Add -v to see the name of each test.
    2. With Claude: uses a little Pro allowance.
           python tools/run_cost.py "Convert 26.2 miles to kilometers." --model sonnet
           python tools/run_cost.py "Convert 26.2 miles to kilometers." --model sonnet --sdk
           Expected, both ways: the 4 steps shown under OUTPUT (thinks, Skill converting-units, Bash: python ...,
           writes the answer), one token line, and an answer with 42.16 km. The token numbers differ between
           the ways (see above).

IF SOMETHING GOES WRONG
    - "The 'claude' command was not found": install Claude Code, or open a new cmd window so PATH is
      read again.
    - "The SDK way needs claude-agent-sdk": install it (python -m pip install -r agent/requirements.txt),
      or add --cli.
    - "Steps:" is empty: claude printed an error instead of steps. Run the claude -p command from
      TWO WAYS above by hand to see it (often: not logged in).

FILES IT READS AND WRITES
    None: both ways run without saving a session.

SEE ALSO
    agent/effort_probe.py (tokens per answer, with the effort level); Lesson 6, Step 28.
"""

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ALLOWED_TOOLS = "Skill,Read,Bash(python *),PowerShell(python *)"


def build_command(claude: str, prompt: str, model: str | None, effort: str | None) -> list[str]:
    cmd = [
        claude, "-p", prompt,
        "--output-format", "stream-json", "--verbose",    # one JSON line per step
        "--allowedTools", ALLOWED_TOOLS,
        "--no-session-persistence",
    ]
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
    return cmd


def describe(block: dict) -> str:
    """One step in a few words: the tool and its skill or command, thinking, or the answer."""
    kind = block.get("type")
    if kind != "tool_use":
        return {"thinking": "thinks", "text": "writes the answer"}.get(kind, kind)
    what = block.get("name")
    if what == "Skill":
        what += f" {block.get('input', {}).get('skill')}"
    elif "command" in block.get("input", {}):
        what += f": {block['input']['command'][:70]}"
    return what


def summarize(events: list[dict]) -> dict:
    """The steps (model: what it did) and the result event of one stream-json run."""
    steps, result = [], {}
    for event in events:
        if event.get("type") == "assistant":
            message = event.get("message", {})
            for block in message.get("content", []):
                steps.append((message.get("model", "?"), describe(block)))
        elif event.get("type") == "result":
            result = event
    return {"steps": steps, "result": result}


def events_from_cli(prompt: str, model: str | None, effort: str | None) -> list[dict]:
    """The claude -p way: run the command and read its JSON lines."""
    claude = shutil.which("claude")
    if not claude:
        raise SystemExit("The 'claude' command was not found.")
    proc = subprocess.run(build_command(claude, prompt, model, effort), cwd=PROJECT_ROOT,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    return [json.loads(line) for line in proc.stdout.splitlines() if line.startswith("{")]


def sdk_options(model: str | None, effort: str | None):
    """The SDK options for the same run as build_command()."""
    from claude_agent_sdk import ClaudeAgentOptions

    return ClaudeAgentOptions(
        cwd=str(PROJECT_ROOT),
        system_prompt={"type": "preset", "preset": "claude_code"},   # Claude Code's instructions, as with claude -p
        setting_sources=["user", "project", "local"],                # the settings files claude -p reads
        allowed_tools=ALLOWED_TOOLS.split(","),
        model=model,
        effort=effort,
        extra_args={"no-session-persistence": None},                 # any other claude flag, as a dictionary
    )


async def events_from_sdk(prompt: str, model: str | None, effort: str | None) -> list[dict]:
    """The SDK way: the same run, each message turned into the JSON line claude -p would print."""
    from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, ThinkingBlock, ToolUseBlock, query

    events = []
    async for message in query(prompt=prompt, options=sdk_options(model, effort)):
        if isinstance(message, AssistantMessage):
            content = []
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    content.append({"type": "tool_use", "name": block.name, "input": block.input})
                elif isinstance(block, ThinkingBlock):
                    content.append({"type": "thinking"})
                elif isinstance(block, TextBlock):
                    content.append({"type": "text"})
            events.append({"type": "assistant", "message": {"model": message.model, "content": content}})
        elif isinstance(message, ResultMessage):
            events.append({"type": "result", "result": message.result, "is_error": message.is_error,
                           "modelUsage": message.model_usage or {}})
    return events


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Show the steps and tokens of one Claude Code run.")
    parser.add_argument("prompt")
    parser.add_argument("--sdk", action="store_true", help="use the Agent SDK instead of claude -p")
    parser.add_argument("--model", help="session model, e.g. haiku or sonnet (default: your Claude Code default)")
    parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], help="session effort")
    args = parser.parse_args()

    if args.sdk:
        events = asyncio.run(events_from_sdk(args.prompt, args.model, args.effort))
    else:
        events = events_from_cli(args.prompt, args.model, args.effort)
    run = summarize(events)

    print(f"Prompt: {args.prompt}\n\nSteps:")
    for number, (model, what) in enumerate(run["steps"], start=1):
        print(f"  {number}. {model:18} {what}")
    print("\nTokens per model:")
    for model, usage in (run["result"].get("modelUsage") or {}).items():
        print(f"  {model}: context re-read {usage.get('cacheReadInputTokens', 0):,}, "
              f"new context {usage.get('cacheCreationInputTokens', 0):,}, "
              f"output {usage.get('outputTokens', 0):,} (thinking {usage.get('thinkingTokens', 0):,}), "
              f"cost≈${usage.get('costUSD', 0):.4f}")
    print(f"\nAnswer: {(run['result'].get('result') or '').strip()[:200]}")
    return 0 if run["result"] and not run["result"].get("is_error") else 1


if __name__ == "__main__":
    sys.exit(main())
