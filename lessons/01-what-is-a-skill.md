# Lesson 1 - What a skill is

**Goal:** find out, by looking and running, what a skill is made of, why it is built that way, and
how Claude uses it.

**Before you start:** open cmd and type the start commands (Lesson 0): first
`C:\pyenvsmy\claudeclioct26\Scripts\activate`, then `cd /d "E:\may10\claudecodecli_and_python"`. Don't start
`claude` yet.

## The idea in one paragraph

A **skill** is a folder with instructions for Claude, and often a Python script. Claude Code reads
the short **description** of every skill at the start. When your request matches a description,
Claude reads that skill's instructions and follows them. In this course, the instructions say:
"run this Python script". So Claude runs the script, reads the result it prints, and answers you.
Python does the exact work (math, files, packages), and Claude does the understanding and the talking.

## Step 1 - See which skills this project has

**What:** you list the skill folders of this project.

**Why:** Claude Code finds skills **only** by their folders. If a skill is not in this list, Claude
Code doesn't know it.

**Run:** (`dir /b` lists the names in a folder, without dates and sizes)

```bat
dir /b .claude\skills
```

**Expected result:**

```text
analyzing-csv
analyzing-excel
analyzing-text
calculating-dates
calculating-invoices
clear-todos
converting-units
plotting-charts
tracking-todos
```

**How to read it:** every folder in `.claude\skills\` is one skill, and the folder name is the
skill's name. Claude Code looks in this folder when you start `claude` in the project folder.

## Step 2 - Look inside one skill

**What:** you list the files of the unit conversion skill.

**Why:** to see the two parts every skill in this course has: instructions for Claude, and a script.

**Run:**

```bat
dir /b .claude\skills\converting-units
```

```bat
dir /b .claude\skills\converting-units\scripts
```

**Expected result:**

```text
scripts
SKILL.md
```

```text
convert.py
```

**How to read it:**

| File | Required? | Who reads it | Purpose |
|---|---|---|---|
| `SKILL.md` | yes | Claude | the description, and the instructions: which command to run, and how to use its output |
| `scripts\convert.py` | no | nobody: Claude **runs** it | the exact work: conversion factors and math |

Some skills also have extra text files that Claude reads when needed. Try
`dir /b .claude\skills\analyzing-csv`: it also has `reference.md`.

## Step 3 - Read the SKILL.md file

**What:** you print the skill's instruction file.

**Why:** this one file decides **when** Claude uses the skill, and **what** Claude does then.

**Run:** (`type` prints a file)

```bat
type .claude\skills\converting-units\SKILL.md
```

**Expected result:** (shortened)

````text
---
name: converting-units
description: Converts physical quantities between units of length, mass, volume, speed, temperature, and digital data size (km to miles, kg to lb, °F to °C, liters to gallons, mph to km/h, MB to GiB) with exact factors. Use for every unit conversion request, even simple ones like miles to kilometers, and whenever the user asks "how many X in Y".
allowed-tools:
  - Bash(python *)
  - PowerShell(python *)
effort: low
---

# Converting units

Never do unit math in your head. Run the script; it is exact and handles aliases.

## Convert one value

```bash
python "${CLAUDE_SKILL_DIR}/scripts/convert.py" convert 100 km mi
```
...
````

**How to read it:** the file has two parts.

1. **The frontmatter: the settings between the two `---` lines.** It is written in YAML: one
   `key: value` per line.

   | Key | What it does | Why it is needed |
   |---|---|---|
   | `name:` | the skill's name. You can also type it as a command: `/converting-units` | it must match the folder name |
   | `description:` | what the skill does, and **when** to use it | Claude reads only this to decide whether the skill fits your request (Lesson 2) |
   | `allowed-tools:` | allows Claude to run `python ...` commands **without asking you**, while it uses this skill | otherwise Claude Code asks your permission for every script run |
   | `effort:` | how much Claude thinks while this skill runs: `low`, because the script does the work | the same model uses fewer tokens (Lesson 6, Part 6) |

2. **The instructions: everything after the second `---`.** This is written for Claude, in normal
   language. It says "never do unit math in your head, run the script", and shows the command. The
   lines with ```` ``` ```` are part of the file: they mark the command, so Claude sees exactly what
   to type.

