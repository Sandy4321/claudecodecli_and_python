# Questions and answers

Test yourself: cover the answer, say yours, then compare. Each answer names the lesson step where
you saw it happen.

## Setup, Pro and seeing inside

**1. Do I need an API key to use Claude from Python?**
No. Claude Code holds your Pro login; `claude -p` and the Agent SDK both use it (Lesson 6, Part 3).

**2. What happens if the environment variable `ANTHROPIC_API_KEY` is set?**
Claude Code uses it instead of your Pro login, and that API account pays. In `claude -p` and the SDK,
this happens without asking. `set ANTHROPIC` shows whether it is set (Lesson 0, Step 8).

**3. Why must the venv be activated before I start `claude`?**
Skills run plain `python`, and Claude Code passes its PATH to them. Only the activated venv puts the
Python with pandas and matplotlib first (Lesson 0, Step 1; Lesson 7, Step 7).

**4. Why do I see dollar amounts if Pro is a flat price?**
They are API list-price estimates of each run. On Pro, nothing is charged. Read them as the size of a
run (Lesson 0, section 3).

**5. How do I see what Claude thinks and which commands it runs?**
Press Ctrl+O for the transcript view. To read the thinking text too, set
`"showThinkingSummaries": true` once in your settings (Lesson 0, Step 9; Lesson 0, Step 10).

## What a skill is, and how Claude chooses

**6. What are the three loading levels of a skill?**
Level 1, the description, is in every request. Level 2, the SKILL.md instructions, is read only when
the skill is chosen. Level 3, extra files, is read only when needed. Scripts are run, never read (Lesson 1,
Step 5).

**7. How much does a skill's long Python script cost in context?**
Nothing: Claude runs it and reads only what it prints. `convert.py` has 222 lines, but Claude sees one
line of JSON (Lesson 1, Step 5).

**8. How does Claude choose a skill?**
It compares your request with the names and descriptions of all skills, using the full language
model. Then it calls the Skill tool for the best fit, or uses no skill (Lesson 2, Step 1).

**9. What makes a good description?**
It says what the skill does, and has a "Use when ..." sentence with the words users really say. Its
last sentence, "Not for ... (use ...)", sends neighboring requests to the right skill (Lesson 2, Step 5).

**10. Why must "Not for ..." be the last sentence in this project?**
The word-counting tools (the preview, and the linter's overlap check) cut it off before they count:
a word counter can't read "not". Claude reads it fine (the header of `tools/skilllib.py`; Lesson 9,
Exercise 4).

**11. How do I make a skill that Claude never starts by itself?**
`disable-model-invocation: true`. Only you can start it, with `/name`. The course uses it for
`clear-todos`, which deletes data (Lesson 2, Step 6; Lesson 3, Step D5).

**12. Is the free word-counting preview (`route_preview.py`) a good test of routing?**
No, it is a rough guess. It finds descriptions that miss the users' words, but only
`routing_eval.py` shows what Claude really chooses (Lesson 2, Step 3).

## Skills that run Python

**13. Why let a script compute instead of Claude?**
Because the script is exact and testable. In a real run, Haiku did the invoice math itself and got
1,403.36. The script gives 1403.37 (Lesson 3, Pattern C, and the header of `invoice.py`).

**14. What should a skill script print?**
One line of JSON. On an error, it prints JSON with "error" and a "hint", and ends with exit code 1.
Then Claude can correct its command and try again (Lesson 3, Step A3).

**15. What are the five patterns of Lesson 3?**
A: one script, several commands. B: call any function by name (`fncli`). C: check the data first,
then calculate. D: data that is kept, and a skill only you can start. E: pip packages from your venv
(Lesson 3, Part 2).

**16. How does a skill find its script, wherever the project folder is?**
With `"${CLAUDE_SKILL_DIR}/scripts/x.py"`, in quotes, because the path may contain spaces (Lesson 3,
Step 2).

**17. How can Claude give a script text without writing a file?**
Through a pipe: `echo text | python text_stats.py stats -` (Lesson 3, Step A4).

**18. What does `allowed-tools: Bash(python *)` do?**
While the skill is active, Claude may run `python ...` commands without a permission prompt
(Lesson 3, Step 2).

## Many skills

