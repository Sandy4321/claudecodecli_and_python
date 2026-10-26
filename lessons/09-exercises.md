# Lesson 9 - Exercises

**Goal:** practice everything from Lessons 1 to 8 on your own. Each exercise says what you will
learn, why it matters, the steps, the result to expect, and what to do if you see something else.

**Before every exercise:** start the usual way (Lesson 0, "Start here"): activate the venv, and
`cd /d "E:\may10\claudecodecli_and_python"`.

**After every exercise,** run the two free checks in cmd. They show at once if a change broke a
skill file or a script (Lesson 5 explains both):

```bat
python tools/skills_lint.py
```

```bat
python -m unittest discover -s tests
```

**Expected result:** `9 skills, 0 error(s).` and `Ran 74 tests ... OK`. If you want, also run the
real routing test. It uses a little of your Pro allowance:

```bat
python tools/routing_eval.py --limit 6
```

## 1. Watch routing happen (5 min)

**You learn:** that Claude chooses by meaning, not by exact words (Lesson 2).

**Why:** people never type a request the same way twice. A good description must work for all forms.

**Steps:** in `claude`, ask the same thing in three ways. Each time, note which skill appears with the
**Skill** tool:

- `How long is a 10k race in miles?`
- `10 km → mi`
- `Is a 10k longer than 6 miles?`

Then ask something that needs **no** skill: `Explain what a kilometer is`.

**Expected result:** most likely `converting-units` for all three, with a `python ... convert.py
convert 10 km mi` command, and about 6.21 miles. The last question gets **no** skill: it asks for an
explanation, not a conversion.

**If you see something else:** if one of the three gets no skill, Claude answered from memory. Note
which form it was. It is a good candidate for a test question in `tools\routing_cases.json` (Lesson 5).

## 2. Break a description, then fix it (10 min)

**You learn:** how much the choice depends on the description, and what the free tools say about a
bad one.

**Why:** you will write descriptions yourself. Seeing a bad one fail makes the rules of Lesson 2,
Step 5 concrete.

**Steps:**

1. Open `.claude\skills\converting-units\SKILL.md` in Notepad. Replace the whole description line
   with `description: Helps with numbers.` and save.
2. Run the linter:
   ```bat
   python tools/skills_lint.py
   ```
3. Run the preview:
   ```bat
   python tools/route_preview.py "convert 5 kg to lb"
   ```
4. Optional (uses allowance): `python tools/routing_eval.py --limit 3`.
5. Put the original description back (copy it from Lesson 1, Step 3), save, and run the linter again.

**Expected result** (real runs):

Step 2, the linter:

```text
[check] converting-units  (auto + /command, description 19 chars)
   WARN  Add a trigger clause such as 'Use when the user asks ...' so Claude knows WHEN to pick it.
```

Step 3, the preview:

```text
   2.77  converting-units       shared words: convert
   0.00  tracking-todos         shared words: -
   0.00  plotting-charts        shared words: -
```

**How to read it:** the linter warns: no "Use when ..." sentence. The preview still puts
`converting-units` first, but only because of the word "convert" in the skill's **name**
(`converting-units`). "kg", "lb" and every other unit are gone. A request like `How heavy is 5 kg
in pounds?` would now share no word at all. Step 4 shows what Claude does. Results can vary,
because the name alone still says a lot.

**Your answer:** in one sentence, explain why the vague description fails. (It doesn't say what the
skill does, with which units, or when to use it.)

## 3. Create a collision on purpose (15 min)

**You learn:** what happens when two skills compete for the same requests, and how the linter
detects it.

**Why:** with many skills, this is the most common problem (Lesson 4, Step 2).

**Steps:**

1. Create the folder `.claude\skills\summarizing-tables\`, and in it a file `SKILL.md` with this
   text. It is a second skill for the same job as `analyzing-csv`:
   ```markdown
   ---
   name: summarizing-tables
   description: Summarizes tables in CSV files - totals, averages and top rows of a column. Use when the user asks about totals, averages or rankings in a CSV file.
   ---

   # Summarizing tables
   ```
2. Run the linter:
   ```bat
   python tools/skills_lint.py
   ```
3. Add a test question that both skills could take to `tools\routing_cases.json`. Add it as a new
   line before the last `]` (don't forget the comma at the end of the line before it):
   ```json
   {"prompt": "What is the average amount in data/sales.csv?", "expect": "analyzing-csv"}
   ```
4. Optional (uses allowance): `python tools/routing_eval.py`. With the collision, Claude may choose
   `summarizing-tables`, which has no script.
5. Fix the collision. Here the jobs are the same, so **merge**: delete the extra skill
   (`rmdir /s /q .claude\skills\summarizing-tables`). Run the linter again.

**Expected result** (a real run of Step 2):

```text
[ok] summarizing-tables  (auto + /command, description 148 chars)
...
Description overlap (pairs that may compete for the same request):
   WARN  analyzing-csv <-> summarizing-tables: 0.38 shared words ['average', 'column', 'csv', 'file', 'ranking', 'rows', 'summarize', 'top', 'total']