**Check where the two `---` lines are:**

**Run:** (`findstr /n "^---"` prints, with line numbers, every line that starts with `---`)

```bat
findstr /n "^---" .claude\skills\converting-units\SKILL.md
```

**Expected result:**

```text
1:---
8:---
```

**Why it matters:** the first `---` must be on **line 1**. If anything comes before it, even an
empty line, Claude Code doesn't see the settings at all. Then the skill has no description. Lesson 2,
Step 4 shows how the linter catches this mistake.

## Step 4 - Run the script yourself, as Claude would

**What:** you type the same command that the SKILL.md tells Claude to run.

**Why:** to see **exactly** what Claude sees. If the script works for you, it works for Claude.

**Run:**

```bat
python .claude/skills/converting-units/scripts/convert.py convert 26.2 mi km
```

**How it works:** `convert` is the action, `26.2` the number, `mi` the unit you have, and `km` the
unit you want. The script looks up both units in its table, converts through meters, and prints the
result as JSON.

**Expected result:**

```text
{"value": 26.2, "from": "mi", "to": "km", "result": 42.164813, "category": "length"}
```

**How to read it:** this one line of JSON is everything Claude gets from the script. **JSON** is a
text format of `"name": value` pairs that both Python and Claude read reliably. Claude reads
`"result": 42.164813` and answers "about 42.16 km".

**Where the path comes from:** in the SKILL.md the command starts with
`"${CLAUDE_SKILL_DIR}/scripts/..."`. Before Claude sees the instructions, Claude Code replaces this
placeholder with the skill's folder (`E:\may10\claudecodecli_and_python\.claude\skills\converting-units`).
So the command finds the script, whatever folder Claude is working in.

**If you see something else:** `{"error": "unknown unit 'mile'", ...}` or similar means the script
doesn't know a unit name. Try `python .claude/skills/converting-units/scripts/convert.py units` to
list all units it knows.

## Step 5 - See the three loading levels as numbers

**What:** `tools\skill_sizes.py` measures how much of each skill Claude reads, and when.

**Why:** this is the most important idea of the course. Claude does **not** read all skills
completely. It reads each skill in three levels, and each level only when needed. That is why you
can have many skills without slowing Claude down.

**Run:**

```bat
python tools/skill_sizes.py
```

**Expected result:** (shortened)

```text
skill                  who starts it       level 1        level 2   level 3
                                       description   instructions   extra files (scripts are run, not read)
----------------------------------------------------------------------------------------------------
analyzing-csv          Claude or you     372 chars       29 lines   reference.md (49 lines), scripts/csv_tool.py (226 lines)
...
clear-todos            only you          107 chars       17 lines   -
converting-units       Claude or you     334 chars       31 lines   scripts/convert.py (222 lines)
...
----------------------------------------------------------------------------------------------------
Level 1 total (in EVERY request): 2,672 characters, about 668 tokens.
Level 2 is added only for the skill Claude chooses. Level 3 scripts never enter the context:
Claude runs them and reads only what they print.
```

**How to read it:** look at the `converting-units` row from left to right.

| Level | Column | When Claude sees it | For `converting-units` |
|---|---|---|---|
| 1 | description | **Always**, in every request, for every skill | 334 characters |
| 2 | instructions | Only after Claude has chosen this skill | 31 lines of SKILL.md |
| 3 | extra files | Only if the instructions send Claude there | `convert.py`: Claude **runs** it and sees only its output (Step 4), never its 222 lines of code |

