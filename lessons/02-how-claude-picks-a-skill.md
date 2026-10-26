# Lesson 2 - How Claude picks the right skill

**Goal:** see, by trying it, how Claude chooses a skill from its description, and understand why it
works that way. Then learn to write descriptions that lead to the right choice.

**Before you start:** open cmd, `C:\pyenvsmy\claudeclioct26\Scripts\activate`, and
`cd /d "E:\may10\claudecodecli_and_python"`.

## How the choice works, step by step

1. When a session starts, Claude Code collects the **name and description** of every skill it may
   offer (level 1, Lesson 1, Step 5).
2. It gives Claude a tool called **Skill**, together with this list of names and descriptions.
3. For each request, Claude compares your words **and their meaning** with the descriptions. If one
   fits, Claude calls the Skill tool with that name. You see this as the **Skill** line in Claude Code.
4. Only now does Claude Code load that skill's instructions (level 2). Claude follows them, for
   example by running the Python script.
5. If no description fits, Claude doesn't call the Skill tool, and answers by itself.

So the **description is the only thing Claude has** for choosing. Everything in this lesson follows
from that.

## Step 1 - See exactly what Claude sees before it chooses

**What:** you print the description line of every skill.

**Why:** these lines are the "menu" Claude chooses from (point 1 above). If a word is not here,
it can't help Claude choose.

**Run:**

```bat
findstr /s /b "description:" .claude\skills\SKILL.md
```

**How it works:** `findstr` searches text in files. `/s` searches the folder and all its subfolders,
so `.claude\skills\SKILL.md` means "every file called SKILL.md below `.claude\skills`". `/b` keeps
only lines that **begin** with `description:`.

**Expected result:** (each line is shortened here)

```text
.claude\skills\analyzing-csv\SKILL.md:description: Summarizes and aggregates tabular data in .csv files - column types, ...
.claude\skills\analyzing-excel\SKILL.md:description: Reads Excel workbooks (.xlsx) with pandas - lists sheets and columns, ...
.claude\skills\analyzing-text\SKILL.md:description: Measures prose in .txt or .md documents - word, sentence and paragraph counts, ...
.claude\skills\calculating-dates\SKILL.md:description: Calculates with calendar dates - days or weeks between two dates, ...
.claude\skills\calculating-invoices\SKILL.md:description: Builds and checks invoices and quotes from line items - ...
.claude\skills\clear-todos\SKILL.md:description: Deletes tasks from data/todos.json - finished tasks only by default, ...
.claude\skills\converting-units\SKILL.md:description: Converts physical quantities between units of length, mass, volume, ...
.claude\skills\plotting-charts\SKILL.md:description: Draws bar and line charts as PNG images from .csv or .xlsx data ...
.claude\skills\tracking-todos\SKILL.md:description: Keeps a persistent to-do list for this project in data/todos.json - ...
```

**How to read it:** each line is `file:line found`. `clear-todos` is in the files, but Claude
doesn't see it in its menu: Step 6 shows why. The rest of each SKILL.md is **invisible** until Claude
has chosen the skill. So words that appear only in the instructions can't help Claude choose.

## Step 2 - Watch Claude choose

**What:** you ask Claude five questions and watch which skill it chooses.

**Why:** to see that Claude chooses by meaning, and that "no skill" is a correct choice too.

**Run:** `claude`, then type each request below, one at a time. For each one, look at which skill
appears with the **Skill** tool.

**Expected result:** the right column shows what happened on the course machine.

| Type this | Skill Claude chose |
|---|---|
| `Which region sold the most in data/sales.csv?` | `analyzing-csv` |
| `Build a pivot of amount by region and product from data/sales.xlsx.` | `analyzing-excel` |
| `Plot the monthly sales amount from data/sales.xlsx as a line chart.` | `plotting-charts` |
| `If a job starts on 2026-10-15, what date is 10 working days later?` | `calculating-dates` |
| `What is the capital of Australia?` | no skill (Claude just answers) |

**How to read it:**