10 skills, 0 error(s).
```

**How to read it:** the new skill itself is `[ok]`: its file is correct. The problem is the pair:
0.38 means 38% of their important words are shared (the warning starts at 0.30). After Step 5, you
see `none above 0.30` and `9 skills, 0 error(s)` again. Keep the new test question: it guards against
the same mistake later.

**If you see something else:** `9 skills` instead of `10` in Step 2 means the new SKILL.md is not in
the right folder, or its first line is not `---`.

## 4. Add a new skill with a Python function library (30 min)

**You learn:** to build a complete skill with a Python script, from an empty folder to a tested
skill (Lessons 3 and 5).

**Why:** this is the main goal of the course: your own Python functions, used by Claude.

**The task:** a skill that answers `What is my monthly payment for a $250,000 mortgage at 6% over 30 years?`

**Steps:**

1. Create the folder `.claude\skills\calculating-loans\scripts\`.
2. Copy `fncli.py` into it (Pattern B, Lesson 3):
   ```bat
   copy .claude\skills\calculating-dates\scripts\fncli.py .claude\skills\calculating-loans\scripts\
   ```
3. Write `scripts\loans.py` with two typed functions, and end it with `fncli.run([...])`, as in
   `dates.py`:
   - `monthly_payment(principal: float, annual_rate_pct: float, years: int) -> dict`
   - `total_interest(principal: float, annual_rate_pct: float, years: int) -> dict`

   The formula is `principal * r / (1 - (1 + r) ** -n)`, with `r = annual_rate_pct / 100 / 12`
   (the rate per month) and `n = years * 12` (the number of months).
4. Write `SKILL.md`:
   - a description: what it does, a "Use when ..." sentence, and as the last sentence
     "Not for invoices or quotes (use calculating-invoices)."
   - `allowed-tools` with `Bash(python *)` and `PowerShell(python *)`
   - a table of commands, with the path in quotes: `"${CLAUDE_SKILL_DIR}/scripts/loans.py"`
   - careful: write dollar amounts as `\$250,000`. A bare `$2` would be replaced by an argument
     (Lesson 2, Step 4).
5. Add unit tests in a new file `tests\test_loans.py`.
6. Add 3 test questions to `tools\routing_cases.json`: two that must go to `calculating-loans`, and
   one borderline question that must go to `calculating-invoices`, for example
   `Make me a quote: 2 laptops at 1200 each plus 20% VAT.`

**Try it first yourself.** Then compare with the solution below.

**Solution, `scripts\loans.py`:**

```python
"""Loan arithmetic: monthly payment and total interest of a fixed-rate loan."""

import fncli


def monthly_payment(principal: float, annual_rate_pct: float, years: int) -> dict:
    """Monthly payment of a fixed-rate loan (annuity formula)."""
    if principal <= 0 or years <= 0 or annual_rate_pct < 0:
        raise ValueError("principal and years must be > 0, annual_rate_pct must be >= 0")
    r, n = annual_rate_pct / 100 / 12, years * 12
    payment = principal / n if r == 0 else principal * r / (1 - (1 + r) ** -n)
    return {"principal": principal, "annual_rate_pct": annual_rate_pct, "years": years,
            "months": n, "monthly_payment": round(payment, 2)}


def total_interest(principal: float, annual_rate_pct: float, years: int) -> dict:
    """Total interest paid over the whole loan."""
    m = monthly_payment(principal, annual_rate_pct, years)
    paid = m["monthly_payment"] * m["months"]
    return {**m, "total_paid": round(paid, 2), "total_interest": round(paid - principal, 2)}


if __name__ == "__main__":
    fncli.run([monthly_payment, total_interest])
```

**Why it is written this way:**

- The `ValueError` becomes a JSON error with the right call (Lesson 3, Step B3), so Claude can fix
  a wrong call by itself.
- `r == 0` is handled separately: the formula would divide by zero for a 0% loan.
- `total_interest` reuses `monthly_payment`, so the two can never disagree.

**Solution, `SKILL.md`:**

````markdown
---
name: calculating-loans
description: Calculates fixed-rate loans and mortgages - the monthly payment, the total amount paid, and the total interest for a principal, an annual interest rate and a term in years. Use when the user asks about a mortgage, loan or car-loan payment, or how much interest a loan costs. Not for invoices or quotes (use calculating-invoices).
allowed-tools:
  - Bash(python *)
  - PowerShell(python *)
---

# Calculating loans

Never do loan math in your head. Run the script.

| Question | Command |
|---|---|
| Monthly payment | `python "${CLAUDE_SKILL_DIR}/scripts/loans.py" monthly_payment --principal 250000 --annual_rate_pct 6 --years 30` |
| Total interest | `python "${CLAUDE_SKILL_DIR}/scripts/loans.py" total_interest --principal 250000 --annual_rate_pct 6 --years 30` |

Write amounts without `\$` and commas: 250000, not \$250,000. Report `monthly_payment` and
`total_interest` as printed, in the user's currency.
````

**Solution, `tests\test_loans.py`:**

```python
import unittest

