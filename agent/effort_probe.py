"""Which reasoning effort is in effect at each step? (Lesson 6, Part 6)

WHAT
    Runs the skills agent like run_agent.py, and before each tool call prints the effort level Claude
    Code reports for that moment ([effort] low before PowerShell: ...). Several prompts are asked one
    after the other in the same conversation. After each answer it prints the output and thinking
    tokens per model ([usage]).

WHY
    To see where an effort comes from: a skill's `effort:` line, the session's --effort, the
    environment variable CLAUDE_CODE_EFFORT_LEVEL, or the model's default. Lesson 6, Steps 22 to 26 use
    it to prove that a skill sets the effort of the requests sent while it is active.

TWO WAYS TO REACH CLAUDE, ONE PROGRAM
    The effort level is only reported to hooks, so both ways use a PreToolUse hook without a matcher
    (before every tool). Both print the line made by effort_hook.effort_line(), and the same
    [usage] lines from the result's model usage.
    1. The Agent SDK (the default): the hook is a function inside this program, and
       ClaudeSDKClient keeps one conversation for all prompts.
    2. claude -p (add --cli): the hook is the script agent/effort_hook.py, switched on with
       --settings; --include-hook-events brings its line back as a JSON line. Each prompt is one
       claude -p run; the second and later prompts pass --resume <session_id> to continue the
       conversation. Needs only the standard library: no SDK.

WHEN TO USE WHICH
    Both give the same levels. The SDK way is faster with several prompts (nothing restarts). The
    claude -p way shows how to watch the effort from any program, or from .claude/settings.json
    for the interactive claude window.

HOW TO RUN  (in cmd, from the project folder, with the venv activated)
    python agent/effort_probe.py --model opus "Convert 26.2 miles to kilometers."
    python agent/effort_probe.py --cli --model opus "Convert 26.2 miles to kilometers."
    python agent/effort_probe.py --model opus --effort high "/converting-units 26.2 mi km"
    python agent/effort_probe.py --model sonnet "Convert 26.2 miles to kilometers." "Now read the file data/article.txt and tell me its first sentence."

OPTIONS
    PROMPT ...       one or more prompts, asked one after the other in one conversation
    --cli            use claude -p with the hook script effort_hook.py instead of the Agent SDK
    --model NAME     haiku, sonnet, opus, or a full id; default: your Claude Code default
    --effort LEVEL   the session effort: low, medium, high, xhigh or max; default: the model's default

NEEDS
    For the SDK way claude-agent-sdk (python -m pip install -r agent/requirements.txt).
    Uses Pro allowance, more with Opus.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k effort_probe -k effort_hook
       Expected (2 tests; the time differs):
           ..
           ----------------------------------------------------------------------
           Ran 2 tests in 0.137s

           OK
       What they check: that --cli switches effort_hook.py on for every tool, resumes the conversation
       for the second prompt, and prints the [usage] lines; and the hook itself. Add -v to see the name
       of each test.
    2. With Claude: uses a little Pro allowance.
           python agent/effort_probe.py --cli --model sonnet "Convert 26.2 miles to kilometers." "Now read the file data/article.txt and tell me its first sentence."
           Expected (a real run; the same levels as the SDK way in Lesson 6, Step 24):
               [effort] medium before Skill: converting-units
               [effort] low    before Bash: python ".../converting-units/scripts/convert.py" convert 26.2 mi km
               ...
               [effort] medium before Read: .../data/article.txt

IF SOMETHING GOES WRONG
    - "The 'claude' command was not found": install Claude Code, or open a new cmd window so PATH is
      read again.
    - "The SDK way needs claude-agent-sdk": install it (python -m pip install -r agent/requirements.txt),
      or add --cli.
    - No [effort] lines at all: Claude used no tool, so no hook ran. Ask something that needs a skill.
    - The same level everywhere: the skill has no effort: line, or CLAUDE_CODE_EFFORT_LEVEL is set
      (it overrides the skill's line).

FILES IT READS AND WRITES
    Claude Code saves each run as a session in your user folder, in .claude/projects (both ways).

SEE ALSO
    effort_hook.py; run_agent.py; Lesson 6, Part 6 (Steps 22 to 26).
"""

import argparse
import asyncio
import sys
from pathlib import Path

from effort_hook import effort_line
from run_agent import build_cli_command, build_options, find_claude, hook_settings, print_message, run_cli

HOOK_SCRIPT = Path(__file__).with_name("effort_hook.py")


def print_usage(model_usage: dict | None) -> None:
    for name, usage in (model_usage or {}).items():
        print(f"[usage] {name}: output {usage.get('outputTokens', 0)} tokens, "
              f"of which thinking {usage.get('thinkingTokens', 0)}")


async def show_effort(hook_input, tool_use_id, context):
    print(effort_line(hook_input))
    return {}                                   # no decision: the normal permission rules apply


async def run(prompts: list[str], model: str | None, effort: str | None) -> None:
    from claude_agent_sdk import ClaudeSDKClient, HookMatcher, ResultMessage

    options = build_options("all", model, effort)
    options.hooks = {"PreToolUse": [HookMatcher(hooks=[show_effort])]}   # no matcher: every tool
    async with ClaudeSDKClient(options=options) as client:              # one conversation for all prompts
        for prompt in prompts:
            if len(prompts) > 1:
                print(f"\n[you]   {prompt}")
            await client.query(prompt)
            async for message in client.receive_response():
                print_message(message, show_init=False)
                if isinstance(message, ResultMessage):
                    print_usage(getattr(message, "model_usage", None))


def run_cli_way(prompts: list[str], model: str | None, effort: str | None) -> None:
    """The --cli way: one claude -p run per prompt, joined by --resume, with effort_hook.py as the hook."""
    claude = find_claude()
    settings = hook_settings(HOOK_SCRIPT)       # no matcher: every tool
    session_id = None
    for prompt in prompts:
        if len(prompts) > 1:
            print(f"\n[you]   {prompt}")
        result = run_cli(build_cli_command(claude, prompt, "all", model, effort, resume=session_id, settings=settings),
                         show_init=False)
        session_id = result.get("session_id") or session_id
        print_usage(result.get("modelUsage"))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Show the effort level in effect at each tool call.")
    parser.add_argument("prompts", nargs="+", help="one or more prompts, asked in one conversation")
    parser.add_argument("--cli", action="store_true", help="use claude -p and the hook script effort_hook.py")
    parser.add_argument("--model", help="model alias or id, e.g. opus (default: your Claude Code default)")
    parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"],
                        help="session effort (default: the model's default)")
    args = parser.parse_args()
    if args.cli:
        run_cli_way(args.prompts, args.model, args.effort)
        return 0
    try:
        asyncio.run(run(args.prompts, args.model, args.effort))
    except ImportError:
        print("The SDK way needs claude-agent-sdk: python -m pip install -r agent/requirements.txt (or add --cli)")
        return 1
    except Exception as error:
        print(f"Agent stopped with an error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