- Claude understands **meaning**, not only words. The chart request names an `.xlsx` file, but asks
  for a *picture*, so it went to `plotting-charts`, not to `analyzing-excel`.
- Every description ends with a "Not for ..." sentence that names the neighbor skill. For example,
  `analyzing-excel` says: *"Not for .csv files (use analyzing-csv) or charts (use plotting-charts)."*
  That sentence tells Claude directly where the border between two similar skills is.
- When no description fits, Claude answers without a skill. That is correct.

**If you see something else:** Claude can choose differently from the table on another day, because
its answers vary a little. If a skill is chosen wrongly again and again, Step 7 shows what to do.

Type `/exit`.

## Step 3 - Try the free word-counting preview (and see its limits)

**What:** `tools\route_preview.py` guesses the skill by counting the words that your request and each
description share.

**Why:** it doesn't contact Claude, so it is free and instant. It warns you early when a description
lacks the words people type.

**How it works:** it uses **BM25**, a standard method of search engines. A shared word scores more
points when it is rare among the descriptions (like "csv"), and fewer when many descriptions contain
it (like "data"). It ignores small words like "the", and it ignores the "Not for ..." sentence,
because a word counter can't understand "not".

**Run:**

```bat
python tools/route_preview.py "Which region sold the most in data/sales.csv?"
```

**Expected result:**

```text
Request: Which region sold the most in data/sales.csv?

   2.80  analyzing-csv          shared words: csv, data
   2.79  plotting-charts        shared words: csv, data
   1.87  analyzing-text         shared words: most

  (not scored, /command only: clear-todos)

  -> Close call between the top two. Make their descriptions more distinct.
```

**How to read it:** the three best skills, with their score and the shared words. The word counter
says "close call", because both descriptions contain "csv" and "data". But in Step 2, **Claude**
chose `analyzing-csv` without trouble. Claude understands that "which region sold the most" asks for
a number, not a picture. So the preview is only a rough warning, never the final answer.

**Run:**

```bat
python tools/route_preview.py "What is the capital of Australia?"
```

**Expected result:**

```text
   0.00  tracking-todos         shared words: -
   0.00  plotting-charts        shared words: -
   0.00  converting-units       shared words: -

  -> No clear match. Claude would most likely answer without a skill.
```

**How to read it:** no description shares any word with the request. That fits: no skill is needed.

**How to use the preview:** if a **typical** request for your skill shares **no** words with its
description, the description probably lacks the words people really type. Add them.

## Step 4 - Find mistakes in descriptions with the linter

**What:** the folder `tools\demo_bad_skills\` contains four broken practice skills. Claude Code never
loads them, because they are not in `.claude\skills\`. They are only there for the linter.

**Why:** to learn the typical mistakes, and the linter message for each, on skills where breaking
something does no harm.

**Run:**

```bat
python tools/skills_lint.py tools/demo_bad_skills
```

**How it works:** without a folder, the linter checks `.claude\skills`. With a folder, it checks that
folder instead.

**Expected result:**

```text
[ok] csv-stats  (auto + /command, description 151 chars)

[ok] csv-totals  (auto + /command, description 145 chars)

[check] Helper_Tool  (auto + /command, description 30 chars)
   ERROR name must be lowercase letters, digits and single hyphens.
   WARN  name 'Helper_Tool' differs from folder 'helper' (both will work as /commands; confusing).
   WARN  Write the description in third person ('Converts...'), not 'I can' / 'you can'.
   WARN  Add a trigger clause such as 'Use when the user asks ...' so Claude knows WHEN to pick it.
   WARN  Body line 4: quote the path - "${CLAUDE_SKILL_DIR}/..." - it may contain spaces.
   WARN  Body line 4: '$5' is replaced by word 6 typed after the skill name ($0 is the first). Write \$5 for a literal dollar sign.
   ERROR Referenced file does not exist: scripts/helper.py

[check] no-frontmatter  (auto + /command, description 0 chars)
   ERROR Frontmatter must start with '---' on the very first line.

Description overlap (pairs that may compete for the same request):
   WARN  csv-stats <-> csv-totals: 1.00 shared words ['analyze', 'average', 'column', 'csv', 'data', 'file', 'ranking', 'statistic', 'total']

