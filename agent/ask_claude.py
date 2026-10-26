"""Ask Claude a question from Python, like a plain LLM, with only a Pro subscription (Lesson 6, Part 3).

WHAT
    Sends one question to Claude and prints the answer, then one line with facts about the call:
    whether it worked, the model, the thinking tokens, a cost estimate and the time. With --schema the
    answer comes back as JSON in a shape you describe (structured output).

WHY
    With an API key you would write (pip install anthropic):
        client = anthropic.Anthropic()                    # reads ANTHROPIC_API_KEY
        reply = client.messages.create(model=..., max_tokens=..., messages=[...])
    A Pro subscription has no API key, so the anthropic package can't log in. The Claude Code program
    holds your Pro login (saved when you ran /login), so this program asks Claude Code instead. Claude
    Code calls the model and counts the call against your Pro allowance.

TWO WAYS TO REACH CLAUDE, ONE PROGRAM
    1. claude -p (the default): runs `claude -p "question" --output-format json ...` with subprocess,
       and reads the one JSON object it prints. Needs only the Python standard library.
    2. The Agent SDK (add --sdk): calls query() from the claude-agent-sdk package, which starts its own
       copy of claude.exe with the same login. Install it once: python -m pip install -r agent/requirements.txt
    Both ways send the same settings: no tools, no skills, a short system prompt instead of Claude Code's
    long one, and your user folder as the working folder, so the call behaves like a plain API call.
    --schema works both ways: claude -p gets --json-schema, the SDK gets
    output_format={"type": "json_schema", "schema": ...} (which the SDK turns into the same flag).
    --strict works both ways too: it also switches off MCP tools (including the connectors of your
    claude.ai account, which --tools "" leaves in), settings files, CLAUDE.md files and attachments. A
    measured question went from about 4,300 to about 870 input tokens (Lesson 6, "Using Claude Code only
    as the model").

WHEN TO USE WHICH
    claude -p: one question at a time, nothing to install; the usual choice for "Claude as an LLM".
    The SDK: when your program already uses the SDK for other jobs, or will grow into an agent with
    conversations, hooks or tools (run_agent.py and the other agent programs).

HOW TO RUN  (in cmd, from the project folder, with the venv activated)
    python agent/ask_claude.py "Explain a Python decorator in two sentences."
    python agent/ask_claude.py --sdk "Explain a Python decorator in two sentences."
    python agent/ask_claude.py --model sonnet --effort low "How many integers from 1 to 10000 are divisible by 3?"
    python agent/ask_claude.py --schema "List three European capitals."
    python agent/ask_claude.py --sdk --schema "List three European capitals."
    python agent/ask_claude.py --strict "What is 17 times 23? Answer with the number only."

OPTIONS
    --model NAME     haiku (the default), sonnet, opus, or a full model id
    --effort LEVEL   low, medium, high, xhigh or max; without it, the model's default (Lesson 6, Part 5)
    --sdk            use the Agent SDK instead of claude -p
    --schema         a demo of structured output: the answer is JSON with a list of countries and capitals
    --strict         Claude Code strictly as the model: also no MCP tools, settings, CLAUDE.md or attachments

OUTPUT
    The answer, then a line like:
        --- {"is_error": false, "model_usage": ["claude-haiku-5-5"], "thinking_tokens": 0,
             "cost_estimate_usd": 0.00039922, "duration_ms": 4288}
    The cost is an API list-price estimate. On Pro nothing is charged; it only shows how big a call was.

GOOD TO KNOW
    If the environment variable ANTHROPIC_API_KEY is set, Claude Code uses it instead of your Pro login,
    and that API account pays. The program warns you when it is set.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k AskClaudeCommand
       Expected (5 tests; the time differs):
           .....
           ----------------------------------------------------------------------
           Ran 5 tests in 0.005s

           OK
       What they check: the claude -p command (no tools, no session, --model, --effort only when set),
       the flags that --strict adds, and the sum of thinking tokens; the third test checks
       tools/run_cost.py. Add -v to see the name of each test.
    2. With Claude: uses a little Pro allowance.
           python agent/ask_claude.py --model haiku "What is 7 times 6? Answer with the number only."
           python agent/ask_claude.py --sdk --model haiku "What is 7 times 6? Answer with the number only."
               Expected, both ways:
                   42

                   --- {"is_error": false, "model_usage": ["claude-haiku-5-5"], "thinking_tokens": 0, ...}
           python agent/ask_claude.py --sdk --schema "List three European capitals."
               Expected: JSON with "capitals": a list of country and capital pairs (the real run: France and
               Paris, Germany and Berlin, Italy and Rome).
           python agent/ask_claude.py --strict "What is 17 times 23? Answer with the number only."
           python agent/ask_claude.py --sdk --strict "What is 17 times 23? Answer with the number only."
               Expected, both ways: 391, and a cost estimate about five times smaller than without --strict.

IF SOMETHING GOES WRONG
    - "The 'claude' command was not found": install Claude Code, or open a new cmd window so PATH is
      read again.
    - "The SDK way needs claude-agent-sdk": install it (python -m pip install -r agent/requirements.txt),
      or add --cli.
    - "WARNING: ANTHROPIC_API_KEY is set": that API account pays for the call. Remove the variable.
    - "is_error": true with "Not logged in": run claude once and type /login.
    - --strict fails with "unknown option": your Claude Code is too old for --safe-mode; run claude update.

FILES IT READS AND WRITES
    None with claude -p (--no-session-persistence). The SDK way's question is saved as a session in your
    user folder's .claude/projects.

SEE ALSO
    api_equivalent.py (the same with your API settings); Lesson 6, Part 3.
"""

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys

