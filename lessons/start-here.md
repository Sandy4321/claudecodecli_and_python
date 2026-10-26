# Start here: what this course gives you

Most people use Claude Code like a chat: they type a request, read the answer, and hope it is right.
This course takes you much further. When you finish it, you can **build, test and control an AI
agent that does real work with your own Python code**. You need only Windows and a Claude Pro
subscription. You will not just know about these things. You will have run each one yourself and
seen the real output, and you keep working code that you can copy into your own projects.

## What you will be able to do

| After this course, you can | Typical use without it | Where you learn it |
|---|---|---|
| Make Claude **run your Python** for exact answers, instead of calculating by itself | trust the model's arithmetic, which can be a cent off | Lesson 3 |
| Give one agent **many skills** that don't compete, and **prove** that Claude picks the right one | write a description and hope | Lessons 2, 4 and 5 |
| **Check every skill for free** before you use it: a linter, 74 unit tests, a routing test | find the mistakes when users do | Lesson 5 |
| Call Claude **from your own Python programs with only Pro**, no API key, in two ways: `claude -p` and the Agent SDK | believe that an API key is needed | Lesson 6, Part 3 |
| Use **Claude Code instead of a direct model call** in your own agent: trimmed for easy requests, the whole harness for hard ones | call the model's API, and build the loop, the tools and the checks yourself | Lesson 6, "The big idea" |
| Choose between `claude -p` and the SDK for each job, and switch every program between them | use one way for everything | Lesson 6, Part 4 |
| Move your **Anthropic API code** (model, effort, max_tokens, usage) to Pro | pay for the API separately | Lesson 6, Step 20 |
| Hold a **conversation with follow-up questions** from a program | start from zero with every question | Lesson 6, Step 14 |
| Enforce **your own rules** on every command and file change, with hooks the model can't skip | write "please don't" into the prompt | Lesson 6, Step 15 |
| Give Claude **your own functions as tools**, inside your program or as a stand-alone MCP server | not possible without a big framework | Lesson 6, Step 8 |
| **Save allowance with the same model**: an effort level per skill, and the thinking tokens measured | switch to a weaker model, or never think about it | Lesson 6, Part 6 |
| **See every step** Claude takes: its thinking, each command, each effort level, each token | see only the final answer | Lesson 0, section 7 |
| Use **pip packages** such as pandas and matplotlib in skills, safely, with a venv | "it works on my machine" | Lesson 7 |
| Turn **messy, misspelled user input** into strict, testable commands | let the model do everything, untested | Lesson 8 |

## What surprises most people

These are the findings that change how you work. The course proves each one with real runs.

| Most people think | What you will see for yourself | Proof |
|---|---|---|
| Calling the model's API directly is the most capable way | Claude Code wraps the same model in a **harness**: agent loop, tools, skills, context management, rules, sessions. On a public benchmark the harness alone moved the same model from about 58% to 82% | Lesson 6, "Why go through Claude Code at all" |
| The Agent SDK is a separate, more powerful engine | it starts **the same Claude Code program** (`claude.exe`), with the same login and skills | Lesson 6, Step 2 |
| The SDK is always the better way for programs | **`claude -p` is often better**: nothing to install, works from `.bat` files and schedulers, text in and text out | Lesson 6, Steps 12 and 13 |
| `claude -p` can do everything the SDK can | it can, but the SDK is **much better for conversations** (0.9 seconds per follow-up against 5.6). It is also better for rules or tools that live in your program | Lesson 6, Step 14 |
| Scripting Claude needs an API key | **a Pro subscription is enough**. But if `ANTHROPIC_API_KEY` is set, it quietly switches the bill to that API account | Lesson 0, section 1 |
| A long script makes a skill expensive | **scripts cost nothing in context**: Claude runs them and reads only their output | Lesson 1, Step 5 |
| To save allowance you need a cheaper model | **the same model with lower effort** thinks less; a skill can set its own effort | Lesson 6, Step 22 |
| Most tokens are Claude's thinking and answer | for a short job, most tokens are the **context read again at every step** | Lesson 6, Step 28 |
| A good description is enough | only a **routing test with real questions** shows what Claude chooses: Haiku chose no skill in 3 of 20, Opus passed all 20 | Lesson 0, section 4; Lesson 5, Test 4 |
| Instructions in a skill are rules | Claude can still decide otherwise; **only a hook enforces** a rule | Lesson 6, Step 15 |
| Claude Code is a tool for programmers only | its harness is **general**: none of the course's 9 skills writes code; Anthropic built its non-coding agent, Cowork, the same way | Lesson 6, "When the harness is the right choice" |
| A Pro login can run your company's agents | Pro is for **your own, individual use**; products and company services need an API key, and the same programs run with one | Lesson 6, "When the harness is the right choice" |
| Claude Code's own instructions make even a plain call smarter | with the tools off, Claude Code's prompt brought no gain in a measured test, at about 4 times the tokens. One flag, `--strict-mcp-config`, cut a plain call from about 4,300 to 870 tokens | Lesson 6, "Using Claude Code only as the model" |
| Allow Claude Code to run Python, and it will compute | **tools alone didn't**: Haiku worked in its head, or wrote commands the allow rule refused. One appended sentence made it compute: right every time on a 300-row table, at a quarter of a plain call's cost per right answer | Lesson 6, "Three questions" |
| `$1` is the first argument of a skill | **`$0` is the first**: counting starts at 0 | Lesson 8, Step 6 |
| A permission callback sees every command | the SDK's `can_use_tool` **never sees** commands that a skill's `allowed-tools` approved; a hook does | Lesson 6, Step 15 |

## What you get in the project folder

Everything in this course runs, and stays yours to copy:

- **9 working skills** that run Python: unit conversion, CSV and Excel analysis, text statistics,
  dates and working days, invoices, a to-do list, charts.
- **7 programs in `agent\`** that call Claude from Python, with their helpers (hook scripts and a tool
  server). Each of them, and the two measuring tools, works in both ways: the SDK and `claude -p`.
  One option switches between them.
- **Tools** that check skills (a linter), measure their size and cost, and test Claude's choice.
- **74 unit tests** that check all of it for free.
- **A header in every `.py` file**: what it does, why, how it works, how to run it, how to test it
  (with the expected output), what to do when something goes wrong, and which files it changes.

The last part of the course, **"What you have learned"**, maps each of these to a job you may have at work.

## How to read this book

| You have | Read |
|---|---|
| One evening | Lesson 0 ("Start here (every time)"), Lesson 1, Lesson 3, Part 1, Lesson 6, Steps 9 to 11 and Step 16, then the **cheat sheet** |
| A weekend | Lessons 0 to 9 in order. Every step has the same parts: **What**, **Why**, **Run**, **Expected result** and **How to read it** |
| A question later | the **cheat sheet**, the **questions and answers**, the appendices, and the header of each `.py` file |

Every "Expected result" is a real output from the course machine. Compare yours with it: when they
match, you know the step worked.
