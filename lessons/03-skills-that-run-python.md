# Lesson 3 - Skills that run Python code

**Goal:** understand, by doing it yourself, how a skill makes Claude run the functions in your `.py`
files. You see what happens at each step, why it is built that way, and how the Python code does its
part.

**How this lesson works.** For each idea you first run the script yourself in cmd, **exactly as
Claude runs it**, and look at the output. Then you look at the Python code that produced it. Then
you ask Claude and watch it do the same thing. Every output shown here was copied from a real run
on the course machine.

**Before you start,** open cmd and type the start commands from Lesson 0:

```bat
C:\pyenvsmy\claudeclioct26\Scripts\activate
```

```bat
cd /d "E:\may10\claudecodecli_and_python"
```

Don't start `claude` yet. You will type the commands below in this cmd window.

## How a skill runs your Python, step by step

When you ask "How many miles is 100 km?", this happens:

| # | Who | What happens |
|---|---|---|
| 1 | Claude | reads the skill descriptions, and chooses `converting-units` (Lesson 2) |
| 2 | Claude Code | loads the skill's SKILL.md. It replaces `${CLAUDE_SKILL_DIR}` with the skill's folder, and gives the text to Claude |
| 3 | Claude | reads the instructions: "run `python ".../convert.py" convert VALUE FROM TO`". It fills in `100 km mi` |
| 4 | Claude Code | runs the command with its **PowerShell** or **Bash** tool: a normal program start, exactly as if you typed it in cmd |
| 5 | Python | runs `convert.py`. The script **prints** one line of JSON, and ends with an **exit code**: `0` for success, `1` for an error |
| 6 | Claude Code | catches everything the script printed, and gives it to Claude |
| 7 | Claude | reads the JSON, and answers you in normal language |

**Why let Python compute, and not Claude?** Claude writes text. It usually gets math right, but not
always, and it can't read an Excel file or draw a PNG by itself. A Python script gives the **same
exact** answer every time, and can use any Python package. Claude does what it is good at:
understanding your request, choosing the script, and explaining the result.

**Why JSON?** Python's `json.dumps()` turns a dictionary into one line of text with clear names
(`"result": 62.137119`). Claude reads that more reliably than a free sentence, and a test can check
it exactly (Lesson 5).

## Part 1 - The basic idea in three steps

### Step 1 - Run a skill's script yourself

**What:** you run the conversion script with the same command that Claude uses (step 4 above).

**Why:** to see exactly what Claude sees (step 6). If the output is right for you, it is right for Claude.

**Run:**

```bat
python .claude/skills/converting-units/scripts/convert.py convert 100 km mi
```

**Expected result:**

```text
{"value": 100.0, "from": "km", "to": "mi", "result": 62.137119, "category": "length"}
```

**How to read it:**

- `convert` is the **command** you gave the script. `100 km mi` are its **arguments**: convert 100
  from km to miles.
- The script prints its result as **JSON**: `"result": 62.137119` is the answer.
- This line is **all** that Claude sees when it runs the script. Claude never reads the 222 lines of
  Python code inside `convert.py`.

**How the Python code does it.** The end of `convert.py` (shortened):

```python
def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")       # Windows: print any character safely
    parser = argparse.ArgumentParser(description="Convert between units.")
    sub = parser.add_subparsers(dest="command", required=True)
    p_convert = sub.add_parser("convert", help="convert VALUE FROM TO")
    p_convert.add_argument("value", type=float)    # "100" becomes the number 100.0
    p_convert.add_argument("from_unit")            # "km"
    p_convert.add_argument("to_unit")              # "mi"
    sub.add_parser("units", help="list supported units by category")

    args = parser.parse_args(argv)                 # reads the words after convert.py
    if args.command == "convert":
        result = convert(args.value, args.from_unit, args.to_unit)   # the real work: a normal function
        print(json.dumps(result))                  # the one line Claude reads
        return 1 if "error" in result else 0       # the exit code
    ...

if __name__ == "__main__":                         # true only when run as a command
    sys.exit(main())
```

- `argparse` is Python's standard module for reading command words. It turns `convert 100 km mi`
  into `args.command="convert"`, `args.value=100.0`, `args.from_unit="km"`, `args.to_unit="mi"`.
- `convert(...)` is a normal Python function that returns a dictionary. `main()` only connects the
  command line to it, and prints the dictionary as JSON.
- `if __name__ == "__main__":` runs `main()` only when the file is started as a command. When a
  test imports the file, nothing runs by itself. The test can then call `convert(...)` directly
  (Lesson 5, Step 3).

### Step 2 - Find the same command inside the skill

**What:** you find the lines in SKILL.md that tell Claude which command to run.

