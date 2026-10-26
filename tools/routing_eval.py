"""Live routing test: does Claude pick the expected skill for each test question? (Lesson 5, Test 4)

WHAT
    Sends each question of tools/routing_cases.json (20 questions) to Claude, one at a time, and
    checks which skill Claude chooses, or that it chooses none. It prints PASS or FAIL per question,
    the total, and saves the details in tools/routing_report.json.

WHY
    The only test that shows what Claude really chooses. Run it after you change a description, add a
    skill, or change the model. The linter and the preview only guess.

HOW IT WORKS
    Each question runs in a new, separate Claude Code session, from the project folder, with only
    the project's settings (your personal skills in ~/.claude stay out of the test). The program
    reads the steps as they come, and stops Claude as soon as Claude calls the Skill tool (that is
    the choice), gives an answer, or used 3 other tools first. read_event() holds these rules, and
    both ways use it.

TWO WAYS TO REACH CLAUDE, ONE PROGRAM
    1. claude -p (the default): for each question it runs
           claude -p "<question>" --output-format stream-json --verbose --setting-sources project --no-session-persistence
       and reads one JSON line per step; stopping Claude means ending the process. Needs only the
       standard library.
    2. The Agent SDK (add --sdk): for each question a ClaudeSDKClient with setting_sources=["project"]
       and system_prompt={"type": "preset", "preset": "claude_code"} (Claude Code's own instructions,
       as claude -p uses them; without it the SDK sends none, and the choice could differ). Each
       message is turned into the JSON line claude -p would print, and read by the same read_event().
       Leaving the `async with` block stops claude.exe as soon as the choice is made.

WHEN TO USE WHICH
    Both give the same verdicts. claude -p needs nothing installed and is the default. The SDK way
    fits when the test is part of a bigger Python test suite, and shows the same test written with
    message objects.

HOW TO RUN  (in cmd, from the project folder, with the venv activated)
    python tools/routing_eval.py --dry-run               (prints the 20 commands, spends nothing)
    python tools/routing_eval.py --limit 4 --model haiku (the first 4 questions, on the cheapest model)
    python tools/routing_eval.py --limit 4 --model haiku --sdk   (the same, through the Agent SDK)
    python tools/routing_eval.py                         (all questions, on your default model)
    python tools/routing_eval.py --cases my_cases.json   (your own questions)

OPTIONS
    --cases FILE     the questions (default: tools/routing_cases.json)
    --limit N        only the first N questions
    --model NAME     haiku, sonnet, opus, or a full id; default: your Claude Code default
    --sdk            use the Agent SDK instead of claude -p
    --dry-run        print the claude commands instead of running them

THE QUESTIONS FILE  (a JSON list)
    {"prompt": "...", "expect": "skill-name"}     Claude must choose this skill
    {"prompt": "...", "expect": null}             Claude must not use any skill
    {"prompt": "...", "expect": ["a", null]}      any of these outcomes is fine

OUTPUT AND EXIT CODE
    Auth: claude.ai subscription (uses your Pro/Max allowance, no API billing)
    Model: claude-opus-5-5
    PASS  Which region sold the most in data/sales.csv?    got=analyzing-csv     want=analyzing-csv
    ...
    6/6 routed as expected in 32s.
    Exit code 0 if all passed, 1 if any failed, 2 if the claude command was not found.
    Each question uses a little of your Pro allowance.

NEEDS
    For the SDK way claude-agent-sdk (python -m pip install -r agent/requirements.txt).

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k routing_eval
       Expected (2 tests; the time differs):
           ..
           ----------------------------------------------------------------------
           Ran 2 tests in 0.384s

           OK
       What they check: the stop rules shared by both ways (Skill chosen, 3 other tools, an error), and
       that --dry-run prints one command per question. Add -v to see the name of each test.
    2. By hand: free.
           python tools/routing_eval.py --dry-run --limit 2
               .../claude.EXE -p "Convert 26.2 miles to kilometers." --output-format stream-json --verbose --setting-sources project --no-session-persistence
               .../claude.EXE -p "How many pounds is 70 kg?" --output-format stream-json --verbose --setting-sources project --no-session-persistence
    3. With Claude: uses a little Pro allowance.
           python tools/routing_eval.py --limit 3 --model haiku
           python tools/routing_eval.py --limit 3 --model haiku --sdk
           Expected: PASS lines for the conversion questions. In real runs Haiku once failed "How many bytes are
           in 3 GiB?" (it answered without the skill); run a close question several times.

IF SOMETHING GOES WRONG
    - FAIL: Lesson 5, "What to do when a routing question fails", shows a real example and the fix.
    - Exit code 2 and "Cannot find the 'claude' command on PATH": install Claude Code.

FILES IT READS AND WRITES
    Reads tools/routing_cases.json (or --cases). Writes tools/routing_report.json (ignored by git).

SEE ALSO
    tools/routing_cases.json; tools/route_preview.py (the free guess); Lesson 5, Test 4.
"""

