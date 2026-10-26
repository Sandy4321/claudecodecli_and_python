"""Your Anthropic API call, done with a Pro subscription instead (Lesson 6, Part 5, Step 20).

WHAT
    The same job as this typical API program, with the same settings at the top of the file
    (MODEL, EFFORT, MAX_TOKENS, PROMPT, SYSTEM), and the same printout (the answer and the tokens):
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=MODEL, max_tokens=4096,
            thinking={"type": "adaptive"}, output_config={"effort": EFFORT},
            messages=[{"role": "user", "content": PROMPT}])
        print(response.content[0].text, response.usage.input_tokens, response.usage.output_tokens)

WHY
    So you can move your own API code to Pro, one line at a time. Pro has no API key, so the call goes
    through the Claude Code program, which holds your login.

HOW EACH PART IS TRANSLATED
    model=...                  ->  --model (claude -p)          model=... (SDK)
    output_config effort       ->  --effort                     effort=...
    max_tokens                 ->  the environment variable CLAUDE_CODE_MAX_OUTPUT_TOKENS (both ways)
    system=...                 ->  --system-prompt              system_prompt=...
    no tools                   ->  --tools ""                   tools=[]
    thinking adaptive          ->  nothing to set: the 5.5 models always think adaptively
    response.content / usage   ->  data["result"] / data["usage"]    ResultMessage.result / .usage

TWO WAYS TO REACH CLAUDE, ONE PROGRAM
    1. claude -p (the default): create_with_cli() runs `claude -p ... --output-format json` with
       subprocess. Needs only the standard library.
    2. The Agent SDK (add --sdk): create_with_sdk() calls query() from claude-agent-sdk, with the
       same settings as options (model=, effort=, system_prompt=, tools=[], env= for max_tokens).
    Both print the same answer and token counts.

WHEN TO USE WHICH
    claude -p: the closest match to one API call, with nothing to install. The SDK: when the program
    will grow into an agent with conversations, hooks or tools (see run_agent.py).

HOW TO RUN  (in cmd, from the project folder, with the venv activated)
    python agent/api_equivalent.py
    python agent/api_equivalent.py --sdk
    python agent/api_equivalent.py --model opus --effort high --prompt "How many integers from 1 to 10000 are divisible by 3 or by 5, but not by 7?"

OPTIONS  (each one overrides the setting of the same name at the top of the file)
    --model NAME     sonnet (the default), haiku, opus, or a full model id
    --effort LEVEL   low (the default), medium, high, xhigh or max
    --prompt TEXT    the question (default: "Explain Python decorators briefly.")
    --sdk            use the Agent SDK instead of claude -p

OUTPUT
    The answer, then:
        Input tokens: 4309 (new 2, written to cache 4307, read from cache 0)
        Output tokens: 77 (of which thinking 73)
    The input is larger than with the API, because Claude Code adds its own text around your prompt.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k api_equivalent
       Expected (1 test; the time differs):
           .
           ----------------------------------------------------------------------
           Ran 1 test in 0.006s

           OK
       What it checks: that the token counts are printed like response.usage of the API (input = new +
       cache write + cache read). Add -v to see the name of each test.
    2. With Claude: uses a little Pro allowance.
           python agent/api_equivalent.py --model haiku --prompt "What is 7 times 6? Answer with the number only."
           python agent/api_equivalent.py --sdk --model haiku --prompt "What is 7 times 6? Answer with the number only."
               Expected, both ways: 42, then two token lines. The real runs:
                   Input tokens: 4286 (new 2, written to cache 1641, read from cache 2643)      (claude -p)
                   Input tokens: 4029 (new 2, written to cache 1105, read from cache 2922)      (the SDK)
                   Output tokens: 3 (of which thinking 0)                                       (both)

IF SOMETHING GOES WRONG
    - "The 'claude' command was not found": install Claude Code, or open a new cmd window so PATH is
      read again.
    - "The SDK way needs claude-agent-sdk": install it (python -m pip install -r agent/requirements.txt),
      or add --cli.
    - "Input tokens" is much bigger than your prompt: normal. Claude Code adds its own text around your
      prompt (Lesson 6, Step 20).

FILES IT READS AND WRITES
    None with claude -p. The SDK way's question is saved as a session in your user folder's
    .claude/projects.

SEE ALSO
    ask_claude.py; Lesson 6, Step 20.
"""

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys

MODEL = "sonnet"     # Claude Code takes aliases (haiku, sonnet, opus) or full IDs like "claude-sonnet-5-5"
EFFORT = "low"       # low, medium, high, xhigh, max
MAX_TOKENS = 4096    # like max_tokens; Claude Code reads it from CLAUDE_CODE_MAX_OUTPUT_TOKENS
PROMPT = "Explain Python decorators briefly."
# Replaces Claude Code's long coding-agent instructions, so the call behaves like a plain API call.
SYSTEM = "You are a concise, helpful assistant."


def create_with_cli(prompt: str, model: str, effort: str) -> dict:
    """client.messages.create(...), done by running `claude -p` once."""
    claude = shutil.which("claude")
    if not claude:
        raise SystemExit("The 'claude' command was not found. Install Claude Code and log in once.")
    cmd = [
        claude, "-p", prompt,
        "--model", model,                   # model=MODEL
        "--effort", effort,                 # output_config={"effort": EFFORT}
        "--system-prompt", SYSTEM,          # system=...
        "--output-format", "json",          # one JSON object: the answer and the usage
        "--tools", "",                      # no tools: a plain question and answer, like the API call
        "--disable-slash-commands",         # no skills either
        "--no-session-persistence",         # don't save it as a resumable session
    ]
    env = {**os.environ, "CLAUDE_CODE_MAX_OUTPUT_TOKENS": str(MAX_TOKENS)}     # max_tokens=MAX_TOKENS
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env,
                          cwd=os.path.expanduser("~"))     # a neutral folder: no project CLAUDE.md
    data = json.loads(proc.stdout)
    return {"text": data.get("result"), "usage": data.get("usage") or {}, "model_usage": data.get("modelUsage") or {}}


async def create_with_sdk(prompt: str, model: str, effort: str) -> dict:
    """The same through the Agent SDK. It starts its own claude.exe, with the same login."""
    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

    options = ClaudeAgentOptions(
        model=model, effort=effort, system_prompt=SYSTEM,
        tools=[], setting_sources=[], max_turns=1, cwd=os.path.expanduser("~"),
        env={"CLAUDE_CODE_MAX_OUTPUT_TOKENS": str(MAX_TOKENS)},
    )
    reply = {"text": None, "usage": {}, "model_usage": {}}
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            reply = {"text": message.result, "usage": message.usage or {},
                     "model_usage": getattr(message, "model_usage", None) or {}}
    return reply


def print_like_api(reply: dict) -> None:
    """Print the answer and the token counts, like the API example prints response.usage."""
    print(reply["text"])
    usage = reply["usage"]
    fresh = usage.get("input_tokens", 0)
    cache_write = usage.get("cache_creation_input_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)
    thinking = sum(m.get("thinkingTokens", 0) for m in reply["model_usage"].values())
    print()
    print("Input tokens:", fresh + cache_write + cache_read,
          f"(new {fresh}, written to cache {cache_write}, read from cache {cache_read})")
    print("Output tokens:", usage.get("output_tokens", 0), f"(of which thinking {thinking})")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="An Anthropic API call, done with a Pro login.")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--effort", default=EFFORT, choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--prompt", default=PROMPT)
    parser.add_argument("--sdk", action="store_true", help="use the Agent SDK instead of claude -p")
    args = parser.parse_args()
    if os.environ.get("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY is set, so this call is billed to that API account, not to Pro.\n")
    if args.sdk:
        reply = asyncio.run(create_with_sdk(args.prompt, args.model, args.effort))
    else:
        reply = create_with_cli(args.prompt, args.model, args.effort)
    print_like_api(reply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