**19. How many skills are too many?**
Every model-invocable description is in every request: 9 skills cost about 668 tokens. More skills
also make the choice harder, so give each skill one job and its own words (Lesson 4, Step 3).

**20. How can two skills share Python code?**
One skill calls the other's script by path: `clear-todos` runs
`"${CLAUDE_SKILL_DIR}/../tracking-todos/scripts/todo.py"` (Lesson 4, Step 4).

**21. Where do big reading jobs go?**
To a subagent: it reads in its own context window and returns only a short result (Lesson 4, Step 5).

## Testing

**22. Which three tests does the course use, and what does each prove?**
Unit tests prove the scripts compute right (free). The linter proves the SKILL.md files are correct
(free). The routing test proves Claude chooses the right skill (uses allowance) (Lesson 5, Test 1;
Lesson 5, Test 2; Lesson 5, Test 4).

**23. How do I run only the tests of one file?**
`-k` with a word from the test names, for example `-k ConvertingUnits` or `-k guard_hook`. Each
`.py` file's header names its own words (Lesson 5, Step 4).

**24. Why are some tests "skipped" with the system Python?**
They need pandas, which only the venv has. They are skipped, not failed, because a missing package is
a setup question (Lesson 5, Step 5).

**25. What do I do when a routing question fails?**
Read which skill Claude chose, and sharpen the descriptions of both skills. Then run the linter and
the routing test again. Lesson 5 shows a real example.

## Your own programs: `claude -p` and the SDK

**26. What does the Agent SDK really run?**
Its own copy of Claude Code (`claude.exe`, bundled in the pip package), with your login and skills.
It is not a different engine (Lesson 6, Step 2).

