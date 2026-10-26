# Claude Code Skills Tutor

This course teaches you to build **an agent with many skills** in the Claude Code CLI. You will learn:

- how Claude decides which skill fits your request, and
- how a skill's text makes Claude run **functions you wrote in Python files**.

Everything in this course runs. The project folder contains a working agent with 9 skills, tests,
and tools that check whether Claude picks the right skill.

**New here?** Read [Start here: what this course gives you](lessons/start-here.md) first. At the end
come [What you have learned](lessons/summary.md), a one-page [cheat sheet](lessons/cheat-sheet.md), and
67 [questions and answers](lessons/questions-and-answers.md) to test yourself.

## Words used in this course

Read this list once. The lessons use these words without explaining them again.

| Word | Meaning |
|---|---|
| Claude Code CLI | The `claude` program that you start by typing `claude` in cmd. CLI means "command-line interface": you type, it answers in the same window. |
| Session | One run of `claude`, from start until you type `/exit`. One session is one conversation. |
| Prompt | A message you type to Claude. |
| Model | The AI that answers: Opus (most capable), Sonnet, Haiku (fastest). Bigger models use more of your Pro allowance. |
| Token | The unit in which AI text is counted. One token is about three quarters of an English word. Usage limits count tokens. |
| Context window | Everything Claude can see at one moment: instructions, the conversation so far, file contents, command outputs. It has a size limit. The more it contains, the more each message costs. |
| Tool | An action that Claude Code performs for Claude. Examples: **Read** (read a file), **Write**/**Edit** (change a file), **Bash** and **PowerShell** (run a command), **Glob**/**Grep** (find files or text), **Skill** (load a skill). |
| Permission prompt | The question "Allow Claude to ...?" that Claude Code shows before some tools. You answer Yes or No. |
| Thinking | The reasoning Claude does before it acts or answers. Claude Code shows it only for a moment, then folds it away. |
| Transcript view | The detailed view that **Ctrl+O** opens: Claude's thinking, and every tool call with its full command and output. **Esc** goes back (Lesson 0, section 7). |
| Skill | A folder with a `SKILL.md` file: a description, instructions, and often a Python script. |
| Frontmatter | The settings block at the top of `SKILL.md`, between two `---` lines (for example `name:` and `description:`). It uses YAML: simple `key: value` lines. |
| Description | The `description:` line in the frontmatter. It tells Claude what the skill does and when to use it. |
| Skill listing | The list of the names and descriptions of all skills. Claude Code puts it in the context window at the start of every session, so Claude knows which skills exist. |
| Routing | Choosing the skill that fits a request. Claude does this itself, by comparing your request with the skill listing. |
| Slash command | A message that starts with `/`, for example `/clear`, `/model`, or `/converting-units`. It runs a built-in command, or starts a skill directly. |
| Headless mode | `claude -p "question"`: Claude Code answers one prompt without the interactive screen, prints the answer and exits. Programs use it. Nobody is there to answer permission prompts. |
| Agent SDK | The Python package `claude-agent-sdk`. It runs Claude Code from your own Python program (Lesson 6). |
| stdout, stdin | stdout is the text a program prints. stdin is text a program reads as input, for example through a pipe: `echo hello \| python script.py`. |
| JSON | A text format for data, for example `{"region": "North", "amount": 2150}`. The skill scripts print JSON so Claude can read their results exactly. |
| Exit code | The number a program returns when it ends. 0 means success; any other number means an error. |
| Standard library | The modules that come with Python (`json`, `csv`, `datetime`, ...). No installation is needed. |
| pip package | A Python library that you install with `pip install`, for example pandas or matplotlib. |
| venv | "Virtual environment": a separate Python folder with its own pip packages. This course uses `C:\pyenvsmy\claudeclioct26`. |
| PATH | The list of folders where Windows looks for programs. It decides which `python.exe` runs when you type `python`. |
| CLAUDE.md | A text file with project rules. Claude Code reads it at the start of every session in that folder. |
| Subagent | A helper Claude that Claude starts for a big sub-task. It works in its own context window and returns only a short result. |
| Hook | A command that Claude Code itself runs automatically on an event (for example, before every file edit). The model cannot skip it. |
| Plugin | An installable package of skills (and other extensions) that other people made. |
| MCP | "Model Context Protocol": a standard way to give Claude extra tools that run in a separate program or inside your Python program. |
| Linter | A program that checks files for mistakes without running them. Here: `tools/skills_lint.py` checks every `SKILL.md`. |
| Unit test | A small automatic test that checks that one function gives the right result. |
| Eval | Short for evaluation: running a list of test questions and measuring the results. Here: does Claude pick the expected skill? |
| Pro allowance | How much Claude your Pro subscription lets you use per 5 hours and per week. The claude.ai chat uses the same allowance. |

