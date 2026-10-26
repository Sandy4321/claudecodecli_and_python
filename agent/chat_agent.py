"""A conversation with several questions in one Claude Code session (Lesson 6, Part 4, Step 14).

WHAT
    Asks two demo questions in the same conversation: "Which region sold the most in data/sales.csv?"
    and the follow-up "And which region sold the least?". With --interactive you type your own
    questions instead. Each step is printed as in run_agent.py, plus the time each question took.

WHY
    A chat program, or any program with follow-up questions, needs Claude to remember the earlier
    questions and answers. This shows how, both ways, and how much faster a follow-up is when
    nothing has to restart.

TWO WAYS TO REACH CLAUDE, ONE PROGRAM
    Both ways keep one conversation, so "And the least?" is understood. They do it differently:
    1. The Agent SDK (the default): ClaudeSDKClient starts one claude.exe and keeps it running, with
       the conversation open, until the `async with` block ends. client.query() sends a question
       into that conversation; client.receive_response() yields the steps of that one answer.
    2. claude -p (add --cli): every question starts a new claude process. The first answer's last
       JSON line has a "session_id"; the next question passes it back:
           claude -p "<first question>" --output-format stream-json --verbose ...
           claude -p "<follow-up>" --resume <session_id> --output-format stream-json --verbose ...
       Claude Code saved the conversation to disk, and loads it again for each follow-up. Your
       program has to keep the session_id. Needs only the standard library: no SDK.

WHEN TO USE WHICH
    The SDK: for a chat, or many quick follow-ups. Nothing restarts, so a follow-up is fast (1.2
    seconds against 5.8 seconds in the real runs of Lesson 6, Step 14).
    claude -p: for a follow-up now and then, perhaps hours later, or from a .bat file: --resume works
    as long as the saved conversation exists.

HOW TO RUN  (in cmd, from the project folder, with the venv activated)
    python agent/chat_agent.py --model haiku
    python agent/chat_agent.py --cli --model haiku
    python agent/chat_agent.py --model haiku --interactive          (an empty line ends the chat)

OPTIONS
    --cli            use claude -p with --resume instead of the Agent SDK
    --model NAME     haiku, sonnet, opus, or a full id; default: your Claude Code default
    --interactive    type your own questions instead of the two demo questions

NEEDS
    For the SDK way claude-agent-sdk (python -m pip install -r agent/requirements.txt).
    Uses some Pro allowance.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k chat_agent
       Expected (1 test; the time differs):
           .
           ----------------------------------------------------------------------
           Ran 1 test in 0.009s

           OK
       What it checks: that the --cli way asks the demo questions and passes the first answer's
       session_id to the next question with --resume. Add -v to see the name of each test.
    2. With Claude: uses a little Pro allowance.
           python agent/chat_agent.py --model haiku          (the SDK way)
           python agent/chat_agent.py --cli --model haiku    (the claude -p way)
           Expected, both ways: the second answer names South (the least), without the file being named again,
           and a [time] line per question. In the real runs of Lesson 6, Step 14 the follow-up took 0.9 seconds
           with the SDK, and 5.6 seconds with --cli.

IF SOMETHING GOES WRONG
    - "The 'claude' command was not found": install Claude Code, or open a new cmd window so PATH is
      read again.
    - "The SDK way needs claude-agent-sdk": install it (python -m pip install -r agent/requirements.txt),
      or add --cli.
    - With --cli the follow-up is not understood: the first run's last line had no session_id (it
      failed). Run the first question alone with run_agent.py --cli to see the error.

FILES IT READS AND WRITES
    Claude Code saves each run as a session in your user folder, in .claude/projects (both ways). The
    --cli way needs them: --resume loads the saved conversation.

SEE ALSO
    run_agent.py (build_options, build_cli_command, run_cli); Lesson 6, Step 14.
"""

import argparse
import asyncio
import sys
import time

from run_agent import build_cli_command, build_options, find_claude, print_message, run_cli

DEMO_QUESTIONS = [
    "Which region sold the most in data/sales.csv?",
    "And which region sold the least?",
]


def next_question(interactive: bool, demo: list[str]):
    """The questions to ask: the demo list, or whatever you type until an empty line."""
    if not interactive:
        yield from demo
        return
    while True:
        try:
            question = input("\nyou> ").strip()
        except EOFError:
            return
        if not question:
            return
        yield question


async def chat(model: str | None, interactive: bool) -> None:
    from claude_agent_sdk import ClaudeSDKClient

    async with ClaudeSDKClient(options=build_options("all", model)) as client:
        for number, question in enumerate(next_question(interactive, DEMO_QUESTIONS), start=1):
            if not interactive:
                print(f"\n[you]   {question}")
            started = time.perf_counter()
            await client.query(question)                     # same session: Claude sees the earlier turns
            async for message in client.receive_response():  # ends after this question's ResultMessage
                print_message(message, show_init=number == 1)
            print(f"[time]  question {number} took {time.perf_counter() - started:.1f}s")


def chat_cli(model: str | None, interactive: bool) -> None:
    """The --cli way: one claude -p process per question, joined by the session_id."""
    claude = find_claude()
    session_id = None
    for number, question in enumerate(next_question(interactive, DEMO_QUESTIONS), start=1):
        if not interactive:
            print(f"\n[you]   {question}")
        started = time.perf_counter()
        result = run_cli(build_cli_command(claude, question, "all", model, resume=session_id),
                         show_init=number == 1)
        session_id = result.get("session_id") or session_id   # the next question continues this conversation
        print(f"[time]  question {number} took {time.perf_counter() - started:.1f}s")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    parser = argparse.ArgumentParser(description="Ask several questions in one conversation.")
    parser.add_argument("--cli", action="store_true", help="use claude -p with --resume instead of the Agent SDK")
    parser.add_argument("--model", help="model alias or id, e.g. haiku (default: your Claude Code default)")
    parser.add_argument("--interactive", action="store_true", help="type your own questions; an empty line ends")
    args = parser.parse_args()
    if args.cli:
        chat_cli(args.model, args.interactive)
        return 0
    try:
        asyncio.run(chat(args.model, args.interactive))
    except ImportError:
        print("The SDK way needs claude-agent-sdk: python -m pip install -r agent/requirements.txt (or add --cli)")
        return 1
    except Exception as error:
        print(f"Chat stopped with an error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
