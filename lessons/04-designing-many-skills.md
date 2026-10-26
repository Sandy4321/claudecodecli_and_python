# Lesson 4 - Designing an agent with many skills

**Goal:** plan many skills so that Claude never confuses them, and understand why each design rule
exists. You check each rule on this project's 9 skills.

**Before you start:** open cmd, `C:\pyenvsmy\claudeclioct26\Scripts\activate`, and
`cd /d "E:\may10\claudecodecli_and_python"`.

## The idea in one paragraph

With one skill, Claude only decides "skill or no skill". With many, it must also decide **which**
one, from the names and descriptions alone (Lesson 2). Each extra skill makes that choice harder,
and adds its description to every request. So a good set of skills has clear names, one job per
skill, descriptions that don't share trigger words, and a small total size. This lesson shows how
to check each of these.

## Step 1 - List all skill names

**What:** you print the `name:` line of every SKILL.md.

**Why:** the names are part of Claude's menu. A clear name helps Claude choose, and helps you type `/name`.

**Run:** (`/s` searches all subfolders, `/b` keeps lines that begin with `name:`)

```bat
findstr /s /b "name:" .claude\skills\SKILL.md
```

**Expected result:**

```text
.claude\skills\analyzing-csv\SKILL.md:name: analyzing-csv
.claude\skills\analyzing-excel\SKILL.md:name: analyzing-excel
.claude\skills\analyzing-text\SKILL.md:name: analyzing-text
.claude\skills\calculating-dates\SKILL.md:name: calculating-dates
.claude\skills\calculating-invoices\SKILL.md:name: calculating-invoices
.claude\skills\clear-todos\SKILL.md:name: clear-todos
.claude\skills\converting-units\SKILL.md:name: converting-units
.claude\skills\plotting-charts\SKILL.md:name: plotting-charts
.claude\skills\tracking-todos\SKILL.md:name: tracking-todos
```

**How to read it:** these names follow three naming rules:

| Rule | Examples | Why |
|---|---|---|
| Skills that Claude chooses by itself use a verb with "-ing" | `analyzing-csv`, `calculating-dates`, `converting-units` | the name reads like an ability: "Claude is good at converting units" |
| The skill that only you start uses a command word | `clear-todos` | you type it like a command: `/clear-todos` |
| The folder name and the `name:` are the same | `analyzing-csv\SKILL.md` has `name: analyzing-csv` | only one name to remember. The linter warns when they differ (Lesson 2, Step 4) |

Never use vague names like `helper`, `utils` or `tools`: they say nothing about the job.

## Step 2 - Give every skill one job, with its own words

**What:** a planning table with one row per skill. Make it **before** you write many skills.

**Why:** two skills that answer the same kind of request compete. Then Claude picks one of them more
or less by chance. The table makes such overlaps visible on paper.

**How to fill it:**

- **Job:** what the skill does, in two or three words.
- **Trigger words:** the words people type when they need this job. They must appear in the description.
- **Must NOT catch:** the neighbor job that could be confused with it. The description says this in
  its "Not for ..." sentence.

**This project's table:**

| Skill | Job | Trigger words people type | Must NOT catch |
|---|---|---|---|
| `converting-units` | unit conversion | convert, how many X in Y, km, lb, °F, GiB | money and currencies |
| `analyzing-csv` | tables in .csv files | .csv, column, total per, top 5, average | Excel files, charts, prose |
| `analyzing-excel` | Excel workbooks | .xlsx, sheet, pivot, Excel | .csv files, charts |
| `plotting-charts` | pictures of data | chart, graph, plot, bar, line | plain number answers |
| `analyzing-text` | prose | words, readable, reading time, essay, article | tables |
| `calculating-dates` | calendar math | days until, deadline, working days, weekday | saving tasks |
| `calculating-invoices` | money totals | invoice, quote, VAT, discount, bill | unit conversion |
| `tracking-todos` | the task list | remind me, add a task, my list, mark done | deleting the list |
| `clear-todos` | deleting tasks | none: only you start it | everything Claude starts by itself |

**Check it on two neighbors.** `analyzing-csv` and `analyzing-excel` are the most similar pair:
both answer questions about tables.

**Run:**

```bat
findstr /b "description:" .claude\skills\analyzing-csv\SKILL.md .claude\skills\analyzing-excel\SKILL.md
```

**Expected result:** (the ends of the two lines)