## Lessons

| # | Lesson | You learn |
|---|---|---|
| 0 | [Setup: Windows, CLI, Pro subscription](lessons/00-setup-windows-pro.md) | How to start every time, which Python runs, how to make sure Pro pays (not an API key), how to see Claude's thinking and every command (Ctrl+O) |
| 1 | [What a skill is](lessons/01-what-is-a-skill.md) | The parts of a skill folder, and how Claude loads it step by step |
| 2 | [How Claude picks the right skill](lessons/02-how-claude-picks-a-skill.md) | Writing descriptions so the right skill is chosen; manual-only skills |
| 3 | [Skills that run Python code](lessons/03-skills-that-run-python.md) | How SKILL.md tells Claude to run your Python, and five ready-made patterns |
| 4 | [Designing an agent with many skills](lessons/04-designing-many-skills.md) | Planning many skills so they don't compete; naming; sharing code |
| 5 | [Testing skills that run Python](lessons/05-testing-skill-routing.md) | Four kinds of tests: unit tests of the Python code, the linter, the preview, and real Claude runs. How to read a failure |
| 6 | [Your own agent with the Agent SDK](lessons/06-agent-sdk-python.md) | Running Claude Code from Python; your functions as tools; Claude as an LLM with Pro; when to use `claude -p` and when the SDK; reasoning effort; effort per skill |
| 7 | [Skills that need pip packages](lessons/07-skills-with-pip-packages.md) | Skills that use pandas and matplotlib from your venv |
| 8 | [Messy input: Claude reads, Python computes](lessons/08-messy-input-and-arguments.md) | A calculator skill for requests in any order, with words and typos; `$ARGUMENTS`, `$0`, `$1` explained |
| 9 | [Exercises](lessons/09-exercises.md) | Eight hands-on exercises, from 5 minutes to a stretch goal |

## The 9 skills of the example agent

| Skill | What it does | Who can start it | Python file | What it teaches |
|---|---|---|---|---|
| `converting-units` | Converts km/miles, kg/lb, °C/°F, GB/GiB, ... | Claude, or you with `/converting-units` | `convert.py` | A script with several commands; error messages that tell Claude how to fix the call |
| `analyzing-csv` | Statistics, totals and top rows of a .csv file | Claude, or you | `csv_tool.py` | Extra details in a separate `reference.md` that Claude reads only when needed |
| `analyzing-text` | Word count, reading time, readability of a text | Claude, or you | `text_stats.py` | Reading text that you pasted into the chat; separating it from a similar skill |
| `calculating-dates` | Days between dates, working days, weekday, age | Claude, or you | `dates.py` + `fncli.py` | **Calling any Python function by its name** |
| `calculating-invoices` | Invoice totals with discount and tax | Claude, or you | `invoice.py` | Check the data first, then calculate (plan, validate, execute) |
| `analyzing-excel` | Sheets, statistics and pivot tables of .xlsx files | Claude, or you | `excel_tool.py` (needs pandas) | **Using pip packages from your venv** |
| `plotting-charts` | Bar and line charts as PNG pictures | Claude, or you | `chart.py` (needs pandas, matplotlib) | **pip packages**; a result that Claude can look at |
| `tracking-todos` | A to-do list saved in `data/todos.json` | Claude, or you | `todo.py` | Data that is kept between sessions |
| `clear-todos` | Deletes tasks from the to-do list | **Only you**: type `/clear-todos done` (delete finished tasks) or `/clear-todos all` (delete all). Claude can never start it. | uses `todo.py` from `tracking-todos` | Making a dangerous skill manual-only (`disable-model-invocation: true`), and giving a skill the words you type after its name (`$ARGUMENTS`) |