from test_skill_scripts import cli, load      # the helpers of the course's test file


class CalculatingLoans(unittest.TestCase):
    loans = load("calculating-loans", "loans.py")

    def test_monthly_payment(self):
        self.assertEqual(self.loans.monthly_payment(250000, 6, 30)["monthly_payment"], 1498.88)

    def test_cli_total_interest(self):
        code, out = cli("calculating-loans", "loans.py", "total_interest",
                        "--principal", "250000", "--annual_rate_pct", "6", "--years", "30")
        self.assertEqual((code, out["total_interest"]), (0, 289596.8))
```

One test calls the function, and one runs the command exactly as Claude does (Lesson 5, Step 3).

**Check it,** in this order:

```bat
python .claude/skills/calculating-loans/scripts/loans.py monthly_payment --principal 250000 --annual_rate_pct 6 --years 30
```

```text
{"principal": 250000.0, "annual_rate_pct": 6.0, "years": 30, "months": 360, "monthly_payment": 1498.88}
```

```bat
python -m unittest discover -s tests -k CalculatingLoans -v
```

```text
test_cli_total_interest (test_loans.CalculatingLoans.test_cli_total_interest) ... ok
test_monthly_payment (test_loans.CalculatingLoans.test_monthly_payment) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.181s

OK
```

```bat
python tools/skills_lint.py
```

**Expected result:** `[ok] calculating-loans ...`, no overlap warning, and `10 skills, 0 error(s).`
Then start `claude` and ask the mortgage question: you should see the Skill tool with
`calculating-loans`, and about 1,498.88 per month.

**If you see something else:** `ModuleNotFoundError: No module named 'fncli'` means `fncli.py` is not
in the `scripts` folder (step 2). After this exercise, the test counts in the other lessons are 2
higher (76), and the linter says 10 skills. Keep the skill, or delete the folder and `tests\test_loans.py`.

## 5. Make a skill file-aware (10 min)

**You learn:** the `paths:` setting, which limits **automatic** use of a skill to work with
matching files.

**Why:** a skill that only makes sense for certain files then stays out of the way for everything else.

**Steps:**

1. Add this to the frontmatter of `.claude\skills\analyzing-csv\SKILL.md` (before the closing `---`):
   ```yaml
   paths:
     - "**/*.csv"
   ```
   `**` means "any folder, at any depth", and `*.csv` means "any file whose name ends in .csv".
2. Start `claude` again (skills are read at the start of a session), and ask
   `Which region sold the most in data/sales.csv?`.
3. Think about it: which requests could now **no longer** reach the skill by themselves?
4. Remove the `paths:` lines again. This project uses descriptions only.

**Expected result:** in Step 2, the skill is still chosen, because a .csv file is involved. The answer
to Step 3: for example CSV text pasted straight into the chat, with no file. You can always start the
skill yourself with `/analyzing-csv`.

## 6. Run a big reading job in a subagent (15 min)

**You learn:** `context: fork`, which runs a skill in a helper Claude with its own context window
(Lesson 4, Step 5).

**Why:** reading many files fills your conversation, and every later message gets slower and more
expensive. A subagent keeps your conversation small.

**Steps:**

1. Create the file `.claude\skills\summarizing-project\SKILL.md` with this content:
   ```markdown
   ---
   name: summarizing-project
   description: Reads all lesson files of this course and returns a 10-line summary. Use when the user asks for a summary or overview of the course lessons.
   context: fork
   agent: Explore
   background: false
   ---

   Read every file in the lessons folder. Then write a summary of the whole course in exactly
   10 lines, one main idea per line. Return only the summary.
   ```

   | Line | What it does |
   |---|---|
   | `context: fork` | runs the skill in a subagent. The text below the frontmatter becomes the subagent's task |
   | `agent: Explore` | uses the built-in helper that can read files but not change them |
   | `background: false` | makes Claude wait for the result before it continues (needs Claude Code 2.1.218 or later; check with `claude --version`) |

2. Start `claude`, and type `/context`. It shows how full the context window is and what fills it.
   Note the number.
3. Type `/summarizing-project`. Wait for the 10-line summary.
4. Type `/context` again.
5. Optional: start a new session, ask `Read all files in the lessons folder and summarize them`
   **without** the skill, and compare `/context` afterwards.

**Expected result:** in Step 4, the context grew only by the short summary, not by all 9 lesson files.
The subagent read them in its own context window. In Step 5, the context grows much more.

**Clean up:** `rmdir /s /q .claude\skills\summarizing-project`.

## 7. Specialized agents from the same skills (15 min)

**You learn:** to make agents with different skill sets from one project, and the limits of the
`skills` list (Lesson 6, Step 6).

**Why:** a real agent program usually needs only some skills.

**Steps:**

1. Make a "finance agent" that knows only invoices and dates:
   ```bat
   python agent\run_agent.py --model haiku --skills calculating-invoices,calculating-dates "What weekday is 2026-12-25 and convert 5 km to miles"
   ```
2. Make a "data agent" that knows only CSV, text and units:
   ```bat
   python agent\run_agent.py --model haiku --skills analyzing-csv,analyzing-text,converting-units "What weekday is 2026-12-25 and convert 5 km to miles"
   ```
3. Look at the `[skill]` and `[tool]` lines. Run each one twice.

**Expected result:** the finance agent uses `calculating-dates` for the weekday (Friday), and the data
agent uses `converting-units` for the miles (about 3.11). For the part without an offered skill, the
agent may answer from its own knowledge. Or it reads the hidden skill's `SKILL.md` with its Read tool,
and runs the script anyway. Lesson 6, Step 6 explains why: the list is not a lock.

## 8. A rule that can't be skipped: a hook (stretch)

**You learn:** hooks, the way to enforce a rule that Claude can't skip (Lesson 4, Step 6).

**Why:** a sentence in a SKILL.md is advice. Claude usually follows it, but not always. Claude Code
itself enforces a hook.

**The goal:** make it impossible for Claude's Write and Edit tools to change any file outside `data\`.

**How it works:** a hook is a command that Claude Code itself runs at a certain moment. Here the
moment is `PreToolUse`: just **before** a tool runs. Claude Code sends the planned tool call to your
command as JSON on stdin, for example
`{"tool_name": "Write", "tool_input": {"file_path": "E:\\...\\notes.txt", ...}, "cwd": "E:\\may10\\claudecodecli_and_python", ...}`.

| Your command ends with | Claude Code then |
|---|---|
| exit code **2** | blocks the tool call, and shows Claude the text your command printed on stderr |
| exit code **0** | runs the tool call normally |

The hook script is ready in the project: [`tools/hooks/only_data_folder.py`](../tools/hooks/only_data_folder.py).

```python
event = json.load(sys.stdin)                      # Claude Code sends the planned tool call as JSON
target = Path(event["tool_input"].get("file_path", ""))
allowed = Path(event["cwd"]) / "data"
try:
    target.resolve().relative_to(allowed.resolve())
