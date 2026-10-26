# Lesson 5 - Testing skills that run Python

**Goal:** learn what can go wrong in a skill with Python code, and which test catches each problem.
Then learn how to run each test, and how to read its result, including a failure.

**Before you start:** open cmd, `C:\pyenvsmy\claudeclioct26\Scripts\activate`, and
`cd /d "E:\may10\claudecodecli_and_python"`.

## Why test at all?

A skill with Python code has four parts, and each one can go wrong in its own way:

| Part | What can go wrong | What you notice in Claude | The test that catches it | Cost |
|---|---|---|---|---|
| The Python script | it computes a wrong number | Claude tells you the wrong number, confidently | **1. Unit tests** | free |
| The `SKILL.md` file | a wrong name, a missing description, a script path that doesn't exist | the skill is never chosen, or fails, without a clear message | **2. Linter** | free |
| The description's words | it lacks the words people type | Claude doesn't choose the skill | **3. Preview** (a rough guess) | free |
| Claude's choice | Claude chooses another skill, or none | the wrong skill answers | **4. Routing test** | a little Pro allowance |

Run the free tests 1 to 3 first, every time you change something. Run test 4 when they all pass.

## Test 1 - Unit tests: does the Python code compute correctly?

### Step 1 - Run all unit tests

**What:** `tests\test_skill_scripts.py` contains 74 unit tests. Each one runs one function of a skill
script with a known input, and checks that the result is exactly the expected one.

**Why:** Claude trusts what a script prints. The unit tests make sure the scripts are right, so that
Claude repeats right answers. They don't contact Claude, so they are free.

**Run:**

```bat
python -m unittest discover -s tests
```

**How it works:** `-m unittest` starts Python's built-in test runner. `discover` searches a folder for
test files, and `-s tests` says which folder: `tests`. The runner opens every file named `test_*.py`
there, and runs every function whose name starts with `test_`.

**Expected result:**

```text
..........................................................................
----------------------------------------------------------------------
Ran 74 tests in 31.351s

OK
```

**How to read it:**

- Each `.` is one passed test. While the tests run, you see the dots appear one by one.
- `Ran 74 tests in 31.351s`: how many tests ran, and how long they took. The time doesn't matter.
- `OK`: **every** test passed.

**If you see something else:**

| You see | Meaning | What to do |
|---|---|---|
| `F` among the dots, `FAILED (failures=1)` | a test got a wrong result | read the `FAIL:` block (Step 2) |
| `E` among the dots, `FAILED (errors=1)` | a test or a script crashed | read the `ERROR:` block. Its last line is the error message |
| `OK (skipped=6)` | the 6 tests that need pandas (Excel, charts, the sample workbook) were skipped | activate the venv (Lesson 0) and run again |

### Step 2 - Learn to read a failure (do it yourself)

**What:** you break the conversion script on purpose, see the tests fail, and read the failure.

**Why:** a failure report looks frightening the first time. After reading one carefully, you can
read any of them.

**Do:**

1. Open `.claude\skills\converting-units\scripts\convert.py` in Notepad.
2. Find line 88. Among other units it contains `"mi": 1609.344` (one mile is 1609.344 meters).
3. Change only that number to `1600.0` (a wrong value), so the text becomes `"mi": 1600.0`. Save the file.

**Run:** (`-k ConvertingUnits` runs only the tests of the conversion script; Step 4 explains `-k`)

```bat
python -m unittest discover -s tests -k ConvertingUnits
```

**Expected result** (a real run):

```text
..F.F
======================================================================
FAIL: test_cli (test_skill_scripts.ConvertingUnits.test_cli)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "E:\may10\claudecodecli_and_python\tests\test_skill_scripts.py", line 136, in test_cli
    self.assertEqual((code, out["result"]), (0, 1.609344))
AssertionError: Tuples differ: (0, 1.6) != (0, 1.609344)
...
======================================================================
FAIL: test_length (test_skill_scripts.ConvertingUnits.test_length)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "E:\may10\claudecodecli_and_python\tests\test_skill_scripts.py", line 119, in test_length
    self.assertAlmostEqual(self.convert.convert(100, "km", "mi")["result"], 62.137119, places=5)
AssertionError: 62.5 != 62.137119 within 5 places (0.36288100000000156 difference)

----------------------------------------------------------------------
Ran 5 tests in 0.152s

FAILED (failures=2)
```