**27. Which system prompt does the SDK send by default?**
An empty one, not Claude Code's long instructions. `system_prompt={"type": "preset", "preset":
"claude_code"}` gives the normal behavior (Lesson 6, Step 2).

**28. How do I get every step from `claude -p`?**
`--output-format stream-json --verbose`: one JSON line per step. `run_agent.py --cli` reads them and
prints the same labels as the SDK way (Lesson 6, Step 11).

**29. When is `claude -p` the better choice?**
One command with nothing to install; `.bat` files and schedulers; text in through a pipe, the answer
into a file (Lesson 6, Step 12; Lesson 6, Step 13).

**30. When is the SDK the better choice?**
Conversations (one process stays open: 0.9 seconds per follow-up, against 5.6 with `--resume`); rules
that need your program's data; your functions as tools without a second program (Lesson 6, Step 16).

**31. Can `claude -p` hold a conversation?**
Yes: read `session_id` from the last JSON line, and pass `--resume <session_id>` with the next
question. Each question starts a new process (Lesson 6, Step 14).

**32. Why a PreToolUse hook, and not the SDK's `can_use_tool`, for rules?**
Claude Code asks `can_use_tool` only about calls that no allow rule covers, and a skill's
`allowed-tools` is such a rule. A hook runs before every matching call (Lesson 6, Step 15).

**33. How does a hook decide with `claude -p`?**
It is a separate program, switched on with `--settings`. It gets the planned call as JSON on stdin. It
answers with JSON on stdout (`permissionDecision`), or blocks with exit code 2 (Lesson 6, Step 15;
Lesson 9, Exercise 8).

**34. How do I give Claude my own functions as tools?**
With the SDK: `@tool` and `create_sdk_mcp_server`, inside your program. With `claude -p`: a small MCP
server program, started with `--mcp-config` (Lesson 6, Step 8).

**35. What is MCP, really?**
JSON messages, one per line: `initialize`, `tools/list`, `tools/call`. `tutor_mcp_server.py` does it
in about 60 lines of standard-library Python (Lesson 6, Step 8).

**36. Is there anything only the SDK can do?**
Offering only some skills (`skills=[...]`): the SDK says it in its start-up message, and `claude -p`
has no flag for it. Everything else works both ways (Lesson 6, Step 11).

**37. How do I turn my Anthropic API code into Pro code?**
`model` becomes `--model`, effort becomes `--effort`, `max_tokens` becomes
`CLAUDE_CODE_MAX_OUTPUT_TOKENS`, `system` becomes `--system-prompt`, no tools becomes `--tools ""`
(Lesson 6, Step 20).

## Effort and cost

**38. What is effort?**
How much Claude thinks before it acts or answers: low, medium, high, xhigh or max. The same model
thinks less at low (Lesson 6, Step 17).

**39. Can thinking be switched off?**
No need to try: the 5.5 models always think adaptively, as much as the question needs. Effort makes
that thinking shorter or longer (Lesson 6, Step 20).

**40. Which effort setting wins?**
The environment variable `CLAUDE_CODE_EFFORT_LEVEL` beats everything. A skill's `effort:` beats the
session's `--effort`, `/effort` or `effortLevel` (Lesson 6, Step 23).

**41. The skill's text joins the same conversation. How can it have its own effort?**
Claude Code sends each request with the effort in force at that moment. While the skill works, its
requests carry the skill's effort. After its answer, the session's effort is back (Lesson 6, Step 24).

**42. How do I give a skill its own model?**
`context: fork` with `model: haiku`: the skill runs in a subagent with that model and effort
(Lesson 6, Step 25).

**43. How much does low effort save?**
It depends on the question. In the real runs, `low` used 11% to 44% less thinking than `high`. In the
careful two-copies test on Opus, the difference was small, and all four answers were right
(Lesson 6, Step 26).

**44. Where do the tokens of a short skill run go?**
Mostly into the context, read again at every step: 110,413 tokens re-read, against 31 tokens of
thinking (Lesson 6, Step 28).

**45. Is a cheaper model a free saving?**
No. Haiku answered 3 of 20 routing questions without the right skill; Opus passed all 20. Test the
cheaper model on your own jobs first (Lesson 0, section 4).

## pip packages and messy input

**46. How does a skill use pandas without breaking on other computers?**
Its packages are in `requirements.txt`, installed into the venv. The script starts with an import
guard: when a package is missing, it prints a helpful error and ends with exit code 2 (Lesson 7,
Step 7).

**47. Why should the script be strict when users type messy text?**
Claude is good at understanding "4 radnias sinus". Python is good at computing. Claude translates the
text into a strict command, and the strict script refuses anything unclear (Lesson 8, Step 4).

**48. What are `$ARGUMENTS`, `$0` and `$1` in a SKILL.md?**
`$ARGUMENTS` is everything typed after `/name`. `$0` is the first word, `$1` the second: counting
starts at 0. Quotes make several words one argument (Lesson 8, Step 6).

**49. Is `$0` a hack?**
No, it is documented ("Pass arguments to skills"). Write a backslash before the dollar sign when you
mean a real price like $5 in a SKILL.md. The linter warns you (Lesson 8, Step 6; Lesson 2, Step 4).

## Building a real harness

**50. What are the parts of an agent harness?**
Exact tools, routing, running from code, rules and safety, memory, cost control, quality gates, and
observability. The summary, "What you have learned", names the file for each.

**51. Where do I start with a job from my work?**
Write and test the Python function first. Then wrap it in a skill, write five routing questions, add
a hook for the rule that must never break, and measure the cost.

**52. What does Claude Code add that a plain API call doesn't have?**
A harness around the same model: the agent loop, built-in tools, skills, context management (caching,
compaction, memory, subagents), permissions and hooks, sessions, MCP, and every step visible (Lesson 6,
"Why go through Claude Code at all").

**53. Is there evidence that the harness matters?**
Yes. Anthropic runs almost all of its major agent loops on this harness. On Terminal-Bench 2.0, the same
model scored between about 58% and 82%, depending only on the harness. Claude Code was not the top
harness there. Its strength is that it is general, mature, and yours with Pro.

**54. When is a plain LLM call the better choice?**
For one question and one answer. The harness adds thousands of context tokens, so `ask_claude.py` turns
the tools off and uses a short system prompt (Lesson 6, Step 20).

**55. Is Claude Code only a tool for writing code?**
No. Its defaults are made for software work, but its harness is general. Anthropic renamed the SDK to
"Agent SDK", and built Cowork, its agent for non-coding work, the same way. None of this course's 9 skills
writes code. The real limit: it works through files and commands on a computer.

**56. Who outside Anthropic says that calling Claude Code is a good idea?**
Simon Willison called Claude Code a tool for general computer automation (October 2025). An
independent comparison (MindStudio, May 2026) recommends the Agent SDK for agents with many steps, and the
plain API for one-call tasks. That is the same rule as this course.

**57. May I run these programs at work with my Pro login?**
For your own, individual use, yes. For a product, a service for other people, or a company's production
jobs, Anthropic's terms ask for an API key (Claude Console, or Bedrock, Vertex AI or Foundry). The same
programs run with `ANTHROPIC_API_KEY` set (Lesson 0, Step 8).

**58. What is the difference between using Claude Code as the model and as the runtime?**
As the model, your program sends one question with the tools off, like `ask_claude.py`: you mostly gain
the door (your Pro login). As the runtime, your program hands over a whole job, like `run_agent.py`. Then
the harness runs the loop, the tools, the skills and the rules. Decide who owns the loop, so you don't build
a loop inside a loop (Lesson 6, "When the harness is the right choice").

**59. Who else uses an agent CLI as the runtime of a general agent?**
OpenClaw runs its agent turns through a local Claude Code or Gemini CLI, with its own tools passed in over
MCP. Anthropic sells the harness itself as Managed Agents, and OpenAI offers its Codex agent to programs
through the Codex SDK.

**60. How do I use Claude Code only as the model, and should I?**
Switch off what it adds: `--tools ""`, `--strict-mcp-config` (it also removes your account's connector
tools), `--system-prompt`, `--setting-sources ""` and `--safe-mode`. `ask_claude.py --strict` does all of it.
Do it when your program owns the loop and the tools. You keep your Pro login and lose the harness. In the
measured runs, Claude Code's own prompt didn't make the answers better (Lesson 6, "Using Claude Code only
as the model").

**61. When does Claude Code, with everything on, beat a plain model call on work that isn't coding?**
When the job needs more than the model's head: exact arithmetic on more than a few lines, files it must
find itself, data too big to paste, several steps. On a 300-row table, it was right 6 times out of 6
against 5, at the same cost per right answer and twice as fast. On small files, it was no more right, at
about 10 times the cost (Lesson 6, "Three questions").

**62. How do I make Claude Code beat a plain model call?**
Give it a way to compute, and tell it to use it, in words that match your allow rule. One appended
sentence, "compute every number with Python", made the lean profile right every time on the big table.
With Python allowed but no such sentence, Claude worked in its head, or wrote `awk`, which the rule
refused (Lesson 6, "Three questions").

**63. How do I cut Claude Code's tokens and keep that advantage?**
Keep its prompt and loop, and switch off what the job doesn't use: `--strict-mcp-config`, `--safe-mode`,
`--tools "Read,Bash,PowerShell"` with a python-only allow rule, `--disable-slash-commands`. That cut the
cost per right answer by 70 to 80% against everything on. Send small, easy questions to a plain call
(Lesson 6, "Three questions").

**64. Why call Claude Code instead of the model's API at all?**
Three gains in one. The door: your Pro login for every model request of your programs, not only for
coding. The harness: the loop and the tools make hard requests come back right. On a 3,000-row table,
Claude Code was right 4 times out of 4 in about 17 seconds, and a plain call once, in about 2 minutes. The dial:
switch off what a request doesn't use, from 39,143 down to 849 input tokens for one plain question
(Lesson 6, "The big idea").

**65. Can switching parts of Claude Code off make it worse?**
Yes, like cheap tires on an expensive car. Allowed only python commands, Claude Code wrote `awk`, which
was refused: right 3 times out of 6. Hindsight's one-turn calls failed now and then because its tools
were allowed none but still loaded. Switch off only what the request doesn't use, say in one sentence
what to use instead, pin the model, and measure (Lesson 6, "The big idea").

**66. Is calling Claude Code instead of the API an established practice?**
Yes. Anthropic runs almost all of its major agent loops on this harness. The Python Agent SDK was
downloaded 29.9 million times in September 2026. OpenClaw, Hindsight, promptfoo, OpenHarness, NodeTool
and a Vercel AI SDK provider plug Claude Code in where a model API would go. That doesn't prove
a win on every request: measure yours (Lesson 6, "Who else builds agents this way").

**67. How do I know a step of this course worked on my computer?**
Compare your output with the "Expected result": every one is a real run. And run the HOW TO TEST
section of any `.py` file.