**Why:** to see the link between the skill's text and your Python file: it is just a command line.

**Run:** (`findstr /n` prints the lines of a file that contain a word, with line numbers)

```bat
findstr /n "python" .claude\skills\converting-units\SKILL.md
```

**Expected result:**

```text
5:  - Bash(python *)
6:  - PowerShell(python *)
17:python "${CLAUDE_SKILL_DIR}/scripts/convert.py" convert 100 km mi
31:python "${CLAUDE_SKILL_DIR}/scripts/convert.py" units
```

**How to read it:**

- **Lines 17 and 31** are the commands that the skill tells Claude to run. Line 17 is the command
  you ran in Step 1. The only difference is `${CLAUDE_SKILL_DIR}`: before Claude reads the file,
  Claude Code replaces it with the skill's folder,
  `E:\may10\claudecodecli_and_python\.claude\skills\converting-units`. **Why:** Claude may be working in
  another folder. With the full path, the command always finds the script.
- **Lines 5 and 6** are the `allowed-tools` setting. They allow Claude to run any `python ...`
  command with its Bash or PowerShell tool **without asking you**, while it uses this skill. **Why
  both:** on Windows, Claude may use either tool. A command that is not allowed makes Claude Code ask you.
- **Why the quotes** around `"${CLAUDE_SKILL_DIR}/scripts/convert.py"`: they keep the command working
  even if a folder in the path has a space, for example `C:\Program Files\...`.
- **Why plain `python`:** Windows finds `python` in the PATH that Claude Code got from your activated
  cmd window. So it is your venv's Python (Lesson 0).

### Step 3 - Watch Claude do the same

**What:** you ask Claude, and watch it run the same command.

**Why:** to see steps 1 to 7 of the table above happen.

**Run:**

```bat
claude
```

**Type in Claude:** `How many miles is 100 km?`

**Expected result:** Claude Code shows each tool it uses. You will see, in this order:

1. the **Skill** tool with `converting-units`: Claude chose the skill (step 1);
2. the **PowerShell** (or **Bash**) tool with `python ".../convert.py" convert 100 km mi`: the same
   command as in Step 1, with the full folder filled in (steps 2 to 6);
3. Claude's answer, about 62.14 miles, taken from the `"result"` in the JSON (step 7).

**See every step:** Claude Code often folds item 2 into one line like `ran 1 shell command`. Press
**Ctrl+O** (Lesson 0, section 7). The transcript view shows the full command and the JSON line that
the script printed (exactly the line you saw in Step 1). It also shows Claude's thinking between the
steps. Press **Esc** to go back.

**If you see something else:** if Claude Code asks permission to run the command, answer Yes. It
asks once per skill, if you didn't choose "don't ask again" before.

Type `/exit` to leave Claude and come back to cmd.

**That is the whole mechanism:** the skill's text contains a command, Claude runs the command, and
Claude reads the JSON that the script prints. The rest of this lesson shows five ways to write such
scripts, each for a different kind of problem.

## Part 2 - Five patterns, each one tried out

### Pattern A - one script, several commands

**The problem it solves:** a skill usually needs a few related actions: convert a value, and list
the units. One script with several **commands** keeps them together, and SKILL.md lists each one.

**Used by:** `convert.py`, `csv_tool.py` and `text_stats.py`.

**How it works:** `argparse` sub-commands (Step 1, the code above): each `sub.add_parser("name")` is
one command, and each command calls one Python function.

#### Step A1 - Ask the script which commands it has

**What:** `--help` asks the script to describe itself.

**Why:** when you write a SKILL.md for a script, this shows you what to put in it. Claude can run it
too, if it is unsure.

**Run:**

```bat
python .claude/skills/converting-units/scripts/convert.py --help
```

**Expected result:**

```text
usage: convert.py [-h] {convert,units} ...

Convert between units.

positional arguments:
  {convert,units}
    convert        convert VALUE FROM TO
    units          list supported units by category
```

**How to read it:** the script has two commands, `convert` and `units`. You didn't write this help
text: `argparse` made it from the `add_parser(..., help="...")` lines.

#### Step A2 - Use the second command

**What:** the `units` command lists every unit the script knows.

**Why:** you may type a unit name that the script doesn't know ("nautical miles"). Then the SKILL.md
tells Claude to run `units` (line 31 in Step 2) and find the right name, instead of guessing.

**Run:**

```bat
python .claude/skills/converting-units/scripts/convert.py units
```

**Expected result:**

```text
{"length": ["mm", "cm", "m", "km", "in", "ft", "yd", "mi", "nmi"], "mass": ["mg", "g", "kg", "t", "oz", "lb", "st"], "volume": ["ml", "l", "m3", "tsp", "tbsp", "cup", "pt", "qt", "gal", "floz"], "speed": ["m/s", "km/h", "mph", "kn"], "data": ["b", "kb", "mb", "gb", "tb", "kib", "mib", "gib", "tib"], "temperature": ["c", "f", "k"]}
```