```text
...analyzing-csv\SKILL.md:description: Summarizes and aggregates tabular data in .csv files - ... Not for .xlsx workbooks (use analyzing-excel), charts (use plotting-charts), or prose .txt documents (use analyzing-text).
...analyzing-excel\SKILL.md:description: Reads Excel workbooks (.xlsx) with pandas - ... Not for .csv files (use analyzing-csv) or charts (use plotting-charts).
```

**How to read it:** each one names its **file type** (`.csv`, `.xlsx`). Each one also ends with a
"Not for ..." sentence that sends the other file type to the other skill. That is how two similar
skills stay separate: the file type in your request decides.

**When two of your skills share trigger words,** you have two choices:

| Choice | When | Example |
|---|---|---|
| **Merge** them into one skill | they are really one job | `csv-stats` and `csv-totals` (Lesson 2, Step 4): overlap 1.00, the same job |
| **Separate** them clearly | they are different jobs | different nouns, different file types, and a "Not for ..." sentence, like the pair above |

The linter measures this for you: `python tools/skills_lint.py` warns when two descriptions share
too many words.

**Split** a skill into two when its instructions have parts that are never needed together, or when
its SKILL.md grows past about 500 lines. **Why:** after Claude chooses a skill, its whole SKILL.md
is loaded (level 2). Parts that are not needed only cost tokens.

## Step 3 - Keep the menu small

**What:** you measure the total size of all descriptions.

**Why:** every description is in **every** request (level 1, Lesson 1). More text in every request
means more allowance used, and a longer menu for Claude to choose from.

**Run:**

```bat
python tools/skill_sizes.py
```

**Expected result:** (the last lines)

```text
Level 1 total (in EVERY request): 2,672 characters, about 668 tokens.
```

**How to read it:** 9 skills cost about 668 tokens per request, which is small. But 100 skills with
350-character descriptions would cost about 35,000 characters, nearly 9,000 tokens in every request.

**Ways to keep it small:**

| Way | How | Why it helps |
|---|---|---|
| Short descriptions | 200 to 400 characters, with the main job in the first sentence | enough for Claude to choose, nothing more |
| "Only you" skills | `disable-model-invocation: true` | they are not in the menu at all, so they cost nothing (`clear-todos` shows "only you" in the output) |
| Rarely used skills by name only | in `.claude\settings.json`: `{"skillOverrides": {"skill-name": "name-only"}}` | the description is left out of the menu, only the name stays |
| Long details in a second file | a link in SKILL.md to `reference.md` | Claude opens it only when it needs it (level 3) |
| Check with Claude Code | `/doctor` shows how much room the menu takes, and `/skill-doctor` lists skills you never use | you find the big and the unused skills |

**See the second-file way:** `analyzing-csv` does it. Run:

```bat
findstr "reference.md" .claude\skills\analyzing-csv\SKILL.md
```

**Expected result:**

```text
For the exact JSON shape of each command, see [reference.md](reference.md).
```

Put **all** such links in SKILL.md itself, and never link from `reference.md` to yet another file.
**Why:** Claude sometimes reads only the beginning of a file it reaches through a second link.

## Step 4 - Share Python code between skills

**What:** you look at how `clear-todos` uses the script of another skill.

**Why:** with many skills, some need the same Python code. You must decide where that code lives.

**Run:**

```bat
findstr "CLAUDE_SKILL_DIR" .claude\skills\clear-todos\SKILL.md
```

**Expected result:**

```text
   python "${CLAUDE_SKILL_DIR}/../tracking-todos/scripts/todo.py" clear --all
   python "${CLAUDE_SKILL_DIR}/../tracking-todos/scripts/todo.py" clear --done-only
```