**How to read it,** from top to bottom:

1. **`..F.F`:** 5 tests ran. Tests 3 and 5 failed (`F`), and the others passed (`.`).
2. **`FAIL: test_length (...ConvertingUnits.test_length)`:** the name of the failed test.
3. **`File "...test_skill_scripts.py", line 119`:** where the failed check is. The line below shows it:
   the test converts 100 km to miles and expects `62.137119`.
4. **`AssertionError: 62.5 != 62.137119`:** the most important line. The script returned **62.5**,
   but the right answer is **62.137119**. "Assertion" means "a check that must be true".
5. **`test_cli`** failed too. It runs the script **as a command**, exactly as Claude does. The
   command printed `1.6` instead of `1.609344` for 1 mile in km.

So the report tells you **which** test failed, **where** the check is, and **what** came out instead
of what. The cause is your wrong mile value.

**Now fix it:** change the number back to `1609.344`, save, and run the same command again.

**Expected result:**

```text
.....
----------------------------------------------------------------------
Ran 5 tests in 0.318s

OK
```

**A second real example.** On the course machine, one test once failed like this:

```text
FAIL: test_skill_sizes_reports_levels (test_skill_scripts.TutorialTools.test_skill_sizes_reports_levels)
  File "E:\may10\claudecodecli_and_python\tests\test_skill_scripts.py", line 291, in test_skill_sizes_reports_levels
    self.assertEqual(proc.returncode, 0)
AssertionError: 1 != 0
```

Read it the same way. The test runs `tools\skill_sizes.py` and expects **exit code 0** (success).
The program ended with **exit code 1** (an error). The cause: Python had saved compiled files
(`__pycache__\*.pyc`) in the skill folders, and the tool tried to read them as text. The tool was
fixed to skip them. The test now also prints the tool's error message when it fails, so the cause is
visible directly in the report.

### Step 3 - Look inside a test

**What:** two of the conversion tests, from `tests\test_skill_scripts.py`.

**Why:** when you write your own skill script, you write tests like these for it.

```python
class ConvertingUnits(unittest.TestCase):
    convert = load("converting-units", "convert.py")      # import the skill's script

    def test_length(self):
        # call the function directly, and check the result
        self.assertAlmostEqual(self.convert.convert(100, "km", "mi")["result"], 62.137119, places=5)

    def test_cli(self):
        # run the script as a command, exactly as Claude does, and check the JSON it prints
        code, out = cli("converting-units", "convert.py", "convert", "1", "mi", "km")
        self.assertEqual((code, out["result"]), (0, 1.609344))
```

**How it works:**

- `class ConvertingUnits(unittest.TestCase)` is a group of tests for one script.
- `load(...)` imports the skill script, so the test can call its functions.
- `test_length` calls the function `convert(100, "km", "mi")` and checks the result.
  `assertAlmostEqual(..., places=5)` accepts tiny rounding differences after the 5th decimal place.
- `test_cli` runs `python convert.py convert 1 mi km` as a separate program, reads the JSON it
  prints, and checks the exit code (`0`) and the result (`1.609344`). This tests the command
  **exactly the way Claude uses it**.

Write both kinds for every skill script: one that tests the function, and one that tests the command.

### Step 4 - Run only some tests, and see their names

**What:** `-k` runs only the tests whose name contains a word, and `-v` ("verbose") prints one line per test.

**Why:** when you work on one script, you only need its tests. That is faster, and the names show
you what is being checked.

**Run:**

```bat
python -m unittest discover -s tests -k ConvertingUnits -v
```

**Expected result:**

```text
test_aliases_and_temperature (test_skill_scripts.ConvertingUnits.test_aliases_and_temperature) ... ok
test_binary_data_units (test_skill_scripts.ConvertingUnits.test_binary_data_units) ... ok
test_cli (test_skill_scripts.ConvertingUnits.test_cli) ... ok
test_errors_explain_the_fix (test_skill_scripts.ConvertingUnits.test_errors_explain_the_fix) ... ok
test_length (test_skill_scripts.ConvertingUnits.test_length) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.318s

OK
```

**How to read it:** each line is `test name (file.group.test name) ... result`. The names say what is
checked. For example, `test_errors_explain_the_fix` checks that a wrong unit gives an error message
with a hint, the way Claude needs it.