**How to read it:** the units are grouped by category. `nmi` is the nautical mile.

#### Step A3 - Make a mistake on purpose

**What:** you ask for an impossible conversion: kilograms to miles.

**Why:** Claude sometimes calls a script with a wrong argument. What the script prints then decides
whether Claude can fix the call by itself.

**Run:**

```bat
python .claude/skills/converting-units/scripts/convert.py convert 5 kg mi
```

**Expected result:**

```text
{"error": "Cannot convert mass (kg) to length (mi).", "hint": "Valid mass units: mg, g, kg, t, oz, lb, st"}
```

**Now check the exit code:** (`%errorlevel%` is the exit code of the last command)

```bat
echo %errorlevel%
```

```text
1
```

**How to read it:** the script didn't crash. It printed the problem **and how to fix it**
(`"hint"`). It ended with exit code `1`, so Claude Code marks the command as failed. Claude reads
the hint, picks a valid unit, and runs the command again.

**How the Python code does it:** inside `convert()`, the function **returns** the error as a
dictionary instead of raising an exception:

```python
if src_cat != dst_cat:
    return {
        "error": f"Cannot convert {src_cat} ({from_unit}) to {dst_cat} ({to_unit}).",
        "hint": f"Valid {src_cat} units: {', '.join(list_units()[src_cat])}",
    }
```

**Why not let Python crash?** A crash prints a "Traceback" of 10 or more lines about Python's
internals. Claude may understand it, but it costs more tokens, and it doesn't say what a **valid**
call would be.

**Another example,** with a column name typed with a capital letter:

**Run:**

```bat
python .claude/skills/analyzing-csv/scripts/csv_tool.py top data/sales.csv --column Amount
```

**Expected result:**

```text
{"error": "Unknown column 'Amount'.", "columns": ["date", "region", "product", "units", "amount"]}
```

**How to read it:** the error lists the real column names. Claude sees that the column is `amount`
(small letters) and fixes its call.

#### Step A4 - Give a script text instead of a file

**What:** you send text into `text_stats.py` without a file.

**Why:** if you paste text into the chat, there is no file to read. Claude could save the text to a
file first, but that needs a write permission and leaves a file behind. A **pipe** is simpler.

**Run:**

```bat
echo Short text. Another one here! | python .claude/skills/analyzing-text/scripts/text_stats.py stats -
```

**How it works:** `echo` prints the text, and `|` (the pipe) passes it to the script's input, called
**stdin**, instead of to the screen. The `-` instead of a file name tells the script "read stdin".
In `text_stats.py` this is two lines:

```python
if source == "-":
    return sys.stdin.read()      # the text that came through the pipe
```

**Expected result:**

```text
{"words": 5, "sentences": 2, "paragraphs": 1, "characters": 31, "reading_time_min": 0.0, "avg_sentence_words": 2.5, "flesch_reading_ease": 85.9, "longest_sentences": ["Another one here!", "Short text."]}
```

**How to read it:** the script counted 5 words in 2 sentences. `flesch_reading_ease` is a
readability score: 60-70 is plain English, 90-100 very easy, below 30 very hard.

**Now in Claude:** type
`How readable is this text: "The cat sat on the mat. It was happy."`, and watch the command that
Claude runs. It sends your text into the script with a pipe (`|`), and writes `-` instead of a file
name.
The SKILL.md of `analyzing-text` tells it to do this for pasted text.

### Pattern B - call any Python function by its name

**The problem it solves:** a dates skill needs many small functions: days between, add days, add
working days, weekday, age, and more later. Writing an `argparse` command for each one, and listing
each in SKILL.md, is repetitive. It is also easy to forget when you add a function.

**Used by:** `dates.py`, with the helper file `fncli.py` (about 130 lines, in the same folder).

**How it works:** you write normal Python functions with **type hints** (`days: int`) and a
**docstring** (the `"""..."""` text under the `def` line). The last lines of `dates.py` hand them to
`fncli`:

```python
PUBLIC = [days_between, add_days, add_business_days, business_days_between, weekday, age]

if __name__ == "__main__":
    fncli.run(PUBLIC)
```

`fncli.run()` uses Python's `inspect` module to read each function's name, parameters, types and
docstring. Then it builds one command per function, and one `--option` per parameter. So the SKILL.md
only says: "run `dates.py --list` to see the functions, then call one".

#### Step B1 - List all functions

**What:** `--list` prints every function in `PUBLIC`.

**Why:** this is how Claude finds out which functions exist, without reading the code.

