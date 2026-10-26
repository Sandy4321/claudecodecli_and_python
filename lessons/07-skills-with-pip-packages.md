# Lesson 7 - Skills that need pip packages (an isolated venv)

**Goal:** a skill whose Python script uses packages that don't come with Python, such as pandas,
openpyxl or matplotlib. You check, with commands, where the packages are, why activation matters,
and what happens when it is missing.

**Before you start:** open cmd, `C:\pyenvsmy\claudeclioct26\Scripts\activate`, and
`cd /d "E:\may10\claudecodecli_and_python"`.

## The idea in one paragraph

Python comes with a **standard library** (json, argparse, datetime, ...). Seven skills of this course
use only that, so any Python can run them. Other packages, like pandas, are installed with `pip`, and
they are installed **into one Python installation**. This course installs them into an isolated
**venv**, `C:\pyenvsmy\claudeclioct26`, so the system Python stays clean. A skill's command just says
`python`. Which Python that is depends on the PATH of the window where you started `claude`
(Lesson 0). So: activate, then start `claude`, and the skills find their packages.

This project has two such skills:

| Skill | Packages it needs | Script | What it does |
|---|---|---|---|
| `analyzing-excel` | pandas, openpyxl | `excel_tool.py` | sheets, statistics and pivot tables of .xlsx files |
| `plotting-charts` | pandas, openpyxl, matplotlib | `chart.py` | bar and line charts as PNG pictures |

The venv was created with `C:\Python312\python.exe -m venv C:\pyenvsmy\claudeclioct26`.

## Step 1 - See that pandas is only in the venv

**What:** `pip show` prints where a package is installed.

**Why:** to see with your own eyes that a package belongs to one Python, and not to the others.