# Replaces Claude Code's long coding-agent system prompt, so this behaves like a plain chat model.
SYSTEM_PROMPT = "You are a concise, helpful assistant. Answer directly."
# Haiku uses the least of your Pro allowance; pass --model sonnet or --model opus for harder questions.
DEFAULT_MODEL = "haiku"

# Reasoning effort, as with an API key. None = the model's default (medium on the 5.5 models).
EFFORT_LEVELS = ["low", "medium", "high", "xhigh", "max"]

# --strict: what else Claude Code would add besides the model. The flags need Claude Code 2.1.30x or later.
STRICT_FLAGS = ["--strict-mcp-config",            # no MCP tools, also not your claude.ai connectors
                "--setting-sources", "",          # no user, project or local settings files
                "--safe-mode",                    # no CLAUDE.md, skills, plugins, hooks or custom agents
                "--permission-mode", "dontAsk",   # never wait for a permission answer
                "--max-turns", "1"]               # one answer, never a loop
STRICT_ENV = {"CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1", "CLAUDE_CODE_DISABLE_ATTACHMENTS": "1"}

CAPITALS_SCHEMA = {
    "type": "object",
    "properties": {"capitals": {"type": "array", "items": {
        "type": "object",
        "properties": {"country": {"type": "string"}, "capital": {"type": "string"}},
        "required": ["country", "capital"]}}},
    "required": ["capitals"],
}


def build_cli_command(claude: str, question: str, model: str = DEFAULT_MODEL, system: str = SYSTEM_PROMPT,
                      schema: dict | None = None, effort: str | None = None, strict: bool = False) -> list[str]:
    """The `claude -p` command line for one question (a separate function, so tests can check it)."""
    cmd = [
        claude, "-p", question,
        "--output-format", "json",      # one JSON object with the answer, usage and cost estimate
        "--model", model,
        "--system-prompt", system,
        "--tools", "",                  # no file or shell tools: a pure question-and-answer call
        "--disable-slash-commands",     # no skills either
        "--no-session-persistence",     # don't save this as a resumable session
    ]
    if schema:
        cmd += ["--json-schema", json.dumps(schema)]
    if effort:
        cmd += ["--effort", effort]      # how much Claude thinks before it answers
    if strict:
        cmd += STRICT_FLAGS
    return cmd


def thinking_tokens(model_usage: dict | None) -> int:
    """Tokens Claude spent thinking, summed over the models used (they count as output tokens)."""
    return sum(usage.get("thinkingTokens", 0) for usage in (model_usage or {}).values())