import argparse
import asyncio
import json
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASES_FILE = Path(__file__).resolve().parent / "routing_cases.json"
# Claude rarely needs more than one tool call to decide; stop after a few
# non-Skill tool calls so a mis-routed case can't run a long agent loop.
MAX_OTHER_TOOL_CALLS = 3
TIMEOUT_SECONDS = 180


def build_command(claude: str, prompt: str, model: str | None) -> list[str]:
    cmd = [
        claude, "-p", prompt,
        "--output-format", "stream-json", "--verbose",
        # Only project settings: your personal ~/.claude skills and plugins stay out of the test.
        "--setting-sources", "project",
        "--no-session-persistence",
    ]
    if model:
        cmd += ["--model", model]
    return cmd


def read_event(outcome: dict, event: dict) -> bool:
    """Update the outcome with one step (a JSON line of claude -p). True when the choice is made."""
    if event.get("type") == "system" and event.get("subtype") == "init":
        outcome["skills_loaded"] = event.get("skills")
        outcome["auth"] = event.get("apiKeySource")
        outcome["model"] = event.get("model")
    elif event.get("type") == "assistant":
        for block in event.get("message", {}).get("content", []):
            if block.get("type") != "tool_use":
                continue
            if block.get("name") == "Skill":
                tool_input = block.get("input", {})
                outcome["skill"] = tool_input.get("skill") or tool_input.get("name") or tool_input.get("command")
                return True
            outcome["other_tools"].append(block.get("name"))
        return len(outcome["other_tools"]) >= MAX_OTHER_TOOL_CALLS
    elif event.get("type") == "result":
        if event.get("is_error"):
            outcome["error"] = str(event.get("result") or event.get("subtype"))[:200]
        return True
    return False


def new_outcome() -> dict:
    return {"skill": None, "other_tools": [], "skills_loaded": None, "error": None}


def run_case(cmd: list[str]) -> dict:
    """The claude -p way: run one prompt; return {"skill": name|None, "other_tools": [...], "skills_loaded": [...]}."""
    outcome = new_outcome()
    proc = subprocess.Popen(
        cmd, cwd=PROJECT_ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
    )
    timer = threading.Timer(TIMEOUT_SECONDS, proc.kill)
    timer.start()
    try:
        for line in proc.stdout:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if read_event(outcome, event):
                return outcome
        stderr = proc.stderr.read().strip()
        if stderr:
            outcome["error"] = stderr[:300]
        return outcome
    finally:
        timer.cancel()
        if proc.poll() is None:
            proc.kill()
        proc.wait()


