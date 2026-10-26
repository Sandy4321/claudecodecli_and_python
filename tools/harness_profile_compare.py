"""Non-coding tasks on data files: Claude Code as the model only, against Claude Code with tools, skills or everything (Lesson 6).

WHAT
    Runs the same data questions (sales totals, an average, an invoice total, a word count, working
    days, one logic question as a control, and two questions on a table of 300 rows, or --rows N, that is
    too long to add up in the head) through `claude -p` in five profiles, on the same model,
    and reports per profile: right answers, how many runs computed with code, input tokens, cost
    estimate, cost per right answer, turns and time.
        model    Claude Code only as the model: no tools, own short prompt, every customization off, one
                 turn. The file's text is pasted into the question, as your own program would do with
                 a plain API call.
        lean     Claude Code's own prompt and loop, but only Read and python commands, no skills, no
                 settings or MCP tools, at most 6 turns. Claude reads the file and decides itself
                 whether to compute with Python or in its head.
        lean_py  lean, plus one rule appended to Claude Code's prompt: compute every number with Python.
        skills   the agent of this course: the project's skills and CLAUDE.md, Skill, Read and python
                 commands, no MCP tools, at most 8 turns.
        full     Claude Code with everything it loads by default (also your user settings and your
                 account's MCP connectors), with the same allowed tools and turn limit as skills.

WHY
    To answer three questions with measurements instead of opinions, for non-coding work:
      1. When does Claude Code with its tools beat a plain model call? (model against lean, skills, full)
      2. What makes it better? (lean against lean_py against skills: Claude's head, Claude's own
         Python, your tested scripts)
      3. How much can you switch off and keep the advantage? (full against skills against lean)
    Cost per right answer is the fair measure: a profile that uses more tokens can still be cheaper if
    it is wrong less often.

HOW IT WORKS
    One `claude -p "<question>" --output-format stream-json --verbose --model <model>` run per task and
    profile, with the profile's flags, without saving a session. model runs from your user folder; the
    others from the project folder, where data/ and the skills are. An answer is right when the task's
    regular expression matches it. read_stream() takes the tools Claude called from the assistant events
    and tokens, total_cost_usd (an API-price estimate) and num_turns from the result event. A run
    "computed with code" when it called Bash, PowerShell or a skill. A question longer than 8,000
    characters goes to claude -p through stdin, because a Windows command line holds at most 32,767
    characters (a 3,000-row table pasted into the question is longer). build_command() makes one command;
    summarize() adds up the rows; tasks() defines the questions. write_orders() writes the big table
    (made-up orders, the same every time; a longer table starts with the same rows) and tasks() computes
    its right answers.

WHICH WAY TO REACH CLAUDE
    claude -p only: every run must be a fresh, separate call. The SDK would give the same numbers.

HOW TO RUN  (in cmd, from the project folder, with the venv activated)
    python tools/harness_profile_compare.py --dry-run                     (prints the commands, spends nothing)
    python tools/harness_profile_compare.py --model haiku --runs 2 --tasks small   (7 tasks x 5 profiles x 2 = 70 runs)
    python tools/harness_profile_compare.py --model sonnet --profiles model,lean
    python tools/harness_profile_compare.py --model haiku --runs 3 --tasks big     (the 300-row table: 30 runs)
    python tools/harness_profile_compare.py --model haiku --tasks "word count,big table count"
    python tools/harness_profile_compare.py --model haiku --runs 2 --tasks big --rows 3000 --profiles model,lean_py,full

OPTIONS
    --model NAME        haiku (the default), sonnet, opus, or a full id; the same model for every profile
    --profiles LIST     comma-separated profiles (default: all five)
    --runs N            how often each task runs in each profile (default 1)
    --tasks LIST        comma-separated task names or groups: small (the seven small-file tasks), big
                        (the two on the big table); default: all nine
    --rows N            the number of rows of the big table (default 300)
    --dry-run           print the commands instead of running them

OUTPUT  (real runs on Haiku; first one line per run, then the table)
    python tools/harness_profile_compare.py --model haiku --runs 2 --tasks small
    [lean_py] word count       right  turns=2  tools=Bash  '180'
    ...
    profile    right  ran code  input tokens      cost  cost per right  turns  seconds
    model     14/14      0/14          1,062 $  0.0003         $0.0003    1.0      6.2
    lean      14/14      0/14         16,695 $  0.0006         $0.0006    1.7      6.8
    lean_py   13/14     12/14         24,082 $  0.0007         $0.0007    2.4      8.8
    skills    12/14      5/14         77,749 $  0.0022         $0.0025    2.4      8.6
    full      13/14      6/14         84,911 $  0.0031         $0.0034    2.1      9.9

    python tools/harness_profile_compare.py --model haiku --runs 3 --tasks big
    profile    right  ran code  input tokens      cost  cost per right  turns  seconds
    model      5/6       0/6           3,610 $  0.0038         $0.0046    1.0     25.6
    lean       3/6       6/6          50,184 $  0.0043         $0.0086    4.0     26.9
    lean_py    6/6       6/6          33,914 $  0.0012         $0.0012    3.0     10.3
    skills     6/6       6/6         112,646 $  0.0030         $0.0030    3.0     11.0
    full       6/6       6/6         135,196 $  0.0043         $0.0043    3.3     12.4
    python tools/harness_profile_compare.py --model haiku --runs 2 --tasks big --rows 1000 --profiles model,lean_py,full
    model      3/4       0/4           9,910 $  0.0088         $0.0118    1.0     54.5
    lean_py    4/4       4/4          40,523 $  0.0023         $0.0023    3.0     11.4
    full       4/4       4/4         151,774 $  0.0056         $0.0056    3.2     12.7

    python tools/harness_profile_compare.py --model haiku --runs 2 --tasks big --rows 3000 --profiles model,lean_py,full
    model      1/4       0/4          27,909 $  0.0215         $0.0858    1.0    116.5
    lean_py    3/4       4/4         104,284 $  0.0071         $0.0095    3.5     18.4
    full       4/4       4/4         181,878 $  0.0083         $0.0083    3.5     16.7
    The longer the table, the slower, dearer and less right the plain call; Claude Code stays at 10 to
    18 seconds, under a cent per right answer.
    On small files the plain call is as right and the cheapest; on the 300-row table lean_py is right
    every time at a quarter of the plain call's cost per right answer. lean ran no code on the small
    files, and on the table its awk and PowerShell commands were refused by the python-only allow rule.
    The details of every run, with the tools it called, go to tools/harness_profile_report.json.

NEEDS
    Only the standard library, the data files of this project, and Claude Code 2.1.30x or later.
    Uses some Pro allowance: the full and skills profiles the most.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k harness_profile_compare
       Expected (2 tests; the time differs):
           ..
           ----------------------------------------------------------------------
           Ran 2 tests in 0.005s

           OK
       What they check: the flags of each profile (lean_py's appended rule), that the model profile
       gets the file's text in its question, that the true answers pass every check (and 1403.36
       doesn't), the 300-row table and the task groups, the cost per right answer, the runs that ran
       code, and reading the tools from stream-json. Add -v to see the name of each test.
    2. By hand: free.
           python tools/harness_profile_compare.py --dry-run --profiles model
               seven claude -p commands, each with --tools "", --safe-mode and --max-turns 1
    3. With Claude: uses some Pro allowance.
           python tools/harness_profile_compare.py --model haiku --runs 2 --profiles model,lean_py --tasks big
               Expected: a table with two rows, 4 runs each; lean_py ran code 4/4, is right 4/4 and
               costs less per right answer; model ran code 0/4 and needs far more seconds.

IF SOMETHING GOES WRONG
    - "unknown option '--safe-mode'": update Claude Code (claude update).
    - "The filename or extension is too long" (WinError 206): a question longer than a Windows command
      line; this version sends questions over 8,000 characters through stdin.
    - Every lean_py run is wrong: python is not on the PATH of the window that started the tool;
      activate the venv first.
    - lean answers "Bash was denied": expected. It wrote awk or PowerShell, and the allow rule lets only
      python commands run; lean_py's appended rule is the fix.

FILES IT READS AND WRITES
    Reads data/sales.csv, data/invoice.json and data/article.txt. Writes tools/harness_profile_orders.csv
    (the big table) and tools/harness_profile_report.json (both ignored by git).

SEE ALSO
    tools/model_mode_compare.py (the model-only modes); agent/ask_claude.py --strict; Lesson 6,
    "Three questions: when, how, and how cheaply Claude Code beats a plain model call".
"""

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORT = PROJECT_ROOT / "tools" / "harness_profile_report.json"
ORDERS = "tools/harness_profile_orders.csv"                    # the big table, written by write_orders()
PROFILES = ["model", "lean", "lean_py", "skills", "full"]
ROLE = "You are the reasoning component of a Python agent. Answer exactly, in the format asked for."
PY_RULE = ("Compute every number with Python (python -c or a short script) and answer from its output; "
           "never count, add or round by hand.")