**Run:** (with the activated venv's Python)

```bat
python -m pip show pandas
```

**How it works:** `python -m pip` runs pip **of this Python**. That is safer than typing just `pip`,
which could belong to another Python.

**Expected result:** (the important lines)

```text
Name: pandas
Version: 3.0.6
Location: C:\pyenvsmy\claudeclioct26\Lib\site-packages
```

**Run:** (with the system Python)

```bat
C:\Python312\python.exe -m pip show pandas
```

**Expected result:**

```text
WARNING: Package(s) not found: pandas
```

**How to read it:** pandas is installed **in the venv's folder** (`Location:`), and the system Python
doesn't have it. Activation decides which Python the word `python` means, for you **and** for every
command that Claude runs.

## Step 2 - See which packages a skill needs

**What:** each package skill has a `requirements.txt` file in its `scripts` folder.

**Why:** anyone who gets the skill folder knows what to install, and can install it with one command.

**Run:**

```bat
type .claude\skills\plotting-charts\scripts\requirements.txt
```

**Expected result:**

```text
# Packages for chart.py. Install into the activated virtual environment:
#   python -m pip install -r requirements.txt
pandas>=2.2
openpyxl>=3.1
matplotlib>=3.8
```

**How to read it:** one package per line. `>=2.2` means "version 2.2 or newer". Lines starting with
`#` are comments.

## Step 3 - Install the packages (only once)

**What:** you install everything listed in both `requirements.txt` files.

**Why:** the scripts can't run without them.

**Run:** (in the activated window, from the project folder)

```bat
python -m pip install -r .claude\skills\analyzing-excel\scripts\requirements.txt -r .claude\skills\plotting-charts\scripts\requirements.txt
```

**How it works:** `-r file` means "install everything listed in this file". You can give `-r` more
than once.

**Expected result:** on the course machine they are already installed, so pip only reports
`Requirement already satisfied: ...` for each package. On a new venv, pip downloads and installs them.

**Check it:**

```bat
python .claude/skills/plotting-charts/scripts/chart.py check
```

```text
{"python": "C:\\pyenvsmy\\claudeclioct26\\Scripts\\python.exe", "pandas": "3.0.6", "matplotlib": "3.11.2"}
```

**How to read it:** the `check` command prints which Python ran the script, and the package versions.
Both are what you want.

**If you see something else:** if `"python"` shows `C:\\Python312\\...`, the venv is not active, and
you installed into the wrong Python. Activate the venv, and install again.

## Step 4 - Use the Excel script yourself

**What:** you run two commands of `excel_tool.py`, as Claude would.

**Why:** to see what the skill gives Claude before Claude uses it.

**Run:**

```bat
python .claude/skills/analyzing-excel/scripts/excel_tool.py sheets data/sales.xlsx
```

**Expected result:**

```text
{"file": "data/sales.xlsx", "sheets": [{"sheet": "Sales", "rows": 12, "columns": ["date", "region", "product", "units", "amount"]}, {"sheet": "Targets", "rows": 4, "columns": ["region", "target"]}]}
```

**How to read it:** the workbook has two sheets. `Sales` has 12 rows with 5 columns, and `Targets` has
4 rows.

**Run:** (a pivot table: total `amount` per `region`)

```bat
python .claude/skills/analyzing-excel/scripts/excel_tool.py pivot data/sales.xlsx --sheet Sales --index region --values amount
```

**Expected result:**

```text
{"index": "region", "columns": null, "values": "amount", "agg": "sum", "rows": [{"region": "East", "amount": 910}, {"region": "North", "amount": 2150}, {"region": "South", "amount": 670}, {"region": "West", "amount": 900}, {"region": "Total", "amount": 4630}]}
```

**How to read it:** pandas summed `amount` for each region and added a `Total` row (4630).

**How it works:** the script opens the workbook with pandas (`pd.ExcelFile(path, engine="openpyxl")`).
pandas uses openpyxl to read .xlsx files. Then the script builds the table with `pd.pivot_table(...)`. These
few lines of pandas do the work of many lines of plain Python. That is why a skill uses packages.

## Step 5 - Draw a chart and look at it

**What:** you draw a line chart of the monthly sales.

**Run:**

```bat
python .claude/skills/plotting-charts/scripts/chart.py line data/sales.xlsx --sheet Sales --x date --y amount --freq M
```

**Expected result:**

```text
{"written": "charts/line_amount_by_date.png", "kind": "line", "x": "date", "y": "amount", "agg": "sum", "freq": "M", "points": [{"date": "2026-01", "amount": 720.0}, {"date": "2026-02", "amount": 1050.0}, {"date": "2026-03", "amount": 2260.0}, {"date": "2026-04", "amount": 600.0}]}
```

**Run:** (opens the picture)

```bat
start charts\line_amount_by_date.png
```

**How to read it:** `--freq M` grouped the dates by month. The script did two things:

1. It saved the picture: `"written": "charts/line_amount_by_date.png"`.
2. It printed the numbers it drew: `"points"`. **Why:** Claude reads the exact values from here, so it
   doesn't have to estimate them from the picture. The skill also tells Claude to open the PNG with
   its Read tool. Claude can look at images, and check that the chart is right.

## Step 6 - The skill's text is as simple as any other

**What:** you look at the commands in the chart skill's SKILL.md.

**Why:** to see that a package skill needs no special setting: activation chooses the venv, not the
skill.

**Run:**

```bat
findstr /n "python" .claude\skills\plotting-charts\SKILL.md
```

**Expected result:**

```text
5:  - Bash(python *)
6:  - PowerShell(python *)
17:python "${CLAUDE_SKILL_DIR}/scripts/chart.py" bar data/sales.csv --x region --y amount --agg sum
23:python "${CLAUDE_SKILL_DIR}/scripts/chart.py" line data/sales.csv --x date --y amount --agg sum --freq M
```

**How to read it:** the commands start with plain `python`, exactly like the standard-library skills.
Nothing in the skill says where the venv is. It works because you activated the venv before you
started `claude`.

The skill also contains one sentence for Claude: if a package is missing, **don't install anything**.
Instead, ask the user to activate the venv and restart `claude`. **Why:** installing software is your decision,
and Claude would install into whatever Python it has, possibly the system Python.

## Step 7 - See what happens without the venv

**What:** you run the Excel script with the system Python, as if you forgot to activate.

**Why:** to see the message Claude gets in that case, and the code that produces it.

**Run:**

```bat
C:\Python312\python.exe .claude/skills/analyzing-excel/scripts/excel_tool.py sheets data/sales.xlsx
```

**Expected result:**

```text
{"error": "Python package 'pandas' is not installed in C:\\Python312\\python.exe", "hint": "Claude Code was started without the skills' virtual environment. Activate the venv, then start claude again. Missing packages: python -m pip install -r \"E:\\may10\\claudecodecli_and_python\\.claude\\skills\\analyzing-excel\\scripts\\requirements.txt\""}
```

**How to read it:** instead of a long Python error report, the script prints a short JSON message:
**what** is missing, **which** Python was used, and **how** to fix it.

**How it works:** these lines at the top of the script:

```python
try:
    import pandas as pd
    import openpyxl
except ImportError as missing:
    print(json.dumps({
        "error": f"Python package '{missing.name}' is not installed in {sys.executable}",
        "hint": "Claude Code was started without the skills' virtual environment. Activate the venv, ...",
    }))
    sys.exit(2)
```

| Part | Meaning |
|---|---|
| `try: ... except ImportError as missing:` | try the imports. If a package is missing, Python raises `ImportError`, and the `except` part runs instead of a crash |
| `missing.name` | the missing package's name, here `pandas` |
| `sys.executable` | the full path of the Python that is running, here `C:\Python312\python.exe` |
| `sys.exit(2)` | ends with exit code 2, so Claude Code marks the command as failed |

Use the same guard in your own package scripts.

`chart.py` also has the line `matplotlib.use("Agg")` before it imports `pyplot`. "Agg" makes matplotlib
draw into files only. **Why:** Claude runs scripts without a screen, so a script must never try to
open a window. A window would wait for someone to close it, and the command would never end.

## Step 8 - Use the skills in Claude

**What:** you ask Claude four questions that need the package skills.

**Why:** to see the whole chain: activated window, `claude`, skill, `python` of the venv, pandas.

**Run:** `claude` (in the activated window), then type these one at a time.

**Expected result:** the skill Claude chose on the course machine is in brackets:

```text
Which sheets and columns are in data/sales.xlsx?                        [analyzing-excel]
Build a pivot of amount by region and product from data/sales.xlsx.     [analyzing-excel]
Make a bar chart of total amount per region from data/sales.csv.        [plotting-charts]
Plot the monthly sales amount from data/sales.xlsx as a line chart.     [plotting-charts]
```

**Watch for,** with the bar chart request (a real test run):

1. the **Skill** tool with `plotting-charts`;
2. a **Bash** or **PowerShell** command: `python ".../plotting-charts/scripts/chart.py" bar data/sales.csv --x region --y amount --agg sum`;
3. the **Read** tool with `charts\bar_amount_by_region.png`: Claude looks at the picture;
4. the answer: "North 2,150, East 910, West 900, South 670 ... checked the image visually against these numbers."

If items 2 and 3 are folded into one line like `Read 1 file, ran 1 shell command`, press **Ctrl+O**
to see them, with the JSON that `chart.py` printed (Lesson 0, section 7). Press **Esc** to go back.

**If you see something else:** `Python package 'pandas' is not installed` means you started `claude`
without activating. Type `/exit`, activate, and start `claude` again.

Type `/exit` when you are done.

## Step 9 - Run the tests both ways

**What:** you run the unit tests with the venv's Python, and then with the system Python.

**Why:** to see how the tests handle a missing package: they skip, they don't fail.

**Run:** (in the activated window)

```bat
python -m unittest discover -s tests
```

**Expected result:** (the end)

```text
Ran 74 tests in 31.351s

OK
```

**Run:** (with the system Python)

```bat
C:\Python312\python.exe -m unittest discover -s tests
```

**Expected result:** (the end)

```text
Ran 74 tests in 11.987s

OK (skipped=6)
```

**How to read it:** two groups of tests belong to this lesson:

| Group | Tests | What it checks | With the system Python |
|---|---|---|---|
| `PackageSkills` | 6 | runs `excel_tool.py`, `chart.py` and `tools\make_sample_xlsx.py` with the same Python that runs the tests | **skipped**, not failed, because pandas is missing. The tests start with `@unittest.skipUnless(has_packages("pandas", "openpyxl", "matplotlib"), ...)` |
| `WrongInterpreter` | 1 | the message from Step 7 | runs. It starts the scripts with `python -S`, which tells Python not to load installed packages. So pandas is "missing" even in the venv. It checks that the script prints the helpful message and doesn't crash |

The system Python run is faster (12.0 instead of 31.4 seconds). The 6 skipped tests are the slow
ones: loading pandas and drawing charts takes time.

## Step 10 - The same skills from a program

**What:** you run a package skill with `claude -p`, without the window.

**Why:** in a program, nobody can answer Claude Code's permission questions (Lesson 6).

**The problem:** in the normal `claude` window, Claude Code may ask you "use this skill?", and you
answer. In a program (`claude -p`, or the Agent SDK), nobody can answer, so the answer is
automatically "no". A real test showed this: the skill didn't load, so its `allowed-tools`
didn't apply. Every `python` command was refused too.

**The fix:** allow the Skill tool in advance.

**Run:** (uses a little allowance)

```bat
claude -p "Make a bar chart of total amount per region from data/sales.csv" --model haiku --allowedTools Skill
```

**Expected result:** Claude's answer, for example with the four region totals, and a new
`charts\bar_amount_by_region.png`. Once the skill is loaded, its own `allowed-tools` allows
the `python` commands.

With the Agent SDK, put `"Skill"` in `allowed_tools`, as `agent\run_agent.py` does (Lesson 6).

## Another way, not used here: write the venv's path into the skill

A SKILL.md could call the venv's Python by its full path instead of plain `python`:

```text
C:/pyenvsmy/claudeclioct26/Scripts/python.exe "${CLAUDE_SKILL_DIR}/scripts/chart.py" bar ...
```

This is called "pinning the interpreter".

| | Activation (this course) | Pinned path |
|---|---|---|
| Works if you forget to activate | no: you get the Step 7 message | yes |
| The commands in SKILL.md | short: `python ...` | long, and `allowed-tools` must name the same path |
| Works on another computer | yes, with any venv that has the packages | only if the venv is in exactly that folder |

That is why this course uses activation. If you pin a path in your own skills,
`python tools/skills_lint.py` checks that the `python.exe` exists, and warns if it doesn't.

## Try it yourself: add a package

**You learn:** the whole cycle for a new package, from `pip install` to Claude using it.

1. Pick a small library, for example `holidays` (public holidays of many countries).
2. In the activated window: `python -m pip install holidays`.
3. Check: `python -m pip show holidays`. `Location:` must be the venv's folder
   (`C:\pyenvsmy\claudeclioct26\Lib\site-packages`).
4. Add a line `holidays` to the `requirements.txt` of the skill that will use it.
5. Write a function that uses it, with the same `try ... except ImportError` guard as in Step 7.
6. Run your script yourself in cmd first, and then ask Claude.
7. Add a test, and run `python -m unittest discover -s tests` (Lesson 5).

**Next:** [Lesson 8 - Messy input: Claude reads, Python computes](08-messy-input-and-arguments.md)