**Run:**

```bat
python .claude/skills/calculating-dates/scripts/dates.py --list
```

**Expected result** (the first two of six functions):

```text
[
  {
    "name": "days_between",
    "signature": "days_between(start: str, end: str) -> dict",
    "doc": "Calendar days from start to end (negative if end is earlier). Dates are YYYY-MM-DD."
  },
  {
    "name": "add_days",
    "signature": "add_days(date: str, days: int) -> dict",
    "doc": "Add (or subtract, if negative) calendar days to a date."
  },
  ...
```

**How to read it:** each entry is one Python function in `dates.py`: its name, its parameters
(`signature`), and the first line of its docstring (`doc`). Nobody wrote this list by hand.

#### Step B2 - See how a function became a command

**What:** `--help` after a function name shows the command that `fncli` built for it.

**Why:** to see the rule that turns Python parameters into command options.

**Run:**

```bat
python .claude/skills/calculating-dates/scripts/dates.py add_business_days --help
```

**Expected result:**

```text
usage: dates.py add_business_days [-h] --date DATE --days DAYS
                                  [--holidays HOLIDAYS]

Add business days (Mon-Fri), skipping comma-separated holiday dates. Days must
be >= 0.
```

**How to read it,** next to the Python function it came from:

```python
def add_business_days(date: str, days: int, holidays: str = "") -> dict:
    """Add business days (Mon-Fri), skipping comma-separated holiday dates. Days must be >= 0."""
```

| In the Python function | Becomes in the command |
|---|---|
| the name `add_business_days` | the command `add_business_days` |
| the parameter `date: str` | the required option `--date DATE` (text) |
| the parameter `days: int` | the required option `--days DAYS`, turned into a whole number |
| the parameter `holidays: str = ""` | the **optional** option `[--holidays HOLIDAYS]`: in `[ ]` because it has a default value |
| the docstring | the help text |

#### Step B3 - Call the function

**What:** you call `add_business_days` with a date and a number of days.

**Run:**

```bat
python .claude/skills/calculating-dates/scripts/dates.py add_business_days --date 2026-10-15 --days 10
```

**Expected result:**

```text
{"date": "2026-10-15", "business_days": 10, "result": "2026-10-29", "weekday": "Thursday"}
```

**How to read it:** 10 working days after Thursday 15 October 2026 is Thursday 29 October 2026.
Weekends are skipped. `fncli` called `add_business_days(date="2026-10-15", days=10)` and printed
the returned dictionary as JSON.

**Try a wrong date:** `python .claude/skills/calculating-dates/scripts/dates.py add_days --date 15.10.2026 --days 3`.
The function raises a `ValueError`, and `fncli` turns it into JSON, with the function's signature
as a reminder of the right call:

```text
{"error": "date must be an ISO date like 2026-10-15, got '15.10.2026'", "function": "add_days", "signature": "add_days(date: str, days: int) -> dict"}
```

#### Step B4 - Add your own function (learn by doing)

**What:** you add a new function to `dates.py`, and it becomes a command at once.

**Why:** this is the main benefit of Pattern B. You give Claude new abilities by writing only a normal
Python function.

1. Open `.claude\skills\calculating-dates\scripts\dates.py` in an editor (for example Notepad).
2. Just above the line that starts with `PUBLIC = [`, paste this function:
   ```python
   def is_weekend(date: str) -> dict:
       """True if the date is a Saturday or a Sunday."""
       day = _parse(date, "date")
       return {"date": day, "weekday": WEEKDAY_NAMES[day.weekday()], "is_weekend": day.weekday() >= 5}
   ```
   `_parse` is a helper already in the file: it turns `"2026-10-17"` into a date, or raises a clear
   `ValueError`. `day.weekday()` is 0 for Monday up to 6 for Sunday, so `>= 5` means Saturday or Sunday.
3. Add `is_weekend` at the end of the `PUBLIC` list, so the line becomes:
   ```python
   PUBLIC = [days_between, add_days, add_business_days, business_days_between, weekday, age, is_weekend]
   ```
   **Why:** only functions in `PUBLIC` become commands. Helpers like `_parse` stay private.
4. Save the file.

**Run:**

```bat
python .claude/skills/calculating-dates/scripts/dates.py is_weekend --date 2026-10-17
```

**Expected result:**

```text
{"date": "2026-10-17", "weekday": "Saturday", "is_weekend": true}
```

**How to read it:** you wrote only a normal Python function, and it is already a command. Run
`dates.py --list` again: your function is now at the end of the list. Claude can find and use it,
even though the skill's SKILL.md doesn't mention it.

**If you see something else:** `invalid choice: 'is_weekend'` means you forgot step 3 or didn't save.
`IndentationError` means the function's lines don't start with exactly 4 spaces.

