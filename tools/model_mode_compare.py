"""Claude Code as the model: the same questions, the same model, several modes. Which mode answers best, and at what cost? (Lesson 6)

WHAT
    Sends each question of a list to the same model through `claude -p` in several modes, and reports per
    mode: how many answers were right, the input tokens sent, the output and thinking tokens, and the time.
    The modes differ only in how much of Claude Code's harness is left on:
        harness      Claude Code's defaults: its own system prompt and all its tools (Claude Code as a runtime)
        cc_prompt    tools off, Claude Code's own system prompt kept, your role appended
        own_prompt   tools off, your own short system prompt instead of Claude Code's
        strict       own_prompt, plus every customization off: settings files, --safe-mode, CLAUDE.md, attachments
    Every mode except harness also passes --strict-mcp-config, so MCP tools (also the connectors of your
    claude.ai account) stay out, and the modes differ only in the system prompt and the customizations.

WHY
    Some developers use Claude Code only as the model of their own agent, with its loop, tools, settings,
    memory files and MCP switched off. Others hope that Claude Code's own instructions make the model
    reason better. This tool measures both questions on your own questions: is cc_prompt more often right
    than own_prompt, and how many tokens does each mode cost?

HOW IT WORKS
    Each question is one `claude -p "<question>" --output-format json --model <model>` run from your user
    folder (no project CLAUDE.md), with the flags of its mode, and without saving a session. The answer is
    right when the question's regular expression matches it. build_command() makes the command for one mode;
    summarize() adds up the rows. The details of every run go to tools/model_mode_report.json.

WHICH WAY TO REACH CLAUDE
    claude -p only: each run must be a fresh, separate call, and the JSON it prints has everything. The SDK
    would give the same numbers (tools=[], system_prompt=..., strict_mcp_config=True, extra_args for
    --safe-mode). A direct API call needs an API key, which a Pro plan doesn't have; with a key you can add
    that baseline yourself.

HOW TO RUN  (in cmd, from the project folder, with the venv activated)
    python tools/model_mode_compare.py --dry-run                 (prints the commands, spends nothing)
    python tools/model_mode_compare.py --model haiku             (12 built-in questions x 4 modes = 48 runs)
    python tools/model_mode_compare.py --model haiku --modes cc_prompt,own_prompt --runs 3
    python tools/model_mode_compare.py --questions my_questions.json

OPTIONS
    --model NAME        haiku (the default), sonnet, opus, or a full id; the same model for every mode
    --modes LIST        comma-separated modes (default: all four)
    --runs N            how often each question runs in each mode (default 1)
    --questions FILE    a JSON list of {"prompt": "...", "expect": "regular expression"}
    --dry-run           print the commands instead of running them

OUTPUT  (a real run on Haiku, Lesson 6)
    mode           right  input tokens  output  thinking  seconds  model s
    harness       11/12         39,151      66        54      5.5      1.4
    cc_prompt     11/12          3,917       8         0      4.7      0.9
    own_prompt    10/12            906      40        32      5.1      1.2
    strict        10/12            882      29        23      4.6      0.9
    "seconds" is the whole run, "model s" the time the model needed. Exit code 0. Each run uses a little
    of your Pro allowance; the harness mode the most.

NEEDS
    Only the standard library, and Claude Code with --safe-mode (2.1.30x or later).

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k model_mode_compare
       Expected (2 tests; the time differs):
           ..
           ----------------------------------------------------------------------
           Ran 2 tests in 0.003s

           OK
       What they check: the flags of each mode (only harness keeps the tools; only cc_prompt keeps
       Claude Code's prompt; strict adds --safe-mode and the two environment variables), and how the
       results of each mode are added up. Add -v to see the name of each test.
    2. By hand: free.
           python tools/model_mode_compare.py --dry-run --modes strict
               one claude -p command per question, each with --tools "", --strict-mcp-config and --safe-mode
    3. With Claude: uses a little Pro allowance.
           python tools/model_mode_compare.py --model haiku --modes own_prompt
               Expected: a table with one row, and 12/12 or close to it.

IF SOMETHING GOES WRONG
    - "unknown option '--safe-mode'": your Claude Code is too old; run `claude update`.
    - A mode is often wrong on one question: read its answers in tools/model_mode_report.json; the regular
      expression may be too strict for an answer that is right in other words.

FILES IT READS AND WRITES
    Reads the questions file, if you give one. Writes tools/model_mode_report.json (ignored by git).

SEE ALSO
    agent/ask_claude.py (one question as a plain LLM call, with --strict); Lesson 6, "Using Claude Code
    only as the model".
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT = PROJECT_ROOT / "tools" / "model_mode_report.json"
ROLE = "You are the reasoning component of a Python agent. Answer briefly and exactly, in the format asked for."
MODES = ["harness", "cc_prompt", "own_prompt", "strict"]
# These two environment variables keep out CLAUDE.md files, and the skill list and similar notes.
STRICT_ENV = {"CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1", "CLAUDE_CODE_DISABLE_ATTACHMENTS": "1"}

QUESTIONS = [
    {"prompt": "A meeting starts at 10:40 and lasts 95 minutes. When does it end? Answer with the time only, as HH:MM.",
     "expect": r"\b12:15\b"},
    {"prompt": "What is 17 times 23? Answer with the number only.", "expect": r"^\D*391\D*$"},
    {"prompt": "Which day of the week is 2026-12-25? Answer with the day name only.", "expect": r"(?i)^\W*friday\W*$"},
    {"prompt": "What date is 45 days after 2026-11-20? Answer as YYYY-MM-DD only.", "expect": r"\b2027-01-04\b"},
    {"prompt": "Pens cost 2 dollars for 3 pens. How much do 12 pens cost? Answer with the number of dollars only.",
     "expect": r"^\D*8(\.0+)?\D*$"},
    {"prompt": "Classify this support ticket as exactly one of: billing, bug, feature_request. Ticket: "
               "'I was charged twice for my subscription this month.' Answer with the label only.",
     "expect": r"(?i)^\W*billing\W*$"},
    {"prompt": "Extract the city and the date from this sentence as JSON with the keys city and date (YYYY-MM-DD): "
               "'The workshop will take place in Lyon on 3 March 2027.' Answer with the JSON only.",
     "expect": r'(?s)"city"\s*:\s*"Lyon".*"date"\s*:\s*"2027-03-03"'},
    {"prompt": "An agent has three tools: get_weather(city), convert_units(value, from_unit, to_unit) and "
               "send_email(to, text). Which one tool answers 'How many km is 26.2 miles?' Answer with the tool name only.",
     "expect": r"^\W*convert_units\W*$"},
    {"prompt": "Anna is older than Ben. Ben is older than Carl. Who is the youngest? Answer with the name only.",
     "expect": r"(?i)^\W*carl\W*$"},
    {"prompt": "To answer 'Which region sold the most in sales.csv?', put these steps in order: A) add up the "
               "amounts per region, B) read the file, C) pick the region with the largest total. "
               "Answer with the three letters only, like XYZ.", "expect": r"^\W*BAC\W*$"},
    {"prompt": "If 5 machines make 5 widgets in 5 minutes, how many minutes do 100 machines need to make "
               "100 widgets? Answer with the number only.", "expect": r"^\D*\b5\b\D*$"},
    {"prompt": "Reply with exactly the word OK and nothing else.", "expect": r"^\s*OK\s*$"},
]


def build_command(claude: str, prompt: str, model: str, mode: str) -> tuple[list[str], dict]:
    """The claude -p command and the extra environment variables for one question in one mode."""
    cmd = [claude, "-p", prompt, "--model", model, "--output-format", "json", "--no-session-persistence"]
    if mode == "harness":
        return cmd, {}                                            # Claude Code exactly as it starts
    cmd += ["--tools", "", "--disable-slash-commands", "--strict-mcp-config"]   # no tools, skills or MCP tools
    if mode == "cc_prompt":
        return cmd + ["--append-system-prompt", ROLE], {}         # keeps Claude Code's own system prompt
    cmd += ["--system-prompt", ROLE]                              # replaces it with yours
    if mode == "own_prompt":
        return cmd, {}
    if mode == "strict":
        return cmd + ["--setting-sources", "", "--safe-mode", "--permission-mode", "dontAsk"], dict(STRICT_ENV)
    raise ValueError(f"unknown mode {mode!r}; use one of {MODES}")


def run_one(claude: str, question: dict, model: str, mode: str) -> dict:
    cmd, extra_env = build_command(claude, question["prompt"], model, mode)
    started = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          cwd=os.path.expanduser("~"), env={**os.environ, **extra_env})
    seconds = time.perf_counter() - started
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"mode": mode, "prompt": question["prompt"], "answer": None, "right": False, "seconds": seconds,
                "error": (proc.stderr or proc.stdout).strip()[:300]}
    usage = data.get("usage") or {}
    model_usage = data.get("modelUsage") or {}
    answer = (data.get("result") or "").strip()
    return {
        "mode": mode, "prompt": question["prompt"], "answer": answer,
        "right": bool(re.search(question["expect"], answer)) and not data.get("is_error"),
        "input_tokens": usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
                        + usage.get("cache_read_input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "thinking_tokens": sum(m.get("thinkingTokens", 0) for m in model_usage.values()),
        "seconds": seconds, "api_seconds": (data.get("duration_api_ms") or 0) / 1000,
        "models": list(model_usage),          # which model really answered: a silent fallback shows here
    }


def summarize(rows: list[dict], modes: list[str]) -> list[dict]:
    """One line per mode: right answers, and the average tokens and seconds per run."""
    out = []
    for mode in modes:
        mine = [r for r in rows if r["mode"] == mode]
        n = len(mine) or 1
        avg = lambda key: sum(r.get(key, 0) for r in mine) / n
        out.append({"mode": mode, "right": sum(r["right"] for r in mine), "runs": len(mine),
                    "input_tokens": avg("input_tokens"), "output_tokens": avg("output_tokens"),
                    "thinking_tokens": avg("thinking_tokens"), "seconds": avg("seconds"),
                    "api_seconds": avg("api_seconds")})
    return out


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Compare modes of Claude Code as the model, on the same questions.")
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--modes", default=",".join(MODES))
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--questions")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    questions = json.loads(Path(args.questions).read_text(encoding="utf-8")) if args.questions else QUESTIONS
    claude = shutil.which("claude") or "claude"

    if args.dry_run:
        for mode in modes:
            for q in questions:
                cmd, env = build_command(claude, q["prompt"], args.model, mode)
                prefix = "".join(f"set {k}={v} && " for k, v in env.items())
                print(prefix + " ".join(f'"{c}"' if (" " in c or not c) else c for c in cmd))
        return 0

    rows = []
    for run in range(args.runs):
        for mode in modes:
            for number, q in enumerate(questions, 1):
                row = run_one(claude, q, args.model, mode)
                rows.append(row)
                mark = "right" if row["right"] else "WRONG"
                print(f"[{mode:10}] {number:2}. {mark}  {str(row['answer'])[:60]!r}")
                other = [m for m in row.get("models", []) if args.model not in m]
                if other:
                    print(f"             note: answered by {other}, not by {args.model}")
    print(f"\nModel: {args.model}, {len(questions)} questions, {args.runs} run(s) per mode\n")
    print(f"{'mode':12} {'right':>7} {'input tokens':>13} {'output':>7} {'thinking':>9} {'seconds':>8} {'model s':>8}")
    for s in summarize(rows, modes):
        print(f"{s['mode']:12} {s['right']:>3}/{s['runs']:<3} {s['input_tokens']:>13,.0f} {s['output_tokens']:>7.0f} "
              f"{s['thinking_tokens']:>9.0f} {s['seconds']:>8.1f} {s['api_seconds']:>8.1f}")
    REPORT.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDetails: {REPORT.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