A **token** is the unit in which Claude reads text: roughly 4 characters. All 9 skills together cost only
about 668 tokens per request (the last line). `clear-todos` says "only you": its description is not
in Claude's list at all. So it costs nothing until you type `/clear-todos`.

## Step 6 - Watch Claude use the skill

**What:** you start Claude Code and ask questions that the skill answers.

**Why:** to see the three levels happen: Claude matches the description (level 1), loads the
instructions (level 2), and runs the script (level 3).

**Run:**

```bat
claude
```

**Type in Claude,** one after the other:

1. `What skills are available?`
   **Expected:** Claude lists the 9 skills of this project, plus some built-in Claude Code skills.
2. `How many kilometers is a marathon (26.2 miles)?`
      **Expected:** first you see the **Skill** tool with `converting-units`. Claude chose it, because
   your question matched the description. Next you see the **PowerShell** (or **Bash**) tool with the
   `python ... convert.py convert 26.2 mi km` command: Claude followed the instructions. Last comes
   the answer: about 42.16 km (from the script's JSON). If the command is folded into a line like
   `ran 1 shell command`, press **Ctrl+O** to see it with its JSON output. Press **Esc** to go back
   (Lesson 0, section 7).
3. `/converting-units 5 kg lb`
   **Expected:** the same tools, and about 11.02 lb. This time you started the skill yourself, by its
   name, so Claude didn't need to match your words to a description.

**If you see something else:** if Claude answers question 2 without the Skill tool, it answered from
memory. That can happen with very easy questions. Lesson 5 shows how a description change fixed it.

Type `/exit` to go back to cmd.

## Step 7 - Where else skills can live

**What:** you look at your **personal** skills folder.

**Why:** a skill can belong to one project or to you. Where you put it decides who can use it.

**Run:** (`%USERPROFILE%` is your user folder, `C:\Users\<you>`)

```bat
dir /b %USERPROFILE%\.claude\skills
```

**Expected result** (on the course machine):

```text
synced
```

**How to read it:** a skill folder you put here works in **every** project on this computer.
`synced` holds skills copied from your claude.ai account. If you see `File Not Found`, you have no
personal skills yet, which is fine. There are three places for skills:

| Place | Folder | Who can use it |
|---|---|---|
| Project | `E:\may10\claudecodecli_and_python\.claude\skills\<name>\` | Anyone who starts `claude` in this project folder. If you copy the project, the skills come with it. |
| Personal | `C:\Users\<you>\.claude\skills\<name>\` | Only you, in every project |
| Plugin | inside an installed plugin | Anyone who installs the plugin. Its skills are named `/plugin-name:skill-name`. |

If a personal skill and a project skill have the **same name**, Claude Code uses the personal one and
ignores the project one. So give your skills unique names.

## Step 8 - A skill or something else?

**What:** you look at `CLAUDE.md`, another way to give Claude instructions.

**Why:** a skill is not always the right tool. Knowing the alternatives helps you choose.

**Run:**

```bat
type CLAUDE.md
```

**Expected result:** the project's rules, for example
`- Run skill scripts from the project root; sample inputs are in data/.`

**How it differs from a skill:** `CLAUDE.md` is read **fully at the start of every session**. A
skill's instructions are read **only when needed**. Choose like this:

| You want... | Use | Example in this course |
|---|---|---|
| Rules for **every** request in the project | `CLAUDE.md` | the file you just printed |
| Know-how and a script for **one kind** of task | a **skill** | `converting-units` |
| A helper for a **big reading job**, so your conversation stays small | a **subagent**: a second Claude with its own context window that returns only a summary | Lesson 9, exercise 6 |
| Your own **Python function** as a tool that Claude calls directly | an SDK `@tool`, or an MCP tool | Lesson 6, Part 2 |
| A rule that must **never** be skipped | a **hook**: Claude Code runs your check automatically, and Claude can't skip it | Lesson 9, exercise 8 |

**Next:** [Lesson 2 - How Claude picks the right skill](02-how-claude-picks-a-skill.md)