**Now in Claude:** start `claude` and type `Is 2026-10-24 a weekend?`. Watch the commands. Claude
may first run `dates.py --list` to look for a fitting function, and then call `is_weekend` (or
`weekday`). Either way, the answer comes from your Python code.

When you are done experimenting, you can keep `is_weekend` or delete it again. The tests don't
depend on it.

### Pattern C - check the data first, then calculate

**The problem it solves:** for money, a mistake is expensive. Two things can go wrong:

1. **The input:** Claude writes the invoice file from your chat message. It can make a mistake in it
   (a missing price, a quantity of 0).
2. **The math:** Python's normal numbers (`float`) can't store most decimal fractions exactly.

See problem 2 yourself:

**Run:**

```bat
python -c "print(0.1 + 0.2)"
```

```text
0.30000000000000004
```

```bat
python -c "from decimal import Decimal; print(Decimal('0.1') + Decimal('0.2'))"
```

```text
0.3
```

**Why:** a `float` is stored in binary, and 0.1 has no exact binary form, just like 1/3 has no exact
decimal form (0.333...). Python's `Decimal` type computes with decimal digits, exactly like on paper.

**Used by:** `invoice.py`.

**How it works:**

- The script has three commands, used **in order**: `validate` checks the file, `total` calculates,
  `render` writes the document.
- `validate` doesn't stop at the first problem. It collects **all** of them in a list, each with its
  exact place. So Claude can fix everything in one round:
  ```python
  for index, item in enumerate(items):
      where = f"items[{index}]"
      if not str(item.get("description", "")).strip():
          problems.append(f"{where}.description is missing or empty.")
      ...
  return {"ok": not problems, "problems": problems}
  ```
- `total` runs the same checks again, and refuses to calculate if any fails.
- All amounts are `Decimal`, rounded to cents with the usual rule (5 and up rounds up):
  ```python
  CENT = Decimal("0.01")
  def money(value):
      return value.quantize(CENT, rounding=ROUND_HALF_UP)
  ```
- The SKILL.md tells Claude the order, and gives it a checklist to copy into its reply and tick off.
  **Why a checklist:** Claude follows a written list of steps more reliably than a paragraph. And you
  can see which step it is on.

#### Step C1 - Look at a broken invoice

**What:** a practice invoice with mistakes.

**Run:** (`type` prints a file)

```bat
type data\invoice_broken.json
```

**Expected result:**

```text
{
  "number": "INV-2026-043",
  "customer": "Beta GmbH",
  "tax_pct": 119,
  "items": [
    {"description": "Support plan", "qty": 0, "unit_price": 49},
    {"description": "", "qty": 2, "unit_price": "abc"}
  ],
  "shipping": 15
}
```

Can you find the mistakes yourself? There are five.

#### Step C2 - Let the script check it

**What:** `validate` checks the invoice without calculating anything.

**Run:**

```bat
python .claude/skills/calculating-invoices/scripts/invoice.py validate data/invoice_broken.json
```

**Expected result:**

```text
{"ok": false, "problems": ["items[0].qty must be a number greater than 0, got 0.", "items[1].description is missing or empty.", "items[1].unit_price must be a number >= 0, got 'abc'.", "'tax_pct' must be between 0 and 100, got 119.", "Unknown top-level fields ['shipping']; allowed: number, customer, currency, discount_pct, tax_pct, items, notes."]}
```

**How to read it:** `"ok": false`, and all five problems, each with its exact place. `items[0]` is
the first item and `items[1]` the second (Python counts from 0). `shipping` is unknown: the script
doesn't know how to tax it, so it refuses instead of ignoring it silently.

#### Step C3 - The script refuses to calculate a broken invoice

**What:** you try `total` on the broken invoice, as if Claude skipped the check.

**Why:** to see the second safety net. Even if Claude skips `validate`, no wrong total comes out.

**Run:**

```bat
python .claude/skills/calculating-invoices/scripts/invoice.py total data/invoice_broken.json
```

**Expected result:** (shortened)

```text
{"error": "Invoice is invalid; run validate first: items[0].qty must be a number greater than 0, got 0. ..."}
```

#### Step C4 - Check and calculate a correct invoice

**Run:**

```bat
python .claude/skills/calculating-invoices/scripts/invoice.py validate data/invoice.json
```

**Expected result:**

```text
{"ok": true, "problems": []}
```

**Run:**

```bat
python .claude/skills/calculating-invoices/scripts/invoice.py total data/invoice.json
```

**Expected result:** (shortened)

```text
{"currency": "USD", "lines": [...], "subtotal": "1440.47", "discount": "144.05", "tax": "106.95", "total": "1403.37"}
```