4 skills, 3 error(s).
```

**How to read it:** one block per skill. `[ok]` has no problem of its own, and `[check]` has at
least one. `ERROR` must be fixed. `WARN` is strong advice. The last line counts only the errors: 3.

Now look at the file behind most of the messages:

```bat
type tools\demo_bad_skills\helper\SKILL.md
```

```text
---
name: Helper_Tool
description: I can help you with your data.
---

# Helper

Run python ${CLAUDE_SKILL_DIR}/scripts/helper.py and tell the user the price is $5.
```

| Message | The mistake | Why it is a problem |
|---|---|---|
| `ERROR name must be lowercase...` | the name `Helper_Tool` has a capital letter and `_` | names may only use `a-z`, `0-9` and `-`. Claude Code may not load the skill |
| `WARN name ... differs from folder` | the name is not the folder name `helper` | two different names for one skill confuse you and Claude |
| `WARN Write the description in third person` | `I can help you with your data.` | the description is read as part of a list about skills. "I can" is unclear: who is "I"? |
| `WARN Add a trigger clause` | no "Use when ..." sentence | Claude can't know **when** to use the skill. "your data" fits almost any request |
| `WARN Body line 4: quote the path` | `${CLAUDE_SKILL_DIR}/scripts/helper.py` without `"` | if the project folder has a space, for example `E:\my skills`, the command breaks into two words |
| `WARN Body line 4: '$5' is replaced...` | `the price is $5` | in a SKILL.md, `$0`, `$1`, ... are placeholders for the words you type after `/name`, counted from 0 (Lesson 8). `$5` becomes the 6th word, usually nothing. Write `\$5` |
| `ERROR Referenced file does not exist` | `scripts/helper.py` is mentioned, but the file isn't there | Claude would run a command that fails |
| `ERROR Frontmatter must start with '---'` | `no-frontmatter` starts with an empty line | Claude Code doesn't see the settings at all (Lesson 1, Step 3). The skill has no name and no description |
| `WARN csv-stats <-> csv-totals: 1.00` | both descriptions use the same words (run `type tools\demo_bad_skills\csv-stats\SKILL.md` and `...csv-totals\SKILL.md`) | overlap `1.00` means all their important words are shared. Claude can't tell them apart. Merge them into one skill, or make them clearly different |

**Now check the real skills:**

**Run:**

```bat
python tools/skills_lint.py
```

**Expected result:** (the end)

```text
Description overlap (pairs that may compete for the same request):
   none above 0.30 - descriptions are well separated

9 skills, 0 error(s).
```

## Step 5 - How to write a good description

**What:** you look at a real description and take it apart.

**Why:** you will write descriptions for your own skills, and they decide everything (see the top of
this lesson).

**Run:**

```bat
findstr /b "description:" .claude\skills\analyzing-csv\SKILL.md
```

**Expected result:**

```text
description: Summarizes and aggregates tabular data in .csv files - column types, missing values, min/max/mean/median, group-by totals and averages, top-N rows by a column. Use when the user asks about the contents, statistics, totals, or rankings in a CSV file. Not for .xlsx workbooks (use analyzing-excel), charts (use plotting-charts), or prose .txt documents (use analyzing-text).
```

**How to read it:** it has the three parts of a good description:

| Part | In this description | Why |
|---|---|---|
| 1. **What it does,** with concrete abilities | "Summarizes and aggregates tabular data in .csv files - column types, missing values, min/max/mean/median, group-by totals ..." | Claude can match requests like "what's the average" or "totals per region" |
| 2. **When to use it,** with the words people type | "Use when the user asks about the contents, statistics, totals, or rankings in a CSV file." | tells Claude directly which requests belong here |
| 3. **What it is NOT for,** naming the neighbor skills | "Not for .xlsx workbooks (use analyzing-excel), ..." | draws the border to similar skills. Keep it as the **last** sentence: the course's tools skip from "Not for" to the end |

**More rules,** each with a good and a bad example:

| Rule | Good | Bad |
|---|---|---|
| Write about the skill, not "I" or "you" | "Converts units..." | "I can help you convert..." |
| Name concrete abilities | "group-by totals, top-N rows" | "works with data" |
| Use the words people type, and file types | ".csv", "VAT", "due date", "chart" | only your own technical terms |
| Put the main job first | "Converts units ..." | a long introduction first |

**One more rule, learned by testing: say if the skill is also for easy questions.** In a test,
"Convert 26.2 miles to kilometers." got **no** skill: Claude knew the answer (42.16 km) and didn't
use the skill. The fix was one sentence in the description:

**Run:**

```bat
findstr /b "description:" .claude\skills\converting-units\SKILL.md
```

**Expected result:** (the end of the line)

```text
... with exact factors. Use for every unit conversion request, even simple ones like miles to kilometers, and whenever the user asks "how many X in Y".
```

After this change the test passed. Lesson 5 shows the before and after results.

**Size limits:**

| Limit | Why |
|---|---|
| a `name` has at most 64 characters | it is also the `/command` name |
| keep a `description` under 1,024 characters | Claude Code shows at most 1,536 characters and cuts the rest, so put the most important sentence first |
| all descriptions together fit in about 1% of Claude's context window | they are in every request. With 9 skills that is easy (Lesson 1, Step 5 showed 2,672 characters). With hundreds of long descriptions, Claude Code would list your least-used skills without their descriptions |

## Step 6 - A skill that only you can start

**What:** you look at the one setting that makes `clear-todos` a "manual only" skill.

**Why:** some skills must never run because Claude **thinks** it should: deleting, publishing,
spending money. You decide when they run.

**Run:**

```bat
findstr /b "disable-model-invocation" .claude\skills\clear-todos\SKILL.md
```

**Expected result:**

```text
disable-model-invocation: true
```

**How it works:** this line tells Claude Code not to put `clear-todos` in the list it gives to Claude
(point 1 at the top). That is why it was missing from Claude's menu in Step 1. Claude can't choose
what it doesn't see. You still can, by typing `/clear-todos`.

**Try it:** start `claude` and type `Delete all my todos.`.

**Expected result:** Claude can't use `clear-todos`. It uses `tracking-todos` instead (chosen in the
course test). Its instructions tell Claude to ask you to type `/clear-todos` yourself. Then type
`/clear-todos done`. Now the skill runs, because you started it, and it deletes the finished tasks.

**All the options:**

| Setting in the frontmatter | You can type `/name` | Claude can choose it | In Claude's menu |
|---|---|---|---|
| (no setting: the normal case) | yes | yes | yes |
| `disable-model-invocation: true` | yes | **no** | no |
| `user-invocable: false` | no | yes | yes |

`user-invocable: false` is the opposite: only Claude uses the skill, and it is hidden from your `/`
menu. Use it for background knowledge that makes no sense as a command.

## Step 7 - If the wrong skill (or none) is chosen

**What:** a checklist, from the cheapest check to the most expensive.

**Why:** a wrong choice has a few typical causes, and each has a free check.

| # | Check | How | What it finds |
|---|---|---|---|
| 1 | Is the skill loaded at all? | in `claude`, type `What skills are available?` | a skill missing from the list is not loaded |
| 2 | If not loaded: is the file correct? | `python tools/skills_lint.py` | a missing first `---`, a wrong name, a broken path |
| 3 | If loaded but **not chosen**: does it share words with the request? | `python tools/route_preview.py "your request"` | no shared words: add the words people type, and a "Use when ..." sentence |
| 4 | If **another** skill was chosen | read both descriptions | add a "Not for ..." sentence to the skill that was wrongly chosen |
| 5 | If chosen **too often** | read the description | make it narrower, or make the skill "only you" (Step 6) |
| 6 | Measure the result | `python tools/routing_eval.py` (Lesson 5) | how many test questions go to the right skill |

You can always force a skill: start your message with `/skill-name`.

**Next:** [Lesson 3 - Skills that run Python code](03-skills-that-run-python.md)