CODE_TOOLS = ("Bash", "PowerShell", "Skill")                   # a run that called one of these computed with code
STDIN_FROM = 8_000                                             # longer questions go through stdin, not the command line
STRICT_ENV = {"CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1", "CLAUDE_CODE_DISABLE_ATTACHMENTS": "1"}
PY_TOOLS = "Read,Bash(python *),PowerShell(python *)"


def orders_rows(rows: int = 300) -> list[tuple[int, str, float]]:
    """Made-up orders, the same every time: (order number, region, amount)."""
    rnd = random.Random(7)
    return [(1001 + i, rnd.choice(["North", "East", "West", "South"]), round(rnd.uniform(20, 900), 2))
            for i in range(rows)]


def write_orders(rows: int = 300) -> None:
    lines = ["order,region,amount"] + [f"{order},{region},{amount:.2f}" for order, region, amount in orders_rows(rows)]
    (PROJECT_ROOT / ORDERS).write_text("\n".join(lines) + "\n", encoding="utf-8")


def thousands(number: int) -> str:
    """A regular expression for a whole number, with or without thousands commas: 1,346 or 1346."""
    whole, groups = str(number), []
    while len(whole) > 3:
        whole, groups = whole[:-3], [whole[-3:]] + groups
    return ",?".join([whole] + groups)