The test groups in the file, to use with `-k`:

| `-k` word | What it tests | Tests |
|---|---|---|
| `ConvertingUnits` | `convert.py`: lengths, temperatures, data sizes, error hints, the command | 5 |
| `AnalyzingCsv` | `csv_tool.py`: summary, totals per group, top rows, wrong column names | 4 |
| `CalculatingDates` | `dates.py`: working days, ages, calling functions by name, wrong dates | 5 |
| `AnalyzingText` | `text_stats.py`: counting words and sentences, frequent words, text from a pipe | 4 |
| `CalculatingInvoices` | `invoice.py`: totals with cent rounding, the 5 problems of the broken invoice, the document | 3 |
| `TrackingTodos` | `todo.py`: add, list, done, clear, wrong priority (with a temporary list, never your real one) | 2 |
| `PackageSkills` | `excel_tool.py`, `chart.py` and `tools\make_sample_xlsx.py` (need the venv) | 6 |
| `WrongInterpreter` | the helpful message when the venv is not active | 1 |
| `TutorialTools` | the tools in `tools\`: linter, preview, skill sizes, `skilllib.py`, the hook of Lesson 9, `show_sdk_command.py` | 10 |
| `CalculatingMath` | `examples\skills\calculating-math\scripts\calc.py`: the strict calculator of Lesson 8 | 5 |
| `AgentGuard` | `agent\guard.py`: which tool calls `guarded_agent.py` allows (Lesson 6, Part 4) | 5 |
| `AskClaudeCommand` | `agent\ask_claude.py`: the `claude -p` command it builds, `--effort`, thinking tokens, the flags of `--strict` (Lesson 6, Part 5); `tools\run_cost.py`: the steps of a run (Part 6) | 5 |
| `BothWays` | the `claude -p` way (`--cli`) of the agent programs: their commands, the hook scripts `guard_hook.py` and `effort_hook.py`, and the tool server `tutor_mcp_server.py`. Also the routing rules that both ways of `routing_eval.py` share, the SDK options of `run_cost.py`, the modes of `tools\model_mode_compare.py`, and the profiles of `tools\harness_profile_compare.py`. One test blocks every import of the SDK, to prove that the `--cli` ways don't need it (Lesson 6, Part 4) | 19 |

**Every `.py` file names its own tests.** The `HOW TO TEST` section at the top of each file gives the
exact `-k` words, with the expected output. It also gives a check by hand, and one with Claude. For example,
`convert.py` says `-k ConvertingUnits`, and `agent\guard_hook.py` says `-k guard_hook`. Open any
script in Notepad and read its first lines.

### Step 5 - See what happens without the venv

**Run:**

```bat
C:\Python312\python.exe -m unittest discover -s tests
```

**Expected result** (the end):

```text
Ran 74 tests in 11.987s

OK (skipped=6)
```

**How to read it:** the system Python has no pandas, so the 6 `PackageSkills` tests can't run. They are
**skipped**, not failed, because a missing pandas is a setup question, not a bug. With `-v` you see
the reason next to each one: `skipped "activate the skills' venv (pandas, openpyxl, matplotlib) to
run these tests"`. Where the Agent SDK is missing too, 2 more tests are skipped
(`skipped=8`). They check `tools\show_sdk_command.py` and the SDK way of `tools\run_cost.py`.

## Test 2 - The linter: are the SKILL.md files correct?

**What:** `tools\skills_lint.py` reads every `SKILL.md` and checks it against the rules of this course.

**Why:** Claude Code doesn't warn you about most mistakes in a `SKILL.md`. The skill just isn't chosen,
or its command fails. The linter finds the cause in a second.

**Run:**

```bat
python tools/skills_lint.py
```

**Expected result** (shortened):

```text
[ok] analyzing-csv  (auto + /command, description 372 chars)
   INFO  Claude Code-only keys ['effort'] (fine here; remove before uploading to claude.ai/API).
...
[ok] clear-todos  (/command only, description 107 chars)
   INFO  Claude Code-only keys ['argument-hint', 'disable-model-invocation', 'effort'] (fine here; remove before uploading to claude.ai/API).
...
Description overlap (pairs that may compete for the same request):
   none above 0.30 - descriptions are well separated

9 skills, 0 error(s).
```