async def run_case_sdk(prompt: str, model: str | None) -> dict:
    """The SDK way: the same run and the same rules, on the SDK's message objects."""
    from claude_agent_sdk import (AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, ResultMessage,
                                  SystemMessage, ToolUseBlock)

    options = ClaudeAgentOptions(
        cwd=str(PROJECT_ROOT),
        setting_sources=["project"],                                 # --setting-sources project
        system_prompt={"type": "preset", "preset": "claude_code"},   # Claude Code's instructions, as with claude -p
        model=model,
        extra_args={"no-session-persistence": None},                 # --no-session-persistence
    )
    outcome = new_outcome()
    async with ClaudeSDKClient(options=options) as client:          # leaving the block stops claude.exe
        await client.query(prompt)
        async for message in client.receive_messages():
            if isinstance(message, SystemMessage):
                event = {"type": "system", "subtype": message.subtype, **message.data}
            elif isinstance(message, AssistantMessage):
                event = {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "name": b.name, "input": b.input}
                    for b in message.content if isinstance(b, ToolUseBlock)]}}
            elif isinstance(message, ResultMessage):
                event = {"type": "result", "is_error": message.is_error, "result": message.result,
                         "subtype": message.subtype}
            else:
                continue
            if read_event(outcome, event):
                break
    return outcome


def run_case_sdk_with_timeout(prompt: str, model: str | None) -> dict:
    try:
        return asyncio.run(asyncio.wait_for(run_case_sdk(prompt, model), TIMEOUT_SECONDS))
    except Exception as error:      # a timeout, or claude-agent-sdk is not installed
        return {**new_outcome(), "error": f"{type(error).__name__}: {error}"[:300]}


def accepted(expect) -> list:
    return expect if isinstance(expect, list) else [expect]


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cases", default=str(CASES_FILE))
    parser.add_argument("--limit", type=int, help="run only the first N cases")
    parser.add_argument("--model", help="model alias or id, e.g. haiku, sonnet, opus")
    parser.add_argument("--sdk", action="store_true", help="use the Agent SDK instead of claude -p")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))[: args.limit]
    claude = shutil.which("claude")
    if not claude and not args.dry_run and not args.sdk:
        print("Cannot find the 'claude' command on PATH. Install Claude Code first.")
        return 2

    passed, rows, started = 0, [], time.time()
    for number, case in enumerate(cases, 1):
        cmd = build_command(claude or "claude", case["prompt"], args.model)
        if args.dry_run:
            print(" ".join(f'"{c}"' if " " in c else c for c in cmd))
            continue
        outcome = run_case_sdk_with_timeout(case["prompt"], args.model) if args.sdk else run_case(cmd)
        if number == 1 and outcome["skills_loaded"] is not None:
            auth = outcome.get("auth")
            if auth in (None, "none"):
                print("Auth: claude.ai subscription (uses your Pro/Max allowance, no API billing)")
            else:
                print(f"Auth: {auth} - WARNING: billed per token to that API account. Unset it to use your subscription.")
            print(f"Model: {outcome.get('model')}")
            print(f"Skills listed at startup: {outcome['skills_loaded']}\n")
        ok = outcome["skill"] in accepted(case["expect"]) and not outcome["error"]
        passed += ok
        got = outcome["skill"] or ("(error)" if outcome["error"] else "(no skill)")
        want = " | ".join(str(e or "(no skill)") for e in accepted(case["expect"]))
        print(f"{'PASS' if ok else 'FAIL'}  {case['prompt'][:58]:58}  got={got:22} want={want}")
        if outcome["error"]:
            print(f"      error: {outcome['error']}")
        elif not ok and outcome["other_tools"]:
            print(f"      Claude used other tools first: {outcome['other_tools']}")
        rows.append({**case, **outcome, "pass": ok})

    if args.dry_run:
        return 0
    print(f"\n{passed}/{len(cases)} routed as expected in {time.time() - started:.0f}s.")
    report = PROJECT_ROOT / "tools" / "routing_report.json"
    report.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Details: {report.relative_to(PROJECT_ROOT)}")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