**How to read it:** subtotal 1440.47, minus 10% discount (144.05), plus 8.25% tax (106.95), gives a
total of 1403.37. The amounts are text in quotes (`"1403.37"`), because `json.dumps` can't write a
`Decimal` as a number without turning it back into a `float`. Text keeps every digit exact.

#### Step C5 - Make the invoice document

**What:** `render` writes the invoice as a Markdown file.

**Run:**

```bat
python .claude/skills/calculating-invoices/scripts/invoice.py render data/invoice.json --out invoice.md
```

```bat
type invoice.md
```

**Expected result:**

```text
# Invoice INV-2026-042

**Bill to:** Acme Ltd

| Description | Qty | Unit price | Amount |
|---|---:|---:|---:|
| Consulting hours | 12 | 95.00 | 1140.00 |
| Workshop materials | 3 | 19.99 | 59.97 |
| Travel | 1 | 240.50 | 240.50 |

Subtotal: 1440.47 USD
Discount (10%): -144.05 USD
Tax (8.25%): 106.95 USD
**Total: 1403.37 USD**

Payment due within 30 days.
```

Delete the practice file afterwards: `del invoice.md`

**Now in Claude:** type `Make me a quote: 3 chairs at 120 each and 1 desk at 450, plus 20% VAT.`

**Expected result:** three steps, in this order:

1. Claude **writes** a JSON file with the items. Claude Code asks your permission to create the
   file: answer Yes;
2. Claude runs **`validate`**, and fixes the file if a problem is reported;
3. only then does Claude run **`total`**, and reports 810.00 + 162.00 VAT = 972.00.

To see the checklist and the order that make Claude do this:
`type .claude\skills\calculating-invoices\SKILL.md`

### Pattern D - data that is kept, and a skill only you can start

**The problem it solves:** Claude remembers nothing between sessions. Close Claude Code, and your
tasks are gone, unless something saves them. A Python script can save them in a **file**.

**Used by:** `tracking-todos` saves tasks in `data\todos.json`. `clear-todos` deletes tasks, and only
**you** can start it.

**How it works:**

- Every command of `todo.py` loads the file, changes the list, and saves it again:
  ```python
  def load(path):
      if not path.exists():
          return []                                   # no file yet: an empty list
      return json.loads(path.read_text(encoding="utf-8"))

  def save(path, todos):
      path.write_text(json.dumps(todos, indent=2), encoding="utf-8")
  ```
- Which file? This line decides it:
  ```python
  return Path(explicit or os.environ.get("TODO_FILE") or DEFAULT_FILE)
  ```
  It takes the `--file` option if given, otherwise the **environment variable** `TODO_FILE` if set,
  otherwise `data/todos.json`. **Why:** so tests and practice can use another file, and never touch
  your real list.
- Deleting is a **separate** skill, `clear-todos`, which Claude can't start (Step D5). **Why:** a
  misunderstood sentence must never delete your data.

#### Step D1 - Use a practice list, so your real list is not touched

**What:** you set the environment variable `TODO_FILE` for this cmd window.

**Run:**

```bat
set TODO_FILE=data\practice_todos.json
```

**How it works:** `set NAME=value` creates an environment variable in this cmd window only. Every
program you start from this window, including `todo.py`, can read it with `os.environ.get("TODO_FILE")`.

**Expected result:** nothing is printed. Check it with `echo %TODO_FILE%`: it prints `data\practice_todos.json`.

#### Step D2 - Add two tasks and list them

**Run:**

```bat
python .claude/skills/tracking-todos/scripts/todo.py add "Buy milk"
```

```bat
python .claude/skills/tracking-todos/scripts/todo.py add "Send the report" --due 2026-10-01 --priority high
```

```bat
python .claude/skills/tracking-todos/scripts/todo.py list
```

