# Lesson 8 - Messy input: Claude reads, Python computes

**Goal:** a skill whose Python script needs clean, exact input. But people type requests in any
order, with numbers as words, and with typos. You see how the SKILL.md makes Claude turn messy text
into one clean command. You also learn exactly how the placeholders `$ARGUMENTS`, `$0`, `$1`, ... work,
and when to use them.

**Before you start:** open cmd, `C:\pyenvsmy\claudeclioct26\Scripts\activate`, and
`cd /d "E:\may10\claudecodecli_and_python"`.

## The idea in one paragraph

Each side does what it is good at. **Claude** understands language: "seven and five add",
"4 radnias sinus" and "squera root 67" are clear to it, in any order, with typos. **Python** computes
exactly, but only from clean input. So the script accepts one strict form,
`calc.py <operation> <numbers> [--unit ...]`, and the SKILL.md teaches Claude to translate the request
into that form. If Claude gets it wrong, the script answers with a JSON error and a hint, and Claude
fixes its call (Lesson 3, Step A3).

## Step 1 - Install the two example skills

**What:** the folder `examples\skills\` has two skills: `calculating-math` (the calculator) and
`showing-arguments` (a small demo for Step 6). They are not in `.claude\skills\`, so Claude Code
doesn't load them until you copy them there.

**Why they are separate:** the other lessons show outputs for the project's 9 skills. When you have
finished this lesson, you remove the copies again (Step 7), or keep the calculator if you like it.

**Run:**

```bat
xcopy /e /i examples\skills\calculating-math .claude\skills\calculating-math
```

```bat
xcopy /e /i examples\skills\showing-arguments .claude\skills\showing-arguments
```

**Expected result:**

```text
examples\skills\calculating-math\SKILL.md
examples\skills\calculating-math\scripts\calc.py
2 File(s) copied
examples\skills\showing-arguments\SKILL.md
1 File(s) copied
```

(If you ran the unit tests before, Python's `__pycache__` files are copied too, and the count is higher.)

**Check them:** `python tools/skills_lint.py` now ends with `11 skills, 0 error(s).` It shows three
`WARN` lines for `showing-arguments`: Step 6 explains them.

## Step 2 - Run the strict script yourself

**What:** you call `calc.py` with clean input, and with input it doesn't accept.

**Why:** to see what the script expects, and what Claude gets back when its call is wrong.

**Run:**

```bat
python .claude/skills/calculating-math/scripts/calc.py add 7 5
```

```bat
python .claude/skills/calculating-math/scripts/calc.py cos 45 --unit degrees
```

```bat
python .claude/skills/calculating-math/scripts/calc.py cos 23
```

```bat
python .claude/skills/calculating-math/scripts/calc.py add seven 5
```

**Expected result:**

```text
{"operation": "add", "numbers": [7.0, 5.0], "unit": null, "result": 12.0}
{"operation": "cos", "numbers": [45.0], "unit": "degrees", "result": 0.7071067812}
{"error": "'cos' needs --unit degrees or --unit radians.", "hint": "If the user gave no unit, use degrees and say so in the answer."}
{"error": "Not a number: ['seven', '5'].", "hint": "Write numbers as digits: 'seven' -> 7, 'twenty-three' -> 23."}
```

**How it works:** the operations are a table in the script: how many numbers each one takes, and the
Python function that computes it:

```python
OPERATIONS = {
    "add": (2, lambda a, b: a + b),
    "subtract": (2, lambda a, b: a - b),
    "multiply": (2, lambda a, b: a * b),
    "divide": (2, lambda a, b: a / b),
    "sqrt": (1, math.sqrt),
    "sin": (1, math.sin),
    "cos": (1, math.cos),
}
ALIASES = {"plus": "add", "times": "multiply", "sine": "sin", "sinus": "sin", "root": "sqrt", ...}
```

**Why the script is strict:**

| Rule in the script | Why |
|---|---|
| numbers only as digits | turning "twenty-three" into 23 is language work: Claude does it better than a word list |
| `sin` and `cos` need `--unit` | 23 degrees and 23 radians give very different results. The script never guesses, so Claude must decide, and the SKILL.md tells it how |
| a fixed number of numbers per operation | `add 7` is a mistake, not a request; the error says so |
| a few other names (`plus`, `sinus`, `root`) | cheap to accept, and it saves Claude a retry |
| every error has a `hint` | Claude reads the hint and fixes its call by itself |

## Step 3 - Read the SKILL.md: how it teaches the translation

**Run:**

```bat
type .claude\skills\calculating-math\SKILL.md
```

**How to read it,** part by part:

| Part of the file | What it does | Why |
|---|---|---|
| `description:` with "in any word order, with numbers written as words ("seven") or with typos ("sinus", "squere root")" | tells Claude **when** to choose the skill: also for messy requests | without these words, a request like "4 radnias sinus" may not look like math (Lesson 2) |
| `effort: low` | Claude thinks little while the skill runs | the translation is easy; the script does the math (Lesson 6, Part 6) |
| "Never compute the result yourself" | Claude runs the script even for "7 + 5" | otherwise Claude answers easy questions from memory (Lesson 5) |
| `What the user typed after /calculating-math ...: $ARGUMENTS` | puts your typed text into the instructions | explained in Step 6 |
| "Find the three parts": operation, numbers, unit | turns a vague job into three small decisions | clear steps are followed more reliably than "understand the request" |
| the rules for order and missing units | "subtract 5 from 7" is 7 - 5; no unit means degrees, said in the answer | these are the cases where a guess would give a wrong number |
| the table "The user writes / Command" | eight examples of messy text and the right command | examples teach the pattern faster than rules alone |
| "say how you read the request" | the answer shows the interpretation | you see at once if Claude misread "23 cosine" |

## Step 4 - Messy input, started with `/calculating-math`

**What:** you type the skill's name and then the messy text.

**Run:** start `claude`, and type each line:

```text
/calculating-math seven and five add
/calculating-math 4 radnias sinus
/calculating-math squera root 67
```

**Expected result:** an answer like `sin 4 rad = -0.7568` for the second line. Press **Ctrl+O** to see
the command Claude built from your text (Lesson 0, section 7).

To demonstrate smart query processing by the LLM, we use typos on purpose in the math queries:
"radnias" for radians and "squere" for square.

**All nine of the examples,** real runs on the course machine (with `claude -p` and Haiku, about
$0.003 each as an API-price estimate):

| You typed after `/calculating-math` | Command Claude ran (after `calc.py`) | Answer (first line) |
|---|---|---|
| `seven and five add` | `add 7 5` | 7 + 5 = 12 |
| `add seven and five` | `add 7 5` | 7 + 5 = **12** |
| `23 cosine` | `cos 23 --unit degrees` | cos 23° = 0.9205 |
| `cosine of 45 degrees` | `cos 45 --unit degrees` | cos 45° = 0.7071 (0.7071067812 to 10 decimal places) |
| `sinus 3 radians` | `sin 3 --unit radians` | sin 3 rad = 0.1411 |
| `4 radnias sinus` | `sin 4 --unit radians` | sin 4 rad = -0.7568 |
| `45 squere root` | `sqrt 45` | The square root of 45 is **6.7082039325**. |
| `squera root 67` | `sqrt 67` | The square root of 67 is **8.1853527719**. |
| `34 square root` | `sqrt 34` | √34 = 5.8309518948 |

**How to read it:** every request became one clean command, and every number came from the script.
"23 cosine" had no unit, so Claude used degrees, as the SKILL.md says. It said so in a later line of
its answer ("I read "23 cosine" as the cosine of 23 with no unit given, so I used degrees").

## Step 5 - Messy input, and Claude chooses the skill

**What:** the same kind of requests, without `/calculating-math`. Claude must recognize that they are
math, choose the skill, and translate them.

**Run:** in `claude`, type:

```text
4 radnias sinus
```

**Expected result** (a real run with Opus: its steps, and the answer):

```text
claude-opus-5-5    thinks
claude-opus-5-5    Skill calculating-math
claude-opus-5-5    Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/calculating-math/sc...
claude-opus-5-5    writes the answer
answer: I took your request as the sine of 4 radians.  **sin(4 rad) = -0.7568024953**
```

The command was `calc.py sin 4 --unit radians`. In the same test, `seven and five add` and
`squera root 67` also went to the skill by themselves, and gave 12 and 8.1853527719.

**How to read it:** the description's words "in any word order", "numbers written as words" and
"typos" let Claude match these requests to the skill (Lesson 2). Without the `/name`, the run also has
the step where Claude chooses the skill, so it costs a little more.

## Step 6 - `$ARGUMENTS`, `$0`, `$1`: how arguments reach a skill

**What:** when you type `/skill-name some words`, Claude Code puts "some words" into the skill's text
before Claude reads it. It is not magic, and not a hack: it is documented in the Claude Code skills
documentation, in the section "Pass arguments to skills". Claude Code does it the same way as it
replaces `${CLAUDE_SKILL_DIR}` (Lesson 1, Step 4).

**The placeholders** (from the documentation):

| Placeholder | Becomes |
|---|---|
| `$ARGUMENTS` | everything you typed after the skill name, exactly as typed |
| `$0` | the **first** word. Counting starts at 0 |
| `$1`, `$2`, ... | the second, third, ... word |
| `$ARGUMENTS[0]`, `$ARGUMENTS[1]`, ... | the same as `$0`, `$1`, ... |
| `$issue` | a named argument, if the frontmatter has `arguments: [issue, branch]`: `$issue` is the first word, `$branch` the second |

Words are split like in a shell: text in quotes counts as **one** argument. To write a real dollar
sign followed by a digit, like a price of \$5, write `\$5`.

**See it:** `showing-arguments` only repeats the placeholders. Its SKILL.md says:

```text
Reply with exactly these four lines and nothing else:

ALL: [$ARGUMENTS]
FIRST: [$0]
SECOND: [$1]
THIRD: [$2]
```

**Run:** in `claude`, type each line:

```text
/showing-arguments seven and five add
/showing-arguments "seven and five" add
```

**Expected result** (two real runs):

```text
ALL: [seven and five add]
FIRST: [seven]
SECOND: [and]
THIRD: [five]
```

```text
ALL: ["seven and five" add]
FIRST: [seven and five]
SECOND: [add]
THIRD: [$2]
```

**How to read it:**

- `$ARGUMENTS` is always the whole text. `$0`, `$1`, `$2` are single words, counted from 0.
- With quotes, `"seven and five"` was one argument: `$0`.
- There was no third argument, so `$2` stayed as it was: the documentation says an indexed
  placeholder without an argument "stays in the content unchanged".
- The linter warns about each `$0`, `$1`, `$2` in this file (`WARN ... '$0' is replaced by word 1 typed
  after the skill name`). Here they are wanted. In most skills, a `$` before a digit is a mistake,
  like a price written as `$5` (Lesson 2, Step 4).

**Which one for messy input?** `$ARGUMENTS`. With `seven and five add`, `$0` is "seven", `$1` is "and"
and `$2` is "five". The positions mean nothing, because people don't type in a fixed order. So the
calculator gives Claude the whole text with `$ARGUMENTS`, and Claude finds the parts. Use `$0`, `$1`, ...
only for commands with a fixed order, like the documentation's example
`/migrate-component SearchBar JavaScript TypeScript` with `Migrate the $0 component from $1 to $2.`

**And when Claude chooses the skill itself?** The documentation says that both you and Claude can pass
arguments, but not in detail how Claude fills them. Don't depend on them: Claude always has your
message in the conversation. That is why the calculator's line says "(empty if you chose this skill
yourself)", and why Step 5 worked without `/calculating-math`.

## Step 7 - Clean up

**What:** remove the two copies, so the other lessons' outputs match again (9 skills).

**Run:**

```bat
rmdir /s /q .claude\skills\calculating-math
```

```bat
rmdir /s /q .claude\skills\showing-arguments
```

The originals stay in `examples\skills\`. The unit tests check `calc.py` there: run
`python -m unittest discover -s tests -k CalculatingMath -v` (5 tests).

## Summary

| You want | Do this | Shown in |
|---|---|---|
| exact results from messy requests | a strict script, and a SKILL.md that teaches Claude to translate the request into one clean command | Steps 2 to 4 |
| Claude to choose the skill for messy requests | describe the messiness in the description: any order, words for numbers, typos | Step 5 |
| your typed text inside the instructions | `$ARGUMENTS` | Step 6 |
| fixed-order arguments | `$0`, `$1`, ... (counted from 0), or named `arguments:` | Step 6 |
| a dollar sign before a digit | `\$5` | Step 6 |

**Next:** [Lesson 9 - Exercises](09-exercises.md)
