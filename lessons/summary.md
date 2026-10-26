# What you have learned

You started as a user of Claude Code. You finish as someone who can **build the harness around an
AI agent**: the tools it uses, the rules it must follow, the tests that prove it works, the program
that runs it, and the numbers that show what it costs. Real companies need this work when they
put agents into production. You have done each part with your own hands, on your own machine, with
real outputs.

## Your achievements

| You can now | And you have proved it, because you |
|---|---|
| Make an agent compute **exactly**, with your Python | ran the same script Claude runs, compared outputs, and saw Claude repeat the script's numbers (Lesson 3) |
| Design **many skills** that don't compete | wrote descriptions with a "Not for ..." boundary, and checked overlaps with the linter (Lesson 4) |
| **Prove** which skill Claude chooses | ran 20 real routing questions, and read every PASS and FAIL (Lesson 5, Test 4) |
| **Test** an agent for free | ran 74 unit tests, broke a script on purpose, and read the failure (Lesson 5, Step 2) |
| Run Claude **from your own programs, with only Pro** | used `claude -p` and the Agent SDK, with the same jobs both ways (Lesson 6, Part 4) |
| Decide **when Claude Code beats a plain model call** | measured five setups on the same data tasks: a plain call for small questions, a lean runtime with one compute rule for tables, at a quarter of the cost (Lesson 6, "Three questions") |
| Move **API code to Pro** | translated model, effort, max_tokens and usage line by line (Lesson 6, Step 20) |
| **Enforce rules** the model can't skip | stopped a file write outside `data\` with a hook, and watched Claude adapt (Lesson 6, Step 15) |
| Give Claude **your functions as tools** | served them in-process and as a stand-alone MCP server (Lesson 6, Step 8) |
| **Control cost** with the same model | set an effort level per skill, and measured the thinking tokens (Lesson 6, Step 26) |
| **See inside** every run | read thinking and commands with Ctrl+O, the effort level with a hook, and the tokens with `run_cost.py` |
| Use **pip packages** safely | ran the same skill with and without the venv, and saw the helpful error instead of a crash (Lesson 7) |
| Handle **messy input** | let Claude translate "4 radnias sinus" into a strict command that a script checks (Lesson 8) |

## The parts of an agent harness, and your ready solution for each

You didn't build these parts from zero. Claude Code is a harness that is already built and used every day,
and you learned to use it from your own programs. On public benchmarks, the harness alone moved the same model by
more than 20 points (Lesson 6, "Why go through Claude Code at all"). What you add is your part: your skills,
your rules, your tools and your tests. You are in good company. Anthropic runs almost all of its major
agent loops on this harness, and its Python Agent SDK was downloaded 29.9 million times in
September 2026. OpenClaw, Hindsight and promptfoo plug Claude Code in where a model API would go. And
OpenAI offers its Codex agent to programs through an SDK (Lesson 6, "The big idea").

An agent in a real company is more than a prompt. It has the parts below. For each one, you have a
working, tested example in the project folder.

| Part | What it does in a real system | Your ready solution | Lesson |
|---|---|---|---|
| Exact tools | calculations, lookups and file work that must be right every time | skills with scripts; `@tool` functions; an MCP server | 3, 6 |
| Routing | the right tool for each request, among many | descriptions with "Use when" and "Not for"; `routing_eval.py` | 2, 4, 5 |
| Running from code | start the agent from a program, a `.bat` file or a scheduler | `claude -p` programs and SDK programs, both ways | 6 |
| Rules and safety | what the agent may never do | hooks (`guard.py`, `only_data_folder.py`), `allowed-tools`, skills only you can start | 3, 6, 9 |
| Memory | conversations and data that last | `ClaudeSDKClient`, `--resume`, the to-do list file | 3, 6 |
| Cost control | the same results for less allowance | `effort:` per skill, the model per job, `run_cost.py` | 0, 6 |
| Quality gates | catch mistakes before users do | linter, 74 unit tests, routing test, the HOW TO TEST section of each file | 5 |
| Observability | know what happened, step by step | Ctrl+O, `stream-json` steps, hook lines, token reports | 0, 6 |

## Copy-paste solutions for your work

Each row is a job you may have at work, and the folder or file to copy. Change the part in the last
column. Keep the structure, the tests and the checks.