**Expected result** (the last command; your `created` date is today's date):

```text
{"file": "data\\practice_todos.json", "count": 2, "tasks": [{"id": 2, "text": "Send the report", "priority": "high", "due": "2026-10-01", "done": false, "created": "2026-10-20", "overdue": true}, {"id": 1, "text": "Buy milk", "priority": "normal", "due": null, "done": false, "created": "2026-10-20", "overdue": false}]}
```

**How to read it:**

- `"file": "data\\practice_todos.json"`: the practice file was used, thanks to `TODO_FILE`. (In
  JSON, a `\` is written as `\\`.)
- Each task got an `id` (1 and 2). Claude uses it later for `done 1`.
- The high-priority task is listed first, and its due date has passed, so `"overdue": true`. The
  SKILL.md tells Claude to mention overdue tasks first.

#### Step D3 - Look at the saved file

**What:** you look at the file the script wrote.

**Why:** to see where the skill's "memory" is.

**Run:**

```bat
type data\practice_todos.json
```

**Expected result:** (first task)

```text
[
  {
    "id": 1,
    "text": "Buy milk",
    "priority": "normal",
    "due": null,
    "done": false,
    "created": "2026-10-20"
  },
  ...
```

**How to read it:** this file is the "memory" of the skill. It stays on disk after Claude Code
closes, and the next session's `list` reads it again.

#### Step D4 - Finish a task, then delete finished tasks

**Run:**

```bat
python .claude/skills/tracking-todos/scripts/todo.py done 1
```

```bat
python .claude/skills/tracking-todos/scripts/todo.py clear --done-only
```

**Expected result** (the last command):

```text
{"removed": 1, "remaining": 1}
```

**How to read it:** task 1 was marked done, and `clear --done-only` removed it. Task 2 remains.

**Clean up** the practice file and the variable (`set TODO_FILE=` with nothing after `=` removes it):

```bat
del data\practice_todos.json
```

```bat
set TODO_FILE=
```

#### Step D5 - See why Claude can't delete your tasks by itself

**What:** you read the SKILL.md of `clear-todos`.

**Run:**

```bat
type .claude\skills\clear-todos\SKILL.md
```

**Expected result:** (the important lines)

```text
---
name: clear-todos
description: Deletes tasks from data/todos.json - finished tasks only by default, or every task with the "all" argument.
argument-hint: "[done|all]"
disable-model-invocation: true
...
The user's argument was: "$ARGUMENTS"

1. If the argument is `all`, run:
   python "${CLAUDE_SKILL_DIR}/../tracking-todos/scripts/todo.py" clear --all
   Otherwise (empty or `done`), run:
   python "${CLAUDE_SKILL_DIR}/../tracking-todos/scripts/todo.py" clear --done-only
```

**How to read it:**

| Line | What it does | Why |
|---|---|---|
| `disable-model-invocation: true` | Claude may **never** start this skill by itself. Only you can, by typing `/clear-todos` | deleting must be your decision (Lesson 2, Step 6) |
| `argument-hint: "[done\|all]"` | shown next to `/clear-todos` in the `/` menu | reminds you which words the skill accepts |
| `$ARGUMENTS` | replaced by the words you type after the name: `/clear-todos all` makes it `all` | the instructions choose the command from your word |
| `${CLAUDE_SKILL_DIR}/../tracking-todos/...` | uses the script of the neighbor skill. `..` means "one folder up" | one script for both skills, so the file format lives in one place. This works only while both skill folders are next to each other |

**Now in Claude:** start `claude` and type `Delete all my todos.`

**Expected result:** Claude can't use `clear-todos`. The `tracking-todos` skill tells Claude to ask
you to type `/clear-todos` yourself. Then type `/clear-todos done`: now the skill runs, because you
started it.

### Pattern E - pip packages from your venv

**The problem it solves:** some work needs packages that are not part of Python, for example pandas
(tables, Excel) and matplotlib (charts). They are installed with `pip`, and in this course only in
your venv.

**Used by:** `analyzing-excel` and `plotting-charts`. Lesson 7 explains this pattern in full. Here,
try it.

**How it works:** the script imports the packages inside a `try`. If an import fails, it prints a
JSON error with the fix, instead of crashing:

```python
try:
    import matplotlib
    matplotlib.use("Agg")       # draw into files only: Claude runs the script without a screen
    import matplotlib.pyplot as plt
    import pandas as pd
except ImportError as missing:
    print(json.dumps({
        "error": f"Python package '{missing.name}' is not installed in {sys.executable}",
        "hint": "Claude Code was started without the skills' virtual environment. ...",
    }))
    sys.exit(2)
```

`sys.executable` is the full path of the Python that runs the script, so the message says **which**
Python lacks the package. The file `scripts\requirements.txt` lists the packages, so
`python -m pip install -r ...requirements.txt` installs them all.

#### Step E1 - Run with the activated venv

**What:** `check` reports which Python runs the script, and the package versions.

**Run:**

```bat
python .claude/skills/plotting-charts/scripts/chart.py check
```

**Expected result:**

```text
{"python": "C:\\pyenvsmy\\claudeclioct26\\Scripts\\python.exe", "pandas": "3.0.6", "matplotlib": "3.11.2"}
```

**How to read it:** `python` is your venv's Python, and pandas and matplotlib are found there.

#### Step E2 - Run with the system Python (as if you forgot to activate)

**What:** the same command, but with the full path of the system Python.

**Why:** to see the error that Claude would get if you started `claude` without activating.

**Run:**

```bat
C:\Python312\python.exe .claude/skills/plotting-charts/scripts/chart.py check
```

**Expected result:**

```text
{"error": "Python package 'pandas' is not installed in C:\\Python312\\python.exe", "hint": "Claude Code was started without the skills' virtual environment. Activate the venv, then start claude again. ..."}
```

**How to read it:** the `try` / `except ImportError` code above ran. The system Python has no
pandas, and the message says what to do.

#### Step E3 - Draw a chart and open it

**What:** you draw a bar chart of the total amount per region.

**Run:**

```bat
python .claude/skills/plotting-charts/scripts/chart.py bar data/sales.csv --x region --y amount
```

**Expected result:**

```text
{"written": "charts/bar_amount_by_region.png", "kind": "bar", "x": "region", "y": "amount", "agg": "sum", "points": [{"region": "North", "amount": 2150.0}, {"region": "East", "amount": 910.0}, {"region": "West", "amount": 900.0}, {"region": "South", "amount": 670.0}]}
```

**Run:** (opens the picture in your image viewer)

```bat
start charts\bar_amount_by_region.png
```

**How to read it:** the script saved the picture (`"written"`) and also printed the numbers it drew
(`"points"`). **Why both:** Claude can't see a picture by running a script. It reads the exact numbers
from `points` to describe the chart, and can open the PNG to check it.

## Part 3 - Bonus: a command that runs before Claude reads the skill

**What:** a SKILL.md can contain a line like `` !`ls data` ``. When the skill starts, Claude Code runs
the command **first**, and puts its **output** in place of the line. Claude sees the result, not the
command.

**Why:** for fresh facts that the instructions need, such as today's date or the list of files. Claude
gets them without spending a turn on running a command.

### Step 4 - Make a small test skill

**Do:** create the folder `.claude\skills\showing-data-files\`, and in it a file `SKILL.md` with this text:

```markdown
---
name: showing-data-files
description: Shows today's date and the files in the data folder. Use when the user asks which data files exist.
allowed-tools:
  - Bash(date *)
  - Bash(ls *)
---

Today is !`date +%Y-%m-%d`.

Files in the data folder:
!`ls data`

Tell the user today's date and list the files above. Do not run any commands.
```

**How it works:** the two `allowed-tools` lines are needed: they allow the `date` and `ls` commands
to run when the skill starts. `date` and `ls` are Bash commands, so this needs Git for Windows
(Lesson 0). `date +%Y-%m-%d` prints the date as `2026-10-20`.

### Step 5 - Use it

**Run:** start `claude` and type `/showing-data-files`.

**Expected result** (a real result):

```text
Today is 2026-10-20.

Files in the data folder:
- article.txt
- invoice.json
- invoice_broken.json
- sales.csv
- sales.xlsx
```

**How to read it:** Claude didn't run any command itself: you see no Bash tool line. Claude Code ran
`date` and `ls data` when the skill started, and Claude only read the results. Keep such commands
fast, and use only commands that read, never ones that change files.

### Step 6 - Remove the test skill

Type `/exit`, then (`rmdir /s /q` deletes a folder with its files, without asking):

```bat
rmdir /s /q .claude\skills\showing-data-files
```

## Summary: which pattern to use

| You need | Pattern | Example skill | Try again with |
|---|---|---|---|
| A few clear actions on one kind of input | A - one script, several commands | `converting-units` | `convert.py --help` |
| Many small functions, and adding new ones easily | B - call any function by name | `calculating-dates` | `dates.py --list` |
| Results where a mistake is expensive | C - check first, then calculate | `calculating-invoices` | `invoice.py validate ...` |
| Data that must survive between sessions, or a dangerous action | D - kept data, manual-only skill | `tracking-todos`, `clear-todos` | `todo.py list` |
| Python packages such as pandas | E - pip packages from the venv | `plotting-charts` | `chart.py check` |

Rules that every skill script in this project follows (you saw each one above):

| Rule | Why |
|---|---|
| 1. It prints its result as **JSON** (Part 1, Step 1) | Claude reads named values reliably, and tests can check them exactly |
| 2. It prints **errors as JSON with a hint**, and ends with exit code 1 (Step A3) | Claude can fix its call by itself, instead of guessing from a crash |
| 3. It never opens a window or asks the user a question. It prints and ends | Claude runs it without a screen and can't answer questions. A script that waits for input would hang |
| 4. It starts printing in UTF-8 (`sys.stdout.reconfigure(encoding="utf-8")`) | characters like `°` then work on Windows (Lesson 0, section 6) |
| 5. Its logic is in normal Python functions, and `main()` only connects them to the command line | tests and other programs can import and reuse them (Pattern B, Lessons 5 and 6) |

**Next:** [Lesson 4 - Designing an agent with many skills](04-designing-many-skills.md)