except ValueError:
    print(f"Blocked by hook: files may only be written inside {allowed}", file=sys.stderr)
    sys.exit(2)                                   # exit code 2 = block the tool call
sys.exit(0)                                       # exit code 0 = allow it
```

`resolve()` turns the path into a full path. `relative_to` raises a `ValueError` when the target file
is not inside the `data` folder. In that case the script blocks the call.

**Steps:**

1. Create the file `.claude\settings.json` in the project, with this content. It switches the hook on
   for the Write and Edit tools:
   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Write|Edit",
           "hooks": [
             { "type": "command", "command": "python tools/hooks/only_data_folder.py" }
           ]
         }
       ]
     }
   }
   ```
   `"matcher": "Write|Edit"` means: run the hook only before the Write or the Edit tool.
2. Exit and start `claude` again, so the new setting is loaded.
3. Ask: `Create a file test.txt in the project folder with the text hi`.
4. Ask: `Create the file data/test.txt with the text hi`. Then delete `data\test.txt`.
5. Think about it:
   - Why is a hook better than the sentence "only write in data/" in a SKILL.md?
   - Which file changes does this hook **not** stop?
6. Delete `.claude\settings.json` again. Otherwise Claude also can't edit the lessons or skills for you.

**Expected result** (tested on the course machine): in Step 3, the hook blocks the write, and Claude
reports `Blocked by hook: files may only be written inside ...\data`. In Step 4, the write is allowed.

**The answers to Step 5:** a hook runs every time, and the model can't skip or forget it. It doesn't
stop a Python script started with the Bash or PowerShell tool. That script can still write anywhere,
because the hook checks only the tools in its `matcher`.

**If you see something else:** if the write in Step 3 is not blocked, Claude Code didn't load the
setting. Check that the file is `.claude\settings.json` (not `.txt`), and that you restarted `claude`.