**At work, use an API key.** Your Pro login is for your own, individual use. For a product, a service
for other people, or a company's production job, run the same programs with an API key from the Claude
Console or a cloud provider. Use it under Anthropic's Commercial Terms (Lesson 6, "When the harness is the
right choice"). The code doesn't change; only who pays does.

| Your job needs | Copy | Change |
|---|---|---|
| Exact numbers in answers: prices, units, dates | `.claude\skills\converting-units\` | the functions, the description |
| A library of functions Claude can call by name | `calculating-dates\scripts\fncli.py` with your functions | your typed functions and their docstrings |
| Check the data before acting (orders, payments) | `.claude\skills\calculating-invoices\` | the checks in `validate()` |
| Data that lasts, plus a delete that only a person may start | `tracking-todos\` and `clear-todos\` | the fields of a record |
| Excel and CSV reports, charts | `analyzing-excel\`, `plotting-charts\`, with `requirements.txt` | column names, chart types |
| Messy text from users | `examples\skills\calculating-math\` | the operations and the "user writes / command" table |
| Claude as an LLM inside a Python program | `agent\ask_claude.py` | the system prompt, the JSON schema |
| Existing Anthropic API code, now on Pro | `agent\api_equivalent.py` | `MODEL`, `EFFORT`, `PROMPT` |
| An agent job from code, with each step logged | `agent\run_agent.py` (`--cli` without the SDK) | the allowed tools, `max_turns` |
| A chat backend with follow-up questions | `agent\chat_agent.py` | where the questions come from |
| Company rules for commands and files | `agent\guard.py` with `guarded_agent.py` or `guard_hook.py` | the rules in `Guard.check()` |
| Internal functions or APIs as tools | `agent\custom_tools_agent.py`, `agent\tutor_mcp_server.py` | the `@tool` functions, or the server's `TOOLS` table |
| A nightly report with no Python program | `agent\daily_report.bat` | the prompt, the schedule |
| A quality gate for your skills | `tools\skills_lint.py`, the tests, `tools\routing_eval.py` | `tools\routing_cases.json` |
| The cost of a job, and where it goes | `tools\run_cost.py`, `agent\effort_probe.py` | the prompt |

## `claude -p` or the SDK: the rule you now know

The surprise of Lesson 6 is that **neither way always wins**. Both run the same Claude Code, so the
answers are the same. What differs is how much your program takes part.

| `claude -p` is better when | The SDK is better when | Both work equally well for |
|---|---|---|
| you want one command and nothing to install | the program holds a **conversation** (0.9 seconds per follow-up, against 5.6) | one question from Python |
| the job runs from a `.bat` file or a scheduler | your **rules** need the program's own data and memory | showing each step while it happens |
| text goes in through a pipe and comes out in a file | your **functions** should be tools without a second program | a routing test, a cost measurement |
| the computer can't get the SDK | you want each step as a Python object | |

**Rule of thumb:** start with `claude -p`. Switch to the SDK as soon as your program must take part
while Claude works. Every program of the course can do both, so you can compare them on your own job.

## The numbers to remember

| Number | Meaning | Lesson |
|---|---|---|
| about 668 tokens | all 9 skill descriptions together, in every request; the scripts cost nothing | 1 |
| 3 of 20 | routing questions Haiku answered without the right skill; Opus passed all 20 | 0 |
| 1,403.36 against 1403.37 | Haiku doing invoice math by itself, against the script: one cent off | `invoice.py` header |
| 849 against 39,143 | input tokens of one plain question: every switch off, against Claude Code's defaults | 6 |
| 0.9 against 5.6 seconds | a follow-up question with the SDK, against `claude -p --resume` | 6 |
| 110,413 | context tokens re-read during one short skill run; the thinking was 31 | 6 |
| 12% to 15% | how much more Opus thought at `high` than at `low`, on the same skill; all answers right | 6 |
| 74 | unit tests that check every script and program, for free | 5 |

## What to do next, at work

1. Pick one repetitive job that needs exact results. Write its Python function first, and test it.
2. Wrap it as a skill: a description with "Use when" and "Not for", and the command to run.
3. Write five real questions for `routing_cases.json`, and run the routing test.
4. Add a hook for the rule that must never be broken.
5. Run the job from a `.bat` file with `claude -p`, or from your program with the SDK, and measure
   its cost with `run_cost.py`. Lower the effort where the script does the work.
6. Before it serves other people or runs in production, switch it to your company's API key.

You now know what most Claude Code users never see: what happens inside each step, and how to make
it exact, safe, tested and affordable.