**How it works:** `clear-todos` has no script of its own. `${CLAUDE_SKILL_DIR}` is
`.claude\skills\clear-todos`. `..` goes one folder up, to `.claude\skills\`, and from there into
`tracking-todos`. This works only while both folders sit side by side.

**Your options:**

| Option | How | Good for | The catch |
|---|---|---|---|
| Each skill has its own copy (the normal case) | every skill folder has its own `scripts\` | skills you give away one by one | a fix must be made in every copy |
| Use the neighbor's script | `${CLAUDE_SKILL_DIR}/../other-skill/scripts/x.py`, as above | skills that always stay together in one project | breaks if you copy one skill alone |
| An installed package | `pip install` your own package into the venv, and the skill runs `python -m mypackage ...` | the same code in many projects | needs the venv, like Pattern E |

Whichever you choose, keep the logic in **functions** (Lesson 3, the rules at the end). The tests in
`tests\` and the programs in `agent\` import exactly the functions that the skills run.

## Step 5 - Big reading jobs go to a subagent

**The problem:** if a skill must read many files or long logs, all that text goes into your
conversation. Claude re-reads the conversation for every new message, so every later message gets
slower and more expensive.

**The solution:** a **subagent**, a helper Claude with its own context window. It does the
reading there, and returns only a short summary to your conversation.

**How:** two lines in the frontmatter:

```yaml
context: fork        # run this skill in a separate helper
agent: Explore       # the built-in helper that can read files but not change them
```

The helper doesn't see your conversation, so the skill's instructions must contain everything it needs.

**Try it:** Lesson 9, exercise 6 gives a complete skill, and shows how `/context` proves that your
conversation stayed small.

## Step 6 - Rules that must never be skipped

**The problem:** Claude follows a skill with judgment, and can skip a step, for example when it thinks
a step is not needed.

**The solution:** some rules must hold **every** time, for example "never write outside `data\`". For
such a rule, use a **hook**: a small program that Claude Code runs automatically before an action. If the hook says
no, the action doesn't happen, and Claude can't skip it.

**Try it:** Lesson 9, exercise 8 has a tested hook.

**Also:** put the most important instructions **at the top** of a SKILL.md. **Why:** in very long
conversations, Claude Code shortens old content and keeps only the first part of each loaded skill
(about 5,000 tokens).

## Step 7 - Use your skills in more places

**What:** where a skill folder can live, and what changes there.

**Why:** a good skill is useful in more than one project.

**Run:**

```bat
dir /b %USERPROFILE%\.claude\skills
```

**How to read it:** this is your personal folder (Lesson 1, Step 7). To use one of your skills in
**every** project, copy its folder there.

| Where | How | Note |
|---|---|---|
| This project | `.claude\skills\` in the project folder | goes with the project when you copy it |
| All your projects | `C:\Users\<you>\.claude\skills\` | only on this computer |
| Other people | package the skills as a **plugin** | started as `/plugin-name:skill-name` |
| claude.ai, Claude API | upload the skill folder | only 6 frontmatter fields are allowed there: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools` |

Fields that only Claude Code understands (`disable-model-invocation`, `argument-hint`, `effort`, `context`,
`paths`, ...) cause an error on claude.ai and the API. The linter lists them.

**Run:**

```bat
python tools/skills_lint.py
```

**Expected result:** look at the `clear-todos` lines:

```text
[ok] clear-todos  (/command only, description 107 chars)
   INFO  Claude Code-only keys ['argument-hint', 'disable-model-invocation', 'effort'] (fine here; remove before uploading to claude.ai/API).
```

**How to read it:** `INFO` is not a problem here. It only reminds you to remove these three lines if
you upload this skill to claude.ai.

## Checklist before you add a skill

| Check | Why | How to check |
|---|---|---|
| Its job doesn't overlap another skill's job | overlapping skills compete | your Step 2 table, and no overlap warning from `skills_lint.py` |
| Its description says what it does, has "Use when ...", and ends with "Not for ..." if a similar skill exists | the description is all Claude has for choosing | `skills_lint.py` warns when "Use when" is missing |
| Its name uses "-ing" if Claude may choose it, or a command word if only you start it | a clear name helps Claude and you | Step 1 |
| If it deletes, publishes or costs money, it has `disable-model-invocation: true` | such actions must be your decision | Lesson 2, Step 6 |
| Its SKILL.md is under 500 lines; long details are in a linked `reference.md` | the whole SKILL.md is loaded when chosen | `skill_sizes.py` |
| Its script prints JSON, gives errors with a hint, and has tests | Claude repeats what the script prints | `python -m unittest discover -s tests` (Lesson 5) |
| Its SKILL.md sets `effort:`: `low` if the script does all the work, `high` if Claude must interpret the results | the same model thinks only as much as the job needs | `python agent\effort_probe.py --model opus "..."` (Lesson 6, Part 6) |
| `"${CLAUDE_SKILL_DIR}"` is in quotes, and `allowed-tools` is set | paths with spaces, and no permission question per run | `skills_lint.py` |
| You added test questions for it, and the routing test passes | only a real test shows what Claude chooses | `python tools/routing_eval.py` (Lesson 5) |

**Next:** [Lesson 5 - Testing skills that run Python](05-testing-skill-routing.md)