## Quick start (20 minutes)

The quick start takes you once through the whole course. You start correctly, check that the Python
code works, use the skills in Claude, and test Claude's choices. Each step says **what** you do,
**why**, the **expected result**, and **what to do if you see something else**. The lessons explain
each part in depth.

You need the Claude Code CLI, logged in with your claude.ai Pro account (Lesson 0). You also need the
venv `C:\pyenvsmy\claudeclioct26`, with pandas, openpyxl and matplotlib installed (Lesson 7).

### Step 1 - Open cmd and start the right way

**What:** two commands. The first switches on your virtual environment (venv). The second goes to the
project folder.

**Why:** the skills run Python scripts. Two of them need pandas and matplotlib, and these packages are
installed only in the venv. After `activate`, the word `python` means the venv's Python, in this
window and for every command Claude runs from it. The project folder is where Claude Code finds the
skills (`.claude\skills\`).

**Run:**

```bat
C:\pyenvsmy\claudeclioct26\Scripts\activate
```

```bat
cd /d "E:\may10\claudecodecli_and_python"
```

**Expected result:** the prompt starts with the venv's name and shows the project folder:

```text
(claudeclioct26) E:\may10\claudecodecli_and_python>
```

**If you see something else:** if `(claudeclioct26)` is missing, the first command failed. Check
that the folder `C:\pyenvsmy\claudeclioct26` exists. If the path is wrong after `cd`, check that you
typed `/d`.

### Step 2 - Check that the Python code works (unit tests)

**What:** the project folder contains a test file, `tests\test_skill_scripts.py`, with 74 small
**unit tests**. A unit test is a short piece of Python. It runs one function of a skill script with a
known input, and checks that the result is exactly right. For example, one test calls the
conversion function with "100 km to miles" and checks that the answer is 62.137119.

**Why:** when Claude uses a skill, it runs the skill's Python script and **trusts its output**. If the
script computes something wrong, Claude repeats the wrong number to you, with confidence. The tests
prove that every script gives correct results **before** Claude uses it. They run on your computer
only: they don't contact Claude, so they are free and take about 20 seconds. Run them after
installing, and every time you change a script.

**Run:**

```bat
python -m unittest discover -s tests
```

**How it works:** `python -m unittest` starts Python's built-in test runner. `discover -s tests`
tells it to look in the folder `tests` for files named `test_*.py`. It then runs every function whose
name starts with `test_`.

**Expected result:**

```text
..........................................................................
----------------------------------------------------------------------
Ran 74 tests in 31.351s

OK
```

**How to read it:** each dot (`.`) is one test that passed: 74 dots for 74 tests. `Ran 74 tests`
counts them, and the time doesn't matter. `OK` means **all** passed.

**If you see something else:**

- **An `F` among the dots and `FAILED (failures=1)` at the end:** a test found a wrong result. Below
  the dots, a block that starts with `FAIL:` names the test. It shows what was expected and what came
  instead. Lesson 5, Step 2 shows how to read such a block, with a real example.
- **`OK (skipped=6)`:** you ran it without the venv, so pandas is missing. The 6 tests that need it
  (Excel, charts, the sample workbook) were skipped. Do Step 1 again.
- **An `E` and `ERROR`:** a script crashed. The block below the dots shows the error message.

### Step 3 - Check that the skill files are written correctly (the linter)

**What:** `tools\skills_lint.py` is a **linter**: a program that reads every `SKILL.md` and checks it
against the rules of this course, without running anything.

**Why:** Claude Code is silent about many mistakes in a `SKILL.md`. With a wrong name, a missing
description, or a script path that doesn't exist, the skill is not chosen, or it fails. You don't see
why. The linter finds these mistakes in a second, for free.

**Run:**

```bat
python tools/skills_lint.py
```

**Expected result** (the end of the output):

```text
Description overlap (pairs that may compete for the same request):
   none above 0.30 - descriptions are well separated

9 skills, 0 error(s).
```

**How to read it:** there is one `[ok]` block per skill above this. `0 error(s)` means all 9 skills
follow the rules. "No overlap" means no two descriptions are so similar that Claude could confuse them.

**If you see something else:** an `ERROR` line must be fixed. It says what is wrong, and in which
skill. A `WARN` line is advice. Lesson 2, Step 4 shows each kind of message on broken practice skills.

### Step 4 - Use the skills in Claude

**What:** you start Claude Code and ask questions that the skills can answer.

**Why:** to see the whole mechanism once. Claude reads the skill descriptions, chooses a skill,
runs the skill's Python script, and answers with the script's result.

**Run:**

```bat
claude
```

Then type these requests one at a time. After each one, look at the tools that Claude Code shows:
first **Skill** (with the skill's name), then **PowerShell** or **Bash** (with a `python ...` command).
Claude Code often folds the commands into one line, like `ran 3 shell commands`. Press **Ctrl+O** to
see each command, its output, and Claude's thinking. Press **Esc** to go back (Lesson 0, section 7):

```text
What skills are available?
Which region sold the most in data/sales.csv?
If a job starts on 2026-10-15, what date is 10 working days later?
Total up data/invoice.json including the discount and tax.
Build a pivot of amount by region and product from data/sales.xlsx.
Plot the monthly sales amount from data/sales.xlsx as a line chart.
Remind me to call the bank on 2026-10-16.
What's on my to-do list?
/clear-todos done
What is the capital of Australia?
```

**Expected result:** for example, "Which region sold the most" uses `analyzing-csv` and answers
North with 2,150. The last question uses **no** skill, because none fits. That is correct.

**If you see something else:** the first time Claude wants to use a skill, Claude Code asks your
permission: answer **Yes**. If the Excel or chart request says `Python package 'pandas' is not
installed`, you started `claude` without Step 1. Type `/exit` and start again from Step 1.

Type `/exit` when you are done.

### Step 5 (optional) - Test Claude's skill choices automatically

**What:** `tools\routing_eval.py` asks Claude a list of test questions (in `tools\routing_cases.json`).
For each question, it checks that Claude chooses the expected skill.

**Why:** Step 4 showed single examples. This test checks many questions at once. You see right
away if a change to a description made Claude choose wrongly. It uses real Claude runs, so it uses a
little of your Pro allowance.

**Run:**

```bat
python tools/routing_eval.py --limit 6
```

**Expected result:** a `PASS` line for each of the first 6 questions, and `6/6 routed as expected`.
Lesson 5 explains the output and how the test works.

### Step 6 (optional) - Run Claude from your own Python program

**What:** `agent\run_agent.py` is a Python program that runs Claude Code, with its skills, in the
background, through the Agent SDK.

**Why:** so you see how to build your own agent program on top of the same skills (Lesson 6).

**Run:** (the first command installs the SDK once; skip it if it is already installed)

```bat
python -m pip install -r agent\requirements.txt
```

```bat
python agent\run_agent.py --model haiku "Which region sold the most in data/sales.csv?"
```

**Expected result:** lines that start with `[init]`, `[skill]`, `[tool]`, `[claude]` and `[done]`.
They show each step Claude took. Lesson 6 explains them.

## Folder map

```text
.claude/skills/<name>/SKILL.md      the skills (description + instructions)
.claude/skills/<name>/scripts/*.py  the Python functions the skills run
data/                               sample inputs (sales.csv, sales.xlsx, ...); todos.json is created here
charts/                             PNG files made by the plotting-charts skill
lessons/                            the course
lessons/images/                     screenshots used in the lessons
tools/skills_lint.py                checks SKILL.md files for mistakes (free, offline)
tools/skill_sizes.py                shows the three loading levels of every skill as numbers (free)
tools/demo_bad_skills/              broken practice skills for the linter (never loaded by Claude)
tools/show_sdk_command.py           shows which claude.exe the Agent SDK starts, and with which options (free)
tools/route_preview.py              rough offline guess of the skill choice (free, a toy)
tools/routing_eval.py               real test: which skill does Claude pick? (claude -p; --sdk: the SDK; uses Pro allowance)
tools/routing_cases.json            the test questions and the expected skills
tools/run_cost.py                   one run: each step, its model, and the tokens (claude -p; --sdk: the SDK)
tools/model_mode_compare.py         Claude Code as the model: the same questions in several modes, right answers and tokens
tools/harness_profile_compare.py    non-coding data tasks: model only against Claude Code with tools, skills or everything
examples/skills/                    extra skills for Lesson 8 (calculator, argument demo); copied in when needed
tools/hooks/only_data_folder.py     hook for exercise 8 (blocks writes outside data/); off until you enable it
agent/ask_claude.py                 asks Claude a question, with only a Pro login (claude -p; --sdk: the SDK)
agent/api_equivalent.py             your Anthropic API call, done with Pro (claude -p; --sdk: the SDK)
agent/run_agent.py                  runs Claude Code with the skills, step by step (the SDK; --cli: claude -p)
agent/custom_tools_agent.py         gives Claude Python functions as tools (the SDK; --cli: claude -p)
agent/tutor_mcp_server.py           the same tools as a stand-alone MCP server, for the --cli way
agent/chat_agent.py                 several questions in one conversation (the SDK; --cli: claude -p --resume)
agent/guarded_agent.py              your Python rules allow or refuse each tool call (the SDK; --cli: claude -p)
agent/guard.py                      the rules of guarded_agent.py, as plain Python (tested)
agent/guard_hook.py                 the same rules as a hook script, for the --cli way
agent/effort_probe.py               shows the effort level in effect at each step (the SDK; --cli: claude -p)
agent/effort_hook.py                the effort hook, as a function (SDK way) and a hook script (--cli way)
agent/daily_report.bat              a scheduled job with claude -p only: no Python program, no SDK
tests/test_skill_scripts.py         automatic tests of every script
Claude_Code_Skills_Tutor.docx       this course as a Word file (+ .pdf), made for printing
```

## SKILL.md template

Copy this to start a new skill. Everything inside the box is the text of the file. The ```` ``` ````
lines belong to the file too: in a SKILL.md they mark command text, the same way as in this course.

````markdown
---
name: doing-the-thing
description: <Verb>s <objects> - <capability>, <capability>, <capability>. Use when the user asks
  <situations, words users say, file types>. Not for <a similar job> (use <other-skill>).
allowed-tools:
  - Bash(python *)
  - PowerShell(python *)
effort: low
---

# Doing the thing

<One line: why Claude should use the script instead of guessing.>

1. <First step - usually look at the input>:
   ```bash
   python "${CLAUDE_SKILL_DIR}/scripts/thing.py" inspect <file>
   ```
2. <Main action>:
   ```bash
   python "${CLAUDE_SKILL_DIR}/scripts/thing.py" do <args>
   ```
3. Report the numbers from the JSON output. If the output is `{"error": ...}`, fix the arguments as
   the message says and run again.

Details: [reference.md](reference.md)
````

**Sources** (Claude Code 2.1.x documentation, October 2026):
[Skills](https://code.claude.com/docs/en/skills) ·
[Agent SDK skills](https://code.claude.com/docs/en/agent-sdk/skills) ·
[Agent SDK custom tools](https://code.claude.com/docs/en/agent-sdk/custom-tools) ·
[Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