def number_pattern(cents: int) -> str:
    """A regular expression for an amount in cents, with or without thousands commas: 12,345.67 or 12345.67."""
    return thousands(cents // 100) + rf"\.{cents % 100:02d}"


def tasks(rows: int = 300) -> list[dict]:
    """The questions. "file" is pasted into the question for the model profile; the others read it."""
    region_cents = {}
    for _, region, amount in orders_rows(rows):                # whole cents: no float rounding errors
        region_cents[region] = region_cents.get(region, 0) + round(amount * 100)
    over_500 = sum(amount > 500 for _, _, amount in orders_rows(rows))
    return [
        {"group": "small", "name": "region totals", "file": "data/sales.csv",
         "question": "What is the total amount per region in data/sales.csv? Answer as region=total, separated by commas.",
         "expect": r"(?s)(?=.*North\D{0,6}2,?150)(?=.*East\D{0,6}910)(?=.*West\D{0,6}900)(?=.*South\D{0,6}670)"},
        {"group": "small", "name": "average amount", "file": "data/sales.csv",
         "question": "What is the average amount per row in data/sales.csv, rounded to 2 decimals? Answer with the number only.",
         "expect": r"^\D*385\.83\D*$"},
        {"group": "small", "name": "most units", "file": "data/sales.csv",
         "question": "Which product sold the most units in data/sales.csv? Skip the row without units. Answer with the product name only.",
         "expect": r"(?i)^\W*widgets?\W*$"},
        {"group": "small", "name": "invoice total", "file": "data/invoice.json",
         "question": "What is the grand total of the invoice in data/invoice.json: the line amounts, minus the discount, "
                     "plus the tax on the discounted amount, each rounded to cents? Answer with the number only.",
         "expect": r"^\D*1,?403\.37\D*$"},
        {"group": "small", "name": "word count", "file": "data/article.txt",
         "question": "How many words are in data/article.txt, including its title line? A word is a run of letters; an "
                     "apostrophe inside it belongs to it, and a hyphen splits it in two. Answer with the number only.",
         "expect": r"^\D*\b180\b\D*$"},
        {"group": "small", "name": "working days", "file": None,
         "question": "How many working days (Monday to Friday) are there from 2026-12-21 to 2027-01-08, both included, if "
                     "2026-12-24, 2026-12-25, 2026-12-31 and 2027-01-01 are holidays? Answer with the number only.",
         "expect": r"^\D*\b11\b\D*$"},
        {"group": "small", "name": "logic (control)", "file": None,
         "question": "Anna is older than Ben. Ben is older than Carl. Who is the youngest? Answer with the name only.",
         "expect": r"(?i)^\W*carl\W*$"},
        {"group": "big", "name": "big table totals", "file": ORDERS,
         "question": f"What is the total amount per region in {ORDERS}, to the cent? Answer as region=total, "
                     "separated by commas.",
         "expect": "(?s)" + "".join(rf"(?=.*{region}\D{{0,6}}{number_pattern(cents)})"
                                    for region, cents in region_cents.items())},
        {"group": "big", "name": "big table count", "file": ORDERS,
         "question": f"How many orders in {ORDERS} have an amount over 500? Answer with the number only.",
         "expect": rf"^\D*\b{thousands(over_500)}\b\D*$"},
    ]


def choose_tasks(spec: str, rows: int = 300) -> list[dict]:
    """The tasks named in spec (comma-separated names or groups); all of them when spec is empty."""
    wanted = {w.strip() for w in spec.split(",") if w.strip()}
    return [t for t in tasks(rows) if not wanted or t["name"] in wanted or t["group"] in wanted]


def question_for(task: dict, profile: str) -> str:
    """The model profile gets the file's text in the question; the others read the file themselves."""
    if profile != "model" or not task["file"]:
        return task["question"]
    if task["file"] == ORDERS and not (PROJECT_ROOT / ORDERS).exists():
        write_orders()
    text = (PROJECT_ROOT / task["file"]).read_text(encoding="utf-8")
    return f"{task['question']}\n\nThis is the content of {task['file']}:\n<file>\n{text}\n</file>"


def build_command(claude: str, prompt: str, model: str, profile: str) -> tuple[list[str], dict, Path]:
    """The claude -p command, the extra environment variables and the folder to run it in, for one profile."""
    cmd = [claude, "-p", prompt, "--model", model, "--output-format", "stream-json", "--verbose",
           "--no-session-persistence", "--permission-mode", "dontAsk"]  # anything not allowed is refused, never asked
    if profile == "model":
        return cmd + ["--tools", "", "--system-prompt", ROLE, "--disable-slash-commands", "--strict-mcp-config",
                      "--setting-sources", "", "--safe-mode", "--max-turns", "1"], dict(STRICT_ENV), Path.home()
    if profile in ("lean", "lean_py"):                         # Claude Code's prompt and loop, few tools
        rule = ["--append-system-prompt", PY_RULE] if profile == "lean_py" else []
        return cmd + ["--tools", "Read,Bash,PowerShell", "--allowedTools", PY_TOOLS, "--disable-slash-commands",
                      "--strict-mcp-config", "--safe-mode", "--max-turns", "6"] + rule, {}, PROJECT_ROOT
    if profile == "skills":                                    # the course's agent
        return cmd + ["--allowedTools", "Skill," + PY_TOOLS, "--setting-sources", "project",
                      "--strict-mcp-config", "--max-turns", "8"], {}, PROJECT_ROOT
    if profile == "full":                                      # everything Claude Code loads by default
        return cmd + ["--allowedTools", "Skill," + PY_TOOLS, "--max-turns", "8"], {}, PROJECT_ROOT
    raise ValueError(f"unknown profile {profile!r}; use one of {PROFILES}")


def read_stream(text: str) -> tuple[dict, list[str]]:
    """The result event and the names of the tools Claude called, from stream-json output."""
    result, tools = {}, []
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            for block in event["message"].get("content") or []:
                if block.get("type") == "tool_use":            # a skill call also names the skill
                    skill = block["input"].get("skill") if block["name"] == "Skill" else None
                    tools.append(f"Skill:{skill}" if skill else block["name"])
        elif event.get("type") == "result":
            result = event
    return result, tools


def split_long_prompt(cmd: list[str], prompt: str) -> tuple[list[str], str | None]:
    """The command and the text for stdin: a long prompt leaves the command line, claude -p reads it from stdin."""
    if len(prompt) <= STDIN_FROM:
        return cmd, None
    return cmd[:2] + cmd[3:], prompt                           # cmd[2] is the prompt, right after -p


def run_one(claude: str, task: dict, model: str, profile: str) -> dict:
    prompt = question_for(task, profile)
    cmd, extra_env, folder = build_command(claude, prompt, model, profile)
    cmd, stdin_text = split_long_prompt(cmd, prompt)
    started = time.perf_counter()
    proc = subprocess.run(cmd, input=stdin_text, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=folder, env={**os.environ, **extra_env})
    seconds = time.perf_counter() - started
    data, tools = read_stream(proc.stdout)
    row = {"profile": profile, "task": task["name"], "seconds": seconds, "tools": tools}
    if not data:
        return {**row, "answer": None, "right": False, "cost": 0.0, "error": (proc.stderr or proc.stdout)[:300]}
    usage = data.get("usage") or {}
    answer = (data.get("result") or "").strip()
    return {**row, "answer": answer,
            "right": bool(re.search(task["expect"], answer)) and not data.get("is_error"),
            "input_tokens": usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
                            + usage.get("cache_read_input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cost": data.get("total_cost_usd") or 0.0, "turns": data.get("num_turns"),
            "models": list(data.get("modelUsage") or {})}


def summarize(rows: list[dict], profiles: list[str]) -> list[dict]:
    """One line per profile. Cost per right answer = all the cost of the profile / its right answers."""
    out = []
    for profile in profiles:
        mine = [r for r in rows if r["profile"] == profile]
        n, right = len(mine) or 1, sum(r["right"] for r in mine)
        cost = sum(r.get("cost", 0.0) for r in mine)
        code = sum(any(t.split(":")[0] in CODE_TOOLS for t in r.get("tools") or []) for r in mine)
        out.append({"profile": profile, "right": right, "runs": len(mine), "code": code,
                    "input_tokens": sum(r.get("input_tokens", 0) for r in mine) / n,
                    "cost": cost / n, "cost_per_right": cost / right if right else None,
                    "turns": sum(r.get("turns") or 0 for r in mine) / n,
                    "seconds": sum(r["seconds"] for r in mine) / n})
    return out


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Non-coding data tasks: Claude Code as the model against Claude Code with tools.")
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--profiles", default=",".join(PROFILES))
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--tasks", default="")
    parser.add_argument("--rows", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]
    chosen = choose_tasks(args.tasks, args.rows)
    claude = shutil.which("claude") or "claude"

    if args.dry_run:
        for profile in profiles:
            for task in chosen:
                cmd, env, folder = build_command(claude, task["question"], args.model, profile)
                prefix = "".join(f"set {k}={v} && " for k, v in env.items())
                print(f"[{profile} in {folder}] " + prefix + " ".join(f'"{c}"' if (" " in c or not c) else c for c in cmd))
        return 0

    write_orders(args.rows)
    rows = []
    for run in range(args.runs):
        for profile in profiles:
            for task in chosen:
                row = run_one(claude, task, args.model, profile)
                rows.append(row)
                mark = "right" if row["right"] else "WRONG"
                print(f"[{profile:7}] {task['name']:16} {mark}  turns={row.get('turns')}  "
                      f"tools={','.join(row['tools']) or '-'}  {str(row.get('answer'))[:40]!r}")
    table = f", big table of {args.rows} rows" if any(t["group"] == "big" for t in chosen) else ""
    print(f"\nModel: {args.model}, {len(chosen)} tasks{table}, {args.runs} run(s) per profile\n")
    print(f"{'profile':8} {'right':>7} {'ran code':>9} {'input tokens':>13} {'cost':>9} {'cost per right':>15} "
          f"{'turns':>6} {'seconds':>8}")
    for s in summarize(rows, profiles):
        per_right = f"${s['cost_per_right']:.4f}" if s["cost_per_right"] is not None else "-"
        print(f"{s['profile']:8} {s['right']:>3}/{s['runs']:<3} {s['code']:>5}/{s['runs']:<3} {s['input_tokens']:>13,.0f} "
              f"${s['cost']:>8.4f} {per_right:>15} {s['turns']:>6.1f} {s['seconds']:>8.1f}")
    REPORT.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDetails: {REPORT.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