**How to read it:**

- One block per skill. `[ok]` means no problem. `auto + /command`: Claude and you can start it.
  `/command only`: only you can.
- `ERROR` lines must be fixed. `WARN` lines are advice. `INFO` lines are only information.
- "Description overlap" compares every pair of descriptions. If two share too many words, you get a
  `WARN` line, because Claude could mix them up.

**What it checks:** the name format, and that a description exists and is not too long. It checks
that the description is written about the skill (not "I can..."), and that it has a "Use when ..."
sentence. It also checks the quotes around `"${CLAUDE_SKILL_DIR}"`, `$1`-style placeholders, that
every script and file mentioned exists, and that every `.py` file is valid Python.

**Try it on broken skills:** `python tools/skills_lint.py tools/demo_bad_skills` prints 3 errors and
an overlap warning. Lesson 2, Step 4 explains each one.

**Try breaking a real skill:** open `.claude\skills\converting-units\SKILL.md`. Remove the two `"`
around `${CLAUDE_SKILL_DIR}/scripts/convert.py` on line 17, save, and run the linter. You get a
`WARN ... quote the path` line. Put the quotes back, and run it again to see `0 error(s)`.

## Test 3 - The preview: a free, rough guess of the choice

**What:** `tools\route_preview.py` guesses which skill fits a request by counting shared words.

**Why:** it gives a quick warning before you spend allowance. If a typical request shares **no** words
with your skill's description, the description probably lacks the words people type.

**Run:**

```bat
python tools/route_preview.py "How many km is a marathon?"
```

**Expected result:**

```text
Request: How many km is a marathon?

   3.55  converting-units       shared words: km, many
   1.24  calculating-dates      shared words: many
   0.00  tracking-todos         shared words: -

  (not scored, /command only: clear-todos)
```

**How to read it:** the number is a score: higher means more shared words. `converting-units` shares
"km" and "many", so it is first. `clear-todos` is not scored, because Claude never chooses it by
itself (only you start it, with `/clear-todos`).

**Its limit:** it only counts words. Claude understands meaning, so the preview can be wrong where
Claude is right (Lesson 2, Step 3 shows a case). The preview also ignores the "Not for ..." sentence,
because a word counter can't understand "not". That is why that sentence must be the **last**
sentence of a description: the tool skips everything from "Not for" to the end.

## Test 4 - The routing test: what does Claude really choose?

### Step 6 - Look at the test questions

**What:** `tools\routing_cases.json` is a list of questions, each with the skill you expect.

**Run:**

```bat
type tools\routing_cases.json
```

**Expected result** (4 of the 20 lines):

```text
  {"prompt": "Convert 26.2 miles to kilometers.", "expect": "converting-units"},
  {"prompt": "Which region sold the most in data/sales.csv?", "expect": "analyzing-csv"},
  {"prompt": "Delete all my todos.", "expect": ["tracking-todos", null], "note": "clear-todos is manual-only, so Claude must not pick it"},
  {"prompt": "What is the capital of Australia?", "expect": null},
```

**How to read it:** `prompt` is the question, and `expect` is the skill Claude should choose. `null`
means "no skill". A list like `["tracking-todos", null]` means "either is fine".

**Why these kinds of questions:**

1. **Normal questions** check that each skill is found.
2. **Borderline questions** check that similar skills are told apart. For example, "How many bytes
   are in 3 GiB?" belongs to unit conversion, not data analysis. Questions for "only you" skills
   check that Claude does **not** choose them.
3. **"No skill" questions** check that descriptions don't grab too much.

### Step 7 - See what will run, for free

**Run:**

```bat
python tools/routing_eval.py --dry-run --limit 2
```

**Expected result:**

```text
C:\Users\Workstation\.local\bin\claude.EXE -p "Convert 26.2 miles to kilometers." --output-format stream-json --verbose --setting-sources project --no-session-persistence
C:\Users\Workstation\.local\bin\claude.EXE -p "How many pounds is 70 kg?" --output-format stream-json --verbose --setting-sources project --no-session-persistence
```

**How it works:** `--dry-run` only prints the commands; it runs nothing. Each question becomes one
`claude` command in headless mode:

| Part | Meaning |
|---|---|
| `-p "..."` | answer this one question without the interactive window |
| `--output-format stream-json` | report each step as it happens, as one JSON line |
| `--verbose` | report all steps (needed for `stream-json`) |
| `--setting-sources project` | load only this project's skills, so your personal skills don't change the test |
| `--no-session-persistence` | don't save the test runs in your session list |

The script reads the JSON lines. As soon as one says that Claude used the **Skill** tool, for
example `{"type": "tool_use", "name": "Skill", "input": {"skill": "converting-units"}}`, it notes the
skill and **stops Claude**. Claude doesn't need to finish its answer, so each question is cheap. If
Claude answers without the Skill tool, the result is "(no skill)".

### Step 8 - Run it for real

**Why:** only this test shows what **Claude** really chooses.

**Run:** (it uses a little of your Pro allowance)

```bat
python tools/routing_eval.py --limit 6
```

**Expected result** (a real run of 6 table and chart questions):

```text
Auth: claude.ai subscription (uses your Pro/Max allowance, no API billing)
Model: claude-opus-5-5

PASS  What are the average and maximum amounts in data/sales.csv  got=analyzing-csv          want=analyzing-csv
PASS  Which region sold the most in data/sales.csv?               got=analyzing-csv          want=analyzing-csv
PASS  Which sheets and columns are in data/sales.xlsx?            got=analyzing-excel        want=analyzing-excel
PASS  Build a pivot of amount by region and product from data/sa  got=analyzing-excel        want=analyzing-excel
PASS  Make a bar chart of total amount per region from data/sale  got=plotting-charts        want=plotting-charts
PASS  Plot the monthly sales amount from data/sales.xlsx as a li  got=plotting-charts        want=plotting-charts

6/6 routed as expected in 32s.
Details: tools\routing_report.json
```

**How to read it:**

- `Auth: claude.ai subscription`: your Pro plan is used, not an API key.
- Each line: `PASS` or `FAIL`, the question (shortened), the skill Claude chose (`got=`), and the
  skill you expected (`want=`).
- `6/6 routed as expected`: all matched. The details of every run are saved in `tools\routing_report.json`.

**Other forms:** `--model haiku` runs on the small Haiku model, which uses less of your allowance.
Without `--limit`, all 20 questions run.

**The same test through the Agent SDK:** add `--sdk`. Each question then gets its own
`ClaudeSDKClient`, with Claude Code's own instructions (`system_prompt={"type": "preset",
"preset": "claude_code"}`). Without this option, the SDK sends no instructions, and the choice could
differ. Both ways use
the same stop rules, in `read_event()`. In a real run of the first 3 questions on Haiku, the SDK way
passed 3 of 3, and `claude -p` 2 of 3. Once, Haiku answered "How many bytes are in 3 GiB?" without
the skill. One run each can't name a winner. When a question is close, run it a few times.

## What to do when a routing question fails: a real example

1. Read the `FAIL` line: which skill was expected, and which was chosen.
2. Change **one** description (Lesson 2, Step 5).
3. Run **all** questions again, because a change can fix one question and break another.

The first real run of this course gave 4 of 5:

```text
FAIL  Convert 26.2 miles to kilometers.              got=(no skill)        want=converting-units
PASS  Which region sold the most in data/sales.csv?  got=analyzing-csv     want=analyzing-csv
PASS  If a job starts on 2026-10-15, what date is... got=calculating-dates want=calculating-dates
PASS  Delete all my todos.                           got=tracking-todos    want=tracking-todos | (no skill)
PASS  What is the capital of Australia?              got=(no skill)        want=(no skill)
```

**Why it failed:** the question is easy, so Claude answered from memory without the skill. The
description only said *"Use when the user asks to convert a number..."*.

**The fix,** one changed sentence, which says the skill is for easy cases too, and why:

```diff
- ... MB to GiB). Use when the user asks to convert a number from one unit to another or asks "how many X in Y".
+ ... MB to GiB) with exact factors. Use for every unit conversion request, even simple ones like
+ miles to kilometers, and whenever the user asks "how many X in Y".
```

(In a "diff", `-` marks the old line and `+` the new lines.)

**The result:** all 3 unit questions passed. The "no skill" question still passed too. A description
that said "use for everything" would have broken that one.

**Next:** [Lesson 6 - Your own agent program with the Claude Agent SDK](06-agent-sdk-python.md)