def ask_cli(question: str, model: str = DEFAULT_MODEL, system: str = SYSTEM_PROMPT, schema: dict | None = None,
            effort: str | None = None, strict: bool = False) -> dict:
    """One question -> one answer, by running `claude -p` (headless Claude Code) as a subprocess."""
    claude = shutil.which("claude")
    if not claude:
        raise SystemExit("The 'claude' command was not found. Install Claude Code and run it once to log in.")
    cmd = build_cli_command(claude, question, model, system, schema, effort, strict)
    env = {**os.environ, **(STRICT_ENV if strict else {})}
    # Run in a neutral folder so no project CLAUDE.md or settings change the answer.
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=os.path.expanduser("~"), env=env)
    if proc.returncode != 0 and not proc.stdout.strip():
        raise RuntimeError(proc.stderr.strip() or f"claude exited with code {proc.returncode}")
    data = json.loads(proc.stdout)
    return {
        "answer": data.get("structured_output") if schema else data.get("result"),
        "is_error": data.get("is_error"),
        "model_usage": list((data.get("modelUsage") or {}).keys()),
        "thinking_tokens": thinking_tokens(data.get("modelUsage")),
        "cost_estimate_usd": data.get("total_cost_usd"),
        "duration_ms": data.get("duration_ms"),
    }


async def ask_sdk(question: str, model: str = DEFAULT_MODEL, system: str = SYSTEM_PROMPT,
                  schema: dict | None = None, effort: str | None = None, strict: bool = False) -> dict:
    """The same call through the Agent SDK. It starts its bundled claude.exe, which uses the same login."""
    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

    options = ClaudeAgentOptions(
        model=model,
        system_prompt=system,
        tools=[],               # no built-in tools
        setting_sources=[],     # ignore CLAUDE.md, skills and settings on disk
        max_turns=1,
        cwd=os.path.expanduser("~"),
        effort=effort,          # None = the model's default
        output_format={"type": "json_schema", "schema": schema} if schema else None,   # --json-schema
        strict_mcp_config=strict,                                                       # --strict-mcp-config
        extra_args={"safe-mode": None, "permission-mode": "dontAsk"} if strict else {},
        env=STRICT_ENV if strict else {},
    )
    result = {"answer": None, "is_error": True}
    # Let the stream finish instead of returning mid-loop, so the SDK can shut claude.exe down cleanly.
    async for message in query(prompt=question, options=options):
        if isinstance(message, ResultMessage):
            result = {"answer": message.structured_output if schema else message.result,
                      "is_error": message.is_error,
                      "model_usage": list((message.model_usage or {}).keys()),
                      "thinking_tokens": thinking_tokens(message.model_usage),
                      "cost_estimate_usd": message.total_cost_usd, "duration_ms": message.duration_ms}
    return result


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    parser = argparse.ArgumentParser(description="Ask Claude a question using your Claude Code login.")
    parser.add_argument("question")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="haiku (default), sonnet, opus, or a full model id")
    parser.add_argument("--schema", action="store_true", help="demo: return structured JSON (European capitals)")
    parser.add_argument("--sdk", action="store_true", help="use the Agent SDK instead of claude -p")
    parser.add_argument("--effort", choices=EFFORT_LEVELS, help="reasoning effort (default: the model's default)")
    parser.add_argument("--strict", action="store_true", help="also no MCP tools, settings, CLAUDE.md or attachments")
    args = parser.parse_args()

    if os.environ.get("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY is set. Claude Code will use it, and this call is billed to that "
              "API account, not your Pro plan.\n")

    schema = CAPITALS_SCHEMA if args.schema else None
    if args.sdk:
        result = asyncio.run(ask_sdk(args.question, args.model, schema=schema, effort=args.effort, strict=args.strict))
    else:
        result = ask_cli(args.question, args.model, schema=schema, effort=args.effort, strict=args.strict)

    answer = result.pop("answer")
    print(json.dumps(answer, indent=2, ensure_ascii=False) if isinstance(answer, (dict, list)) else answer)
    print("\n---", json.dumps(result), "(cost is an API list-price estimate; on Pro nothing is charged)")
    return 1 if result.get("is_error") else 0


if __name__ == "__main__":
    sys.exit(main())
