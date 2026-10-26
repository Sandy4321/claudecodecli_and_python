# Lesson 6 - Your own agent program with the Claude Agent SDK

**Goal:** run Claude Code, with its skills, from your own Python program. You will also give Claude
your own Python functions as tools, and ask Claude questions from Python, with only your Pro login.
Part 4 does the same jobs with `claude -p` and with the SDK, so you see when each one is the better choice.
Part 5 shows how to set the reasoning effort, to use less of your allowance. It also translates a
typical Anthropic API call into Pro code (Step 20). Part 6 shows how each
skill sets its own effort, with the same model.

**Before you start:** open cmd, `C:\pyenvsmy\claudeclioct26\Scripts\activate`, and
`cd /d "E:\may10\claudecodecli_and_python"`. Run every command of this lesson in that window.

## The idea in one paragraph

Until now **you** typed into Claude Code. In this lesson **your Python program** does it. There is no
second way to reach Claude here. With only a Pro plan (no API key), every request goes through the
Claude Code program, which holds your login. Your Python program starts Claude Code **in the
background**, sends it a question, and reads back each step. The **Claude Agent SDK** is a Python
package that does this for you. `claude -p` is the same thing without the package.

## The big idea: Claude Code instead of a direct model call

**What:** your Python agent sends its requests for the model to Claude Code (`claude -p` or the Agent
SDK) instead of to the model's API. That is more than a way to spend your Pro allowance on every
request, not only on coding. Claude Code is a **harness** around the model, so the same request can
come back **more capable**. And you can **trim** the harness for each request, so a simple one stays
cheap.

**Why:** you get three gains in one, and each is measured in this lesson:

| Gain | What your agent gets | Measured in this lesson |
|---|---|---|
| **1. The door** | your Pro login for every model request of your programs, coding or not, within your plan's usage limits ([Anthropic Help Center](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan)); the same model names; with an API key at work, the same programs run unchanged | Part 3: `ask_claude.py` answers from Python with only Pro |
| **2. The harness: stronger answers to hard requests** | the agent loop (act, check the result, act again), tools (read the files itself, compute exactly with Python), your skills, context management, rules and sessions | a 3,000-row table: a plain call, adding up in its head, was right 1 time out of 4, in about 2 minutes on average. Claude Code ran a few lines of Python. It was right 4 times out of 4, in 17 seconds, at a tenth of the cost per right answer (below) |
| **3. The dial: only as much harness as the request needs** | switch off what a request doesn't use: your account's MCP connectors, the built-in tools, settings and memory files, extra turns | one plain question: 39,143 input tokens with everything on, 849 with everything off; one computing job: 70 to 80% lower cost per right answer than everything on, with no fewer right answers |

**The harder the request, the larger the gain.** This test asks the same two questions as
"Three questions", below: the total per region to the cent, and the number of orders over 500. It asks
them on longer tables of made-up orders, on Haiku: three runs per question at 300 rows, two at 1,000
and 3,000:

```bat
python tools/harness_profile_compare.py --model haiku --runs 2 --tasks big --rows 3000 --profiles model,lean_py,full
```

| Rows | Plain call | Claude Code, everything on | Claude Code, lean, with one compute rule |
|---|---|---|---|
| 300 | right 5 of 6, 26 s, $0.0046 per right answer | 6 of 6, 12 s, $0.0043 | 6 of 6, 10 s, $0.0012 |
| 1,000 | 3 of 4, 55 s, $0.0118 | 4 of 4, 13 s, $0.0056 | 4 of 4, 11 s, $0.0023 |
| 3,000 | 1 of 4, 117 s, $0.0858 | 4 of 4, 17 s, $0.0083 | 3 of 4, 18 s, $0.0095 |

**How to read it:**

- **The plain call gets slower, dearer and less right as the table grows.** At 3,000 rows, one set of
  totals took it 5.6 minutes and about 112,000 output tokens, and was still wrong. Another time it
  answered "About 1,800" instead of 1,346. Twice, at 1,000 and 3,000 rows, it said honestly that it
  couldn't add up that many rows by hand.
- **Claude Code stays fast and cheap,** because Python adds up 3,000 rows as quickly as 300: 10 to 18
  seconds, under a cent per right answer. At 3,000 rows, everything on was right every time at a tenth
  of the plain call's cost per right answer.
- **At 3,000 rows, everything on beat the lean profile.** The lean profile lost one run to its own
  restriction: Claude wrote a command that the python-only rule refused. Trim most for easy requests.
  For hard ones, keep what the job may need.
- **A long question needs stdin on Windows.** A command line holds at most 32,767 characters, so a
  3,000-row table pasted into `claude -p "..."` fails with "The filename or extension is too long".
  The tool sends every question longer than 8,000 characters through stdin, as Step 12 does with a
  pipe.

**The warning: don't fit cheap tires to an expensive car.** The harness is designed and tested as a
whole. Taking parts out can cost more than it saves:

- **In this course:** allowed to run only python commands, Claude Code wrote `awk` and PowerShell
  instead, which the rule refused. It was right 3 times out of 6, not 6 ("Three questions", below).
- **In Hindsight**, an open-source memory system for agents: its one-turn calls allowed no tools but
  didn't remove them, so they failed now and then. Without a pinned model, Claude Code ran a different
  model than Hindsight's logs showed ("What others found when they switched parts off", below).
- **In Missy**, another agent: with the tools off but Claude Code's prompt kept, the model tried to
  call tools that didn't exist ("What others found when they switched parts off", below).
- **At Anthropic itself:** three changes in the harness, not in the model, lowered Claude Code's
  quality (the postmortem, below).

**The rule:** switch off only what the request doesn't use, and keep what it does. For example, Sigil,
an agent framework, answers its model calls with no tools, but gives its web searches exactly one tool,
WebSearch. Tell Claude in one sentence what it should use ("compute every number with Python"), and
pin the model. Then measure right answers and cost per right answer, before and after, on your own
requests.

**Not a strange idea: an established practice.**

- **Anthropic built its own agents this way:** it renamed the Claude Code SDK to the Agent SDK,
  because the harness behind Claude Code can power other agents. It runs almost all of its major
  agent loops on it (sources below).
- **The Agent SDK is downloaded tens of millions of times a month.** The Python package
  `claude-agent-sdk` had 14.2 million downloads in May 2026 and 29.9 million in September. That is
  about one for every five downloads of Anthropic's plain API package (`anthropic`, 146.4 million in September)
  ([PyPI Stats: claude-agent-sdk](https://pypistats.org/packages/claude-agent-sdk),
  [anthropic](https://pypistats.org/packages/anthropic)). The npm package
  `@anthropic-ai/claude-agent-sdk` had 44.9 million in the month to 22 October 2026
  ([npm](https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk)). Downloads count installs,
  also by automatic builds, not people. But the growth is clear.
- **Well-known open-source projects plug Claude Code in where a model API would go:** OpenClaw (about
  393,000 GitHub stars), Hindsight (about 54,000), promptfoo (about 26,000), OpenHarness (about 16,000),
  the Vercel AI SDK through a community provider, and more. The list, with what each keeps of the
  harness, is in "Who else builds agents this way", below.
- **OpenAI does the same with its coding agent:** the Codex SDK runs Codex from your programs.

**What this doesn't prove:** that a harness wins on every request. On small, easy requests a plain
call was just as right, and cheaper ("Three questions", below). Use the harness where the request is
hard, and the dial where it is easy.

## Why go through Claude Code at all: the harness around the model

**What:** an API call gives you **the model**: text in, text out, one answer per request. Claude Code
gives you the same model **inside a harness**. The harness is the program around the model: it runs
the agent loop, gives the model tools, manages its context, and enforces your rules. With `claude -p` or the SDK, your program
gets that whole harness, not only the model.

**Why it matters:** with the API alone, you would build each of these parts yourself, and test them
yourself. With Claude Code, they are already built, maintained, and used every day by a very large
number of developers.

| A plain API call gives you | Claude Code adds around the same model | Where you used it |
|---|---|---|
| one answer to one request | the **agent loop**: gather context, act with a tool, check the result, repeat until the job is done | Lesson 6, Step 4 (5 turns for one question) |
| tools only if you define and run them yourself | **built-in tools**: read, write, edit and search files, run commands | Lesson 3, Part 1 |
| no skills | **skills**: found on disk, offered by their descriptions, loaded only when chosen | Lesson 1, Step 5 |
| the whole history sent again; you trim it yourself | **context management**: prompt caching, compaction near the limit, `CLAUDE.md` memory, files read only when needed, subagents with a clean context | Lesson 4, Step 5; Lesson 6, Step 28 |
| no safety layer | **permissions and hooks**: allowed tools, refused calls, your rules enforced outside the model | Lesson 6, Step 15 |
| no memory between calls | **sessions** that your program can resume | Lesson 6, Step 14 |
| integrations that you write | **MCP**: tool servers plugged in with one option | Lesson 6, Step 8 |
| a token count | **observability**: every step as JSON, the transcript (Ctrl+O), hook events | Lesson 0, section 7 |

**The evidence,** from Anthropic and from public benchmarks:

- **Anthropic builds its own agents on this harness.** In September 2025, it renamed the Claude Code
  SDK to the Claude Agent SDK. The reason: "the agent harness that powers Claude Code" can power many
  other kinds of agents. Anthropic also reported that this harness already runs almost all of its
  major agent loops ([Building agents with the Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk),
  29 September 2025).
- **It is used at a very large scale.** Claude Code passed 500 million dollars in run-rate revenue
  within months of its full launch. Its usage grew more than tenfold in three months
  ([Anthropic, 2 September 2025](https://www.anthropic.com/news/anthropic-raises-series-f-at-usd183b-post-money-valuation)).
- **Anthropic's engineers explain why the model alone is not enough.** Context is a limited resource:
  the more a model must hold, the worse it recalls. A good harness keeps the context small and
  useful. Claude Code compacts a long conversation, and loads files with Glob and Grep only when they
  are needed. It reads `CLAUDE.md` as memory, and gives side jobs to subagents
  ([Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents),
  29 September 2025). For work that spans many sessions, they add a progress file, a feature list and
  git on top of the harness
  ([Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents),
  26 November 2025).
- **The harness changes results as much as a model does.** On Terminal-Bench 2.0, third-party reports
  compiled from the public leaderboard put the same model, Claude Opus 4.6, between about 58% and 82%.
  Only the harness around it was different
  ([Harness performance on Terminal-Bench](https://codex.danielvaughan.com/2026/04/09/harness-performance-terminal-bench/)).
  A test of one model in four harnesses found a 13-point spread
  ([Same model, different harness](https://kimchi.dev/blog/same-model-different-harness-terminal-bench),
  September 2026, by a harness vendor). A June 2026 research survey concludes that an agent's quality
  comes from the model and the harness together
  ([arXiv 2606.20683](https://arxiv.org/abs/2606.20683)).

**Be fair about it:**

- On those benchmarks, Claude Code was **not** the best harness for every model: specialized
  harnesses scored higher. Its strength is that it is general, mature, and tested by daily use. It
  is also available to you with a Pro login, ready for your own skills, rules and tools.
- The harness costs context. Even a plain question carried 4,309 input tokens of Claude Code's own
  text (Step 20). A short skill run read 110,413 tokens of context again (Step 28). For a pure
  question and answer, use the "plain LLM" settings of `agent/ask_claude.py`: no tools and a short
  system prompt. With `--strict`, a question costs about 850 tokens instead of 4,300 ("Using Claude
  Code only as the model", below).

**What it opens up:** a single API call can only answer. Through the harness, your program can hand
Claude a **job**, for example "build the pivot of this workbook and save the report". Claude finds the
file, chooses the skill, runs your Python, checks the result, and stays inside your rules. Meanwhile,
your program watches every step. That is the difference between a model and an agent. It is also why
every program in this lesson goes through Claude Code.

## When the harness is the right choice, and when it isn't

**What:** this section shows who else calls Claude Code (or a similar agent program) instead of the
model's API, and the two very different ways to do it. It also answers whether Claude Code is only for
code, when a plain API call is better, and what Anthropic's terms allow with a Pro login.

**Why:** a harness is not free: it costs context, time and, at work, a license. You should know when
it pays off, and that you are not the only one who builds agents this way.

### Who else builds agents this way

**Open-source projects that call Claude Code where a model API would go** (GitHub stars on 26 October
2026; "harness kept" says how much of Claude Code each one uses):

| Project | What it is | How it uses Claude Code | Harness kept |
|---|---|---|---|
| [OpenClaw](https://docs.openclaw.ai/gateway/cli-backends), about 393,000 stars | an agent gateway | runs its agent turns through a local Claude Code or Gemini CLI, as the main runtime or as a fallback. OpenClaw keeps the sessions, and gives Claude Code its own tools through an MCP bridge (`mcp__openclaw__<name>`, like the `mcp__tutor__` tools of Step 8) | the loop |
| [Hindsight](https://github.com/vectorize-io/hindsight), about 54,000 | memory for agents | the Agent SDK as the model of its own memory work, with a Pro or Max login: one turn, no tools, no settings files | model only |
| [promptfoo](https://www.promptfoo.dev/docs/providers/claude-agent-sdk), about 26,000 | a tool for testing LLM applications | the provider `anthropic:claude-agent-sdk`, alias `anthropic:claude-code`: no tools by default, read-only file tools when you give it a working folder. It can run on a Claude Code plan | both |
| [OpenHarness](https://github.com/HKUDS/OpenHarness), about 16,000 | an agent framework | its personal assistant, ohmo, runs on an existing Claude Code or Codex subscription through a CLI bridge, with no API key | the runtime |
| [NodeTool](https://github.com/nodetool-ai/nodetool), about 600 | a visual builder for AI workflows | `ClaudeAgentProvider` has both ways: a "pure LLM" call (one turn, tools and settings off, its own prompt), and a loop mode in which Claude Code runs its own agent loop over NodeTool's tools | both |
| [ai-sdk-provider-claude-code](https://ai-sdk.dev/v5/providers/community-providers/claude-code), about 370; 193,000 npm downloads a month | a community provider listed in the Vercel AI SDK documentation | Claude models through the Agent SDK and the Claude Code CLI, with a Pro or Max login or an API key | the model |
| [pi-claude-cli](https://github.com/rchern/pi-claude-cli), about 110 | a model provider for the pi agent | every request is a `claude -p` run; Claude asks for tools, and pi runs them | the model |
| [dsh-claude-cli](https://github.com/katsos/dsh-claude-cli) and [dsh-oh-my-claude](https://github.com/lcestou/dsh-oh-my-claude), small | two providers for the same agent, DeepSeek Harness | the first switches off Claude Code's loop, tools, settings, memory files and MCP; the second keeps its sessions, hooks, CLAUDE.md files and MCP servers | opposite choices |
| [Agentry](https://github.com/aweussom/agentry), small | an OpenAI-compatible API on your own computer | your OpenAI client code talks to a persistent `claude -p` process, with the built-in tools and MCP off | the model |
| [Sigil](https://sigilagent.com/reference/claude-code.html), small | an agent framework that compiles skills into procedures | a headless `claude -p` run on your subscription answers every model tier (compiler, executor, router, chat), with no API key. A model answer gets one turn and no tools; a web search gets exactly one tool, WebSearch | the model, plus one tool |
| [Build A Harness](https://github.com/3IVIS/buildaharness), small | a canvas for agent governance, with a personal assistant, Aielia | `ASSISTANT_LLM_BACKEND=claude-cli` uses a `claude` login instead of an API key | the model |
| [Voicetest](https://dev.to/pld/using-claude-code-as-a-free-llm-backend-for-voice-agent-testing-40bg) | a tool for testing voice agents | `claude -p --output-format json` as a plain LLM backend for simulations and judges, on a Pro or Max plan. Its author notes that one call runs at a time, so large parallel test suites are better on an API | the model |

**How to read it:** the large projects show that the pattern is used, not only discussed. They also show
both ways. Some keep only the model and run everything else themselves; others hand Claude Code the
loop. The two DeepSeek Harness providers make opposite choices for the same parent agent. They are a
good pair to compare.

**The vendors themselves:**

- **Anthropic** lists finance agents, personal assistants, customer support agents and deep research
  agents as examples of what to build with the Agent SDK
  ([Building agents with the Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk)).
  Its documentation tells programs in other languages to run `claude -p` as a subprocess with JSON
  output ([Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)). It now also sells
  the harness itself. **Managed Agents** is a hosted agent harness. Anthropic offers it next to the
  Messages API, which gives "direct model prompting access" for your own agent loop
  ([Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview)). And it built
  **Cowork**, its desktop agent for non-coding knowledge work, with the same agentic approach as Claude
  Code ([Claude Cowork](https://claude.com/blog/cowork-research-preview)).
- **OpenAI** does the same with its own coding agent. The Codex SDK controls local Codex agents from
  your program, for internal tools, workflows and your own applications. Its Python version ships
  with the Codex CLI inside ([Codex SDK](https://learn.chatgpt.com/docs/codex-sdk)). Like Anthropic,
  OpenAI presents it mainly for engineering work.

**Independent voices:**

- **Simon Willison**, an independent developer with a widely read blog about LLM tools, wrote in
  October 2025 that Claude Code is poorly named. In Willison's view, it is not only a coding tool, but
  a tool for general computer automation
  ([Claude Skills are awesome, maybe a bigger deal than MCP](https://simonwillison.net/2025/Oct/16/claude-skills/)).
  Barry Zhang of Anthropic said that skills came out of a prototype that showed Claude Code is a
  general-purpose agent ([quoted by Simon Willison](https://simonwillison.net/2025/Oct/16/barry-zhang/)).
- **An independent comparison** (MindStudio, May 2026) gives the same rule as this lesson. Use the
  plain API for tasks that finish in one call, with low overhead and full control. Use the Agent SDK for
  agents that act through a number of steps that nobody knows in advance
  ([What is the Claude Agent SDK?](https://www.mindstudio.ai/blog/what-is-claude-agent-sdk-vs-claude-api)).

**What nobody has shown yet:** a controlled study in which calling Claude Code beats calling the API
for every job. The evidence shows that the pattern works, that large projects and both vendors use
it, and that the harness changes results. This course's own measurement shows where it wins and where
it doesn't ("Three questions", below).

### Two ways to use Claude Code from your agent: as the model, or as the runtime

| | As the **model** | As the **runtime** |
|---|---|---|
| What you send | one question | a job: "find the files, compute, check, report" |
| Who runs the loop | your Python | Claude Code |
| Tools, skills, context management, hooks | switched off, or not used | they do the work |
| In this course | `agent/ask_claude.py`, `agent/api_equivalent.py` | `agent/run_agent.py`, `custom_tools_agent.py`, `guarded_agent.py` |
| What you gain over the API | mostly the door: your Pro login, nothing else to install | the whole harness |

The large gain is in the second column. It is biggest when your program **can't know the steps in
advance**. Claude Code then finds what it needs, chooses the next step, looks at the result, and
changes its plan.

**Decide who owns the loop.** Your Python program may already plan, call tools and retry. If it hands
each small step to a Claude Code run that also plans and calls tools, it builds a loop inside a loop.
That costs time and tokens. Choose one: keep your loop and use Claude Code as the model, or hand
Claude Code a whole sub-job and let your program supervise it.

**For a general-purpose agent, adapt three things:**

1. **Your own instructions,** not Claude Code's default coding persona: `system_prompt=` in the SDK, or
   `--system-prompt` in `claude -p` (Step 2, Step 10).
2. **Your business tools, through a controlled door:** an MCP server (`tutor_mcp_server.py`, Step 8)
   for calendars, databases or tickets, because files and commands alone don't reach them. And a hook
   (Step 15) for what may never happen.
3. **Skills for the know-how,** with scripts for everything that must be exact (Lesson 3).

### Is Claude Code only a harness for writing code?

Its **defaults** are made for software work. Anthropic describes the Claude Code product as built for
software engineering, and its long built-in instructions are about code. The **harness** underneath is
general: the loop, the file and command tools, skills, hooks, sessions and MCP. You use it for other
work by giving it your own instructions and tools. This course does exactly that: none of its
9 skills writes code. They analyze sales data, compute dates and invoices, keep a to-do list, and draw
charts.

The real limit is a different one: the harness works **through files and commands on a computer**.
Skills need a file system and a place to run code, a point Simon Willison makes too. A job that is
only text in and text out doesn't need any of it.

### When to use which

| Your job | Better choice | Why |
|---|---|---|
| Answer a question, write a short email from full instructions, translate, classify, choose an action | a plain call: Claude Code as the model, or the API | no loop is needed. Even with the tools off, Claude Code adds about 4,300 tokens of its own text (about 850 with `ask_claude.py --strict`), and a few seconds to start |
| A database update that is fully specified in advance | your own Python, without a model | nothing to decide, so nothing for a model to do |
| Thousands of small requests, or answers for hundreds of users at once | the API, with an API key | every `claude -p` run starts a program and carries Claude Code's own text, one call at a time, under your plan's limits |
| Analyze several spreadsheets, find what doesn't match, and write a report | Claude Code as the runtime | exploring, running scripts and checking results is what the loop is for |
| Research across many documents | the runtime, with search tools | it reads only what it needs, and keeps notes |
| A multi-step office workflow across business systems | the runtime, with MCP tools and hooks | your tools do the actions; the hooks keep the rules |
| A job that continues later, or a conversation | the runtime, with sessions | no history handling of your own (Step 14) |
| A fixed pipeline, the same steps every time | `claude -p` or the SDK in a program | Anthropic calls these "static workflows"; the programs of this course are such workflows |
| A product for other people, or a company's production jobs | the runtime or the API, **with an API key**, or Managed Agents | see the terms below |

Anthropic's own advice for the harness points the same way: spend extra steps, subagents and
parallel work only where they earn their cost
([A harness for every task](https://claude.dev/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code/),
2 June 2026).

### Pro login or API key: what Anthropic's terms allow

- **Your Pro login is for ordinary, individual use.** Anthropic's documentation says the usage
  limits of Pro and Max assume ordinary, individual use of Claude Code and the Agent SDK. Learning
  with this course is such use, and so are your own programs on your own computer.
- **Products and services need an API key.** Developers who build products or services with Claude,
  including with the Agent SDK, should use an API key, under Anthropic's Commercial Terms. The key
  comes from the Claude Console or a supported cloud provider (Amazon Bedrock, Google Vertex AI,
  Microsoft Foundry).
  You may not offer a Claude login in your own application, or send other people's requests through
  your Pro plan. A person may sign in to the unmodified Claude Code program with their own plan. This
  is allowed also when another product starts that program, as OpenClaw does. Anthropic may enforce
  these rules without notice ([Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)).
- **So, at work:** keep the same programs, and run them with your company's API key. Set it in the
  environment variable `ANTHROPIC_API_KEY` before the program starts (Lesson 0, Step 8 shows how
  Claude Code then uses it). The `cost≈$` numbers become real costs. Or move the job to Managed
  Agents, where Anthropic hosts the harness. When you are unsure which way fits, Anthropic's
  documentation suggests asking its sales team.

## Using Claude Code only as the model: switching the harness off

**What:** some developers use Claude Code as nothing but the model of their own agent. They switch
off its loop, its tools, its settings, its memory files and its MCP tools, and keep everything else in
their own code. This section shows how, and measures on this machine what each switch removes. It also
tests whether Claude Code's own instructions make the model answer better.

**Why:** it is the opposite of the harness idea above. It fits when your program owns the loop and the
tools, and only needs answers from the model.

**Who does it:**

- **dsh-claude-cli** makes a Claude Code login the model backend of another agent harness. In its own
  words, the harness stays the agent. It switches off the CLI's loop, tools, settings, memory files and
  MCP servers ([dsh-claude-cli on GitHub](https://github.com/katsos/dsh-claude-cli), a small project).
- **pi-claude-cli** registers Claude Code as a model provider of the pi agent: every request is a
  `claude -p` run, Claude proposes tool calls, and pi runs them
  ([pi-claude-cli](https://cdn.jsdelivr.net/npm/pi-claude-cli@0.3.1/README.md)).
- **Voicetest**, above, uses it as a plain LLM backend for its tests.
- **Hindsight, Sigil, NodeTool, Agentry and promptfoo** do it too, for some or all of their calls (the table
  in "Who else builds agents this way", above).

**How, switch by switch** (checked with `claude --help` on Claude Code 2.1.308):

| Switch | What it keeps out |
|---|---|
| `--tools ""` | the built-in tools: Read, Write, Edit, Bash, PowerShell, ... |
| `--strict-mcp-config` | MCP tools, also the connectors of your claude.ai account, which `--tools ""` leaves in |
| `--system-prompt "..."` | Claude Code's own instructions (one line about the Agent SDK stays) |
| `--setting-sources ""` | your user, project and local settings files |
| `--safe-mode` | CLAUDE.md, skills, plugins, hooks and custom agents; your login keeps working |
| `--disable-slash-commands` | skills started with `/name` |
| `--no-session-persistence` | the saved session on disk |
| `--permission-mode dontAsk` | permission questions; anything not allowed is refused |
| `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`, `CLAUDE_CODE_DISABLE_ATTACHMENTS=1` | every CLAUDE.md file; the skill list and similar notes ([Anthropic: modifying system prompts](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts)) |

**Not this one:** `--bare` sounds right ("minimal mode"), but it never reads your Pro login: it
accepts only an `ANTHROPIC_API_KEY`.

**There is no switch for the loop.** With no tools, a `claude -p` run ends after one answer anyway.
When the parent agent needs tool requests, dsh-claude-cli declares the parent's tools through an MCP
server that never runs them. It ends the request as soon as the model's message ends. So Claude asks
for a tool, and the parent agent runs it.

**All of it in one program:** `agent/ask_claude.py --strict` (both ways, with `--sdk` too).

### What really reaches the model

Claude Code can write every request it sends to a folder: set `OTEL_LOG_RAW_API_BODIES=file:<folder>`
before `claude -p` ([Anthropic: see what Claude received](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts)).
These are the requests of one question, on Haiku, from the user folder:

| Setup | Tools sent | System prompt | Input tokens |
|---|---|---|---|
| Claude Code's defaults | 16 | 11,387 characters | 39,143 |
| tools off, Claude Code's prompt kept | 10, the connector tools | 9,971 characters | 7,332 |
| tools off, own prompt (`ask_claude.py`) | 10, the connector tools | 339 characters | 4,297 |
| the same, plus `--strict-mcp-config` | 0 | 339 characters | 871 |
| every switch (`ask_claude.py --strict`) | 0 | 339 characters | 849 |

**How to read it:**

- One switch did most of the work: `--strict-mcp-config` took 4,297 down to 871 tokens. The reason:
  `--tools ""` had left the 10 MCP tools of the account's claude.ai connectors in every request.
- The other switches changed almost nothing here, because these calls ran from the user folder, where
  there is no CLAUDE.md and no skill. From a project folder, they matter.
- Some text stays even with every switch: the line about the Agent SDK in the system prompt, a short
  reminder with account context, and an environment block (working folder, platform). And every run
  starts a program: about 5 seconds in total, of which the model needed about 1.

### What others found when they switched parts off

- **Keeping Claude Code's prompt with the tools off went wrong** in Missy, an open-source agent. Its
  first adapter appended Missy's instructions to Claude Code's agentic system prompt. With the built-in
  tools off, the model still tried to call file tools that didn't exist, in 43 of 201 failing test
  cases. In 39 more, safety notices and a silent switch to an older model showed up in the answer
  text. The fix: replace the prompt, use `--max-turns 1`, block MCP tools, and check that the pinned
  model answered ([Missy, pull request 170](https://github.com/MissyLabs/missy/pull/170), October 2026).
- **Switch a part off completely, or not at all.** Hindsight, which uses Claude Code as the model of
  its memory work, documents three traps in its code. Allowing no tools (`allowed_tools=[]`) left
  them loaded. So a one-turn call sometimes spent its only turn loading tools, and failed with "Reached
  maximum number of turns (1)". Removing them (`tools=[]`) fixed it. Without a pinned model, Claude
  Code used its own default, an Opus-class model on a Pro or Max login. Hindsight's logs still showed
  the configured model (issue 2881). And the settings files of the computer brought in hooks that fed
  Hindsight's own calls back into its memory: a loop. Now it runs Claude Code in an empty folder, and
  loads no settings files (issues 1751 and 5542)
  ([Hindsight: claude_code_llm.py](https://github.com/vectorize-io/hindsight/blob/main/hindsight-api-slim/hindsight_api/engine/providers/claude_code_llm.py)).
- **Keep one tool, not all or none.** Sigil answers its model calls with one turn and no tools.
  Otherwise, Claude Code would reach for its own tools instead of writing the tool-call text that Sigil
  reads. Its web search gets exactly one tool, WebSearch, on Haiku. Its documentation reports about
  9,000 input tokens per call, even with all tools off. With `--system-prompt`, `--tools ""` and
  `--strict-mcp-config`, this course measured about 850 ("What really reaches the model", above). So
  measure the flags you use ([Sigil: Claude Code](https://sigilagent.com/reference/claude-code.html)).
- **Text answers work, tool work doesn't**, in clio-agent's Claude Code provider with the tools off
  ([clio-agent, issue 717](https://github.com/iowarp/clio-agent/issues/717)).
- **Fewer tools, same success, lower cost:** restricting Claude Code and Codex to one `execute_code`
  tool was cheaper than their full tool sets, or tied with them, in 3 of 4 settings. The pass rates were
  statistically tied ([arXiv 2607.10569](https://arxiv.org/abs/2607.10569), July 2026).
- **A big harness costs more per success:** a preregistered study compared Claude Code 2.1.220 with
  the small PI.DEV harness. Claude Code sent a 12 to 15 times larger fixed prefix and took 2 to 7 times
  more turns. So its cost per successful task was 5 to 30 times higher, at comparable success rates (mostly open
  models, plus Claude Sonnet 5)
  ([Weinberger and Hozez, arXiv 2608.01347](https://arxiv.org/abs/2608.01347), August 2026).
- **The layer itself changes quality, both ways:** Anthropic traced a drop in Claude Code's quality to
  three changes in the harness, not in the model. They were a lower default effort, old thinking cleared
  on every turn, and a line in the system prompt that limited answer length. It says the API was not affected
  ([Anthropic postmortem](https://anthropic.com/engineering/april-23-postmortem), 23 April 2026). So
  set the model and the effort yourself, and test again after a Claude Code update.
- **An anecdote to read with care:** one developer's code-review tool found 7 issues, all real,
  through `claude -p`, and 84 through the API on Sonnet, about 69 of them false. But it was one diff
  and one run, and the CLI looked at fewer files. The API version also had four integration bugs, which
  the author fixed on the way. It shows how much the integration matters, not that the CLI is smarter
  ([Claude CLI vs API for code review](https://dev.to/fole/claude-cli-vs-api-for-code-review-same-model-wildly-different-results-1oai),
  March 2026).

### Does Claude Code's own prompt make the model answer better?

That is the real question behind keeping Claude Code's instructions: maybe its engineering helps the
model even without tools. `tools/model_mode_compare.py` tests it. It asks the same 12 questions (a
time, a date, arithmetic, a ticket label, JSON extraction, a tool choice, logic, the order of steps, an
exact reply) with the same model, in different modes. A real run on Haiku:

```bat
python tools/model_mode_compare.py --model haiku
```

```text
mode           right  input tokens  output  thinking  seconds  model s
harness       11/12         39,151      66        54      5.5      1.4
cc_prompt     11/12          3,917       8         0      4.7      0.9
own_prompt    10/12            906      40        32      5.1      1.2
strict        10/12            882      29        23      4.6      0.9
```

**Then the comparison that matters, repeated:** Claude Code's own prompt (`cc_prompt`) against a
short prompt of your own (`own_prompt`), both with the tools off. There are three runs on Haiku and
one on Sonnet:

```bat
python tools/model_mode_compare.py --model haiku --modes cc_prompt,own_prompt --runs 3
```

```text
Model: haiku, 12 questions, 3 run(s) per mode
mode           right  input tokens  output  thinking  seconds  model s
cc_prompt     31/36          3,917       7         0      4.9      0.9
own_prompt    33/36            905      34        26      4.9      1.2

Model: sonnet, 12 questions, 1 run(s) per mode
mode           right  input tokens  output  thinking  seconds  model s
cc_prompt     12/12          3,092      12         0      5.2      1.4
own_prompt    12/12            883      22        16      5.0      1.4
```

**How to read it:**

- **Claude Code's prompt did not make the answers better.** On Haiku, it was right 31 times out of
  36, and your own prompt 33 times. One of those "wrong" answers was right, but not in the format
  asked for. On Sonnet, both were right every time. With this few questions, the difference on Haiku is
  within chance. So the honest result is: no sign of a gain.
- **It cost more:** 4.3 times the input tokens on Haiku (3,917 against 905), 3.5 times on Sonnet.
- **The model mattered more than the prompt.** Haiku's mistakes were simple (a time, a date, a
  price), and the date question failed in all three `cc_prompt` runs. Sonnet made none in either mode.
- **No answer tried to use a tool,** because these questions need none. Missy's agent, which asked
  about files, did run into that problem (above).
- **Anthropic's advice points the same way:** start from Claude Code's prompt for coding tools where a
  person watches and steers. Write your own prompt for an agent with a different job, identity or
  permission model
  ([Anthropic: modifying system prompts](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts)).

### So: when to switch the harness off

- **Switch it off** when your program owns the loop and the tools, and only needs answers:
  `python agent/ask_claude.py --strict "..."`. You keep the door (your Pro login, the model names)
  and send about 850 input tokens instead of about 4,300, or 39,000 with every default on. Each call
  still costs a few seconds to start the program.
- **Keep it on** when you want what this lesson is about: a job done by the loop, the tools, the
  skills and the rules. Switching all of that off throws away the reason to use Claude Code.
- **For high volume, or many users at once,** use neither: call the API with an API key.

**Test it on your own agent:** put 50 to 100 real questions of your agent into a file, as a JSON list
of `{"prompt": "...", "expect": "<regular expression>"}`. Then run
`python tools/model_mode_compare.py --questions my_questions.json --runs 3`. With an API key, you can
add the direct API call as a third baseline.

## Three questions: when, how, and how cheaply Claude Code beats a plain model call

**What:** the three questions that matter if you want Claude Code instead of a direct model call in
your own agent, for work that is not coding:

1. When does Claude Code, with its tools, beat a plain model call?
2. How do you make it beat a plain model call?
3. How do you cut its tokens and still keep that advantage?

**Why:** the sections above show that the harness matters, and that a model-only call gains nothing
from Claude Code's prompt. Your agent needs the next step: which jobs to give to the harness, how to
set it up, and at what cost.

### What others have measured

- **The same model, different harnesses, coding tasks:** in the HarnessTax study (UC Berkeley and
  Arena, September 2026), each model solved about as many tasks in Claude Code as in Codex CLI and the
  small Pi harness. But Claude Code cost about twice as much as Pi
  ([HarnessTax](https://arena.ai/blog/coding-agents-harness-tax/)). A smaller test shows where the
  difference starts: about 27,000 input tokens per request in Claude Code, against about 2,600 in Pi.
  On a simple task, 24 of Claude Code's 28 tools were never used
  ([Portkey: The Harness Tax](https://portkey.ai/blog/the-harness-tax/), April 2026).
- **Fewer tools, same success, lower cost**, and **a big harness costs more per success**: the
  tool-restriction paper and the preregistered study in "What others found when they switched parts
  off", above.
- **Anthropic's own advice for fewer tokens** in Claude Code: MCP tool definitions are deferred until
  used, and unused servers should be switched off. Prefer command-line tools to MCP servers. Let a
  hook or a script pre-process data, so the model sees hundreds of tokens instead of tens of
  thousands. Give know-how through skills, which load only when used, and keep CLAUDE.md under 200
  lines. Lower the effort for simple work, and write specific prompts
  ([Anthropic: manage costs effectively](https://code.claude.com/docs/en/costs)).
- **What nobody has published:** the same model, on work that is not coding, as a plain call against
  Claude Code with its tools. So this course measured it.

### What this course measured

**The test:** `tools/harness_profile_compare.py` asks the same questions in five profiles of `claude -p`,
all on Haiku, the cheapest model, where mistakes show first:

| Profile | What Claude gets |
|---|---|
| `model` | no tools, a short prompt of your own, every customization off, one turn. The file's text is pasted into the question, as your program would do with a plain API call |
| `lean` | Claude Code's own prompt and loop, with only `Read` and python commands allowed; no skills, no CLAUDE.md, no MCP tools |
| `lean_py` | `lean`, plus one sentence appended to Claude Code's prompt: compute every number with Python |
| `skills` | the agent of this course: the project's skills and CLAUDE.md, no MCP tools |
| `full` | everything Claude Code loads by default, also your user settings and your account's connectors |

An answer is right when it matches the true value exactly. "Ran code" counts the runs that called
Bash, PowerShell or a skill. The cost is Claude Code's API-price estimate (`total_cost_usd`). With Pro,
you don't pay it, but it shows how much of your allowance a profile uses.

**Round 1: small files.** Seven tasks: the total per region, an average, the product with the most
units, an invoice total, a word count, working days, and a logic question as a control. Every file is
under 1 KB, small enough to paste into a question. Two runs per task:

```bat
python tools/harness_profile_compare.py --model haiku --runs 2 --tasks small
```

```text
Model: haiku, 7 tasks, 2 run(s) per profile

profile    right  ran code  input tokens      cost  cost per right  turns  seconds
model     14/14      0/14          1,062 $  0.0003         $0.0003    1.0      6.2
lean      14/14      0/14         16,695 $  0.0006         $0.0006    1.7      6.8
lean_py   13/14     12/14         24,082 $  0.0007         $0.0007    2.4      8.8
skills    12/14      5/14         77,749 $  0.0022         $0.0025    2.4      8.6
full      13/14      6/14         84,911 $  0.0031         $0.0034    2.1      9.9
```

**How to read it:**

- **The plain call was as right as any profile, and the cheapest.** A first round without `lean_py`
  gave the same picture. Over both rounds, `model` was right 27 times out of 28, and `lean`, `skills`
  and `full` 26 times each. With this few runs, a difference of one or two is chance.
- **Three of the "wrong" answers had the right value in the wrong form.** Twice, in `skills` and
  `full`, Haiku answered "Carl" with an explanation instead of the name only. Once `lean_py` wrote its
  Python command in a form that the allow rule didn't cover. The command was refused, and Claude said so.
- **Unrestricted Claude Code cost about 10 times as much per right answer** ($0.0034 against $0.0003),
  with 80 times the input tokens, and took 3.7 seconds longer.
- **Tools alone don't make Claude compute.** `lean` was allowed to run Python, but ran it in none of
  its 14 runs: it read each file and worked in its head. One appended sentence made `lean_py` run
  Python in 12 of 14.
- **The skills were called once in 14 runs.** For these one-line computations, Claude read the file
  or wrote its own Python.

**Round 2: a table too long to add up in your head.** The tool writes 300 made-up orders (order,
region, amount). The questions: the total per region to the cent, and the number of orders over 500.
Three runs per task:

```bat
python tools/harness_profile_compare.py --model haiku --runs 3 --tasks big
```

```text
Model: haiku, 2 tasks, 3 run(s) per profile

profile    right  ran code  input tokens      cost  cost per right  turns  seconds
model      5/6       0/6           3,610 $  0.0038         $0.0046    1.0     25.6
lean       3/6       6/6          50,184 $  0.0043         $0.0086    4.0     26.9
lean_py    6/6       6/6          33,914 $  0.0012         $0.0012    3.0     10.3
skills     6/6       6/6         112,646 $  0.0030         $0.0030    3.0     11.0
full       6/6       6/6         135,196 $  0.0043         $0.0043    3.3     12.4
```

**How to read it:**

- **The plain call had to work hard, and slipped.** Working in its head, Haiku wrote about 3,300
  output tokens for each count, and 7,000 to 13,600 for each set of totals. It took 26 seconds on
  average, and one of its totals was one cent off, given as exact.
- **A few lines of Python were cheaper than the hand arithmetic.** `lean_py` read the file, ran Python,
  and was right 6 times out of 6, in 10 seconds. It cost $0.0012 per right answer: a quarter of the
  plain call's cost, with 9 times its input tokens. Its answers needed about 420 output tokens. The
  plain call's cost was mostly its long output.
- **Unrestricted Claude Code was right every time,** at about the same cost per right answer as the
  plain call ($0.0043 against $0.0046), in half the time. `skills` and `full` ran Python in every run.
  Both read the project's CLAUDE.md, which names `python`.
- **`lean` failed for a reason you can fix.** It tried `awk` and PowerShell's `Import-Csv`, not python.
  The allow rule `Bash(python *)` refused both, and `--permission-mode dontAsk` doesn't ask. Then it
  was honest: twice it gave no totals rather than unchecked ones, and once it added a note to the
  right count. It gave no wrong number, but half its runs gave no usable answer.

### The answers

**1. When does Claude Code, unrestricted, beat a direct model call on work that is not coding?** When
the job needs more than the model's head: exact arithmetic on more than a few lines of data, files it
must find and read itself, data too big to paste, several steps. On the 300-row table, it was right 6
times out of 6 against 5 out of 6, at the same cost per right answer and twice as fast. On 3,000 rows,
it was right 4 times out of 4 against once, at a tenth of the cost per right answer ("The big idea",
above). When the data is small enough to paste and the question is easy, it does not beat a plain
call. It gives the same right answers, at about 10 times the cost.

**2. How do you make it beat a direct call?**

- **Give it a way to compute, and tell it to use it**, in words that match your allow rule. One
  appended sentence did more than any tool or skill: `lean_py` was right 6 times out of 6 on the big
  table, the cheapest and fastest profile.
- **Check the form of every answer** with a pattern, or ask for JSON with `--json-schema`. Claude
  Code's longer prompt made Haiku add explanations.
- **Put rules that must be exactly yours into skills:** an invoice's rounding, your company's holidays
  (Lessons 2 to 4). For a one-line sum, Claude writes its own Python.

**3. How do you cut its tokens and keep the advantage?**

- **Switch off what the job doesn't use, and keep Claude Code's prompt and loop:**
  `--strict-mcp-config` (your account's connectors), `--safe-mode` (CLAUDE.md, skills, plugins,
  hooks), `--tools "Read,Bash,PowerShell"` with an allow rule for python only, and
  `--disable-slash-commands`. Against unrestricted Claude Code, that meant about 70 to 75% fewer input
  tokens, and a 70 to 80% lower cost per right answer. It gave no fewer right answers (big table:
  $0.0012 against $0.0043; small files: $0.0007 against $0.0034).
- **Count the output tokens too:** a short Python run cost less than long reasoning in the head.
- **Route each job:** send small, easy questions to the plain call (`ask_claude.py --strict`), and
  jobs that compute on files to the lean runtime. One program can choose per job.
- **Don't trim what a hard job may need:** on the 3,000-row table, the lean runtime lost one run to its
  python-only rule. Everything on was right every time ("The big idea", above).

**What this test doesn't show:** Haiku only, two or three runs per task, made-up data, one computer. A
larger model may slip less in its head. So repeat the test with your model and your own jobs, and
compare the cost per right answer.

### The three profiles, ready to copy

These are the profiles of the test, with `--max-budget-usd` added. Haiku is the model measured here.
Use `sonnet` for harder jobs.

**Model only** (a plain call, with your data in the question):

```bat
claude -p "<question with the data>" --model haiku --output-format json --tools "" --system-prompt "<your role>" --strict-mcp-config --setting-sources "" --safe-mode --max-turns 1 --no-session-persistence
```

**Lean runtime with the compute rule** (`lean_py`: Claude Code's prompt and loop, reading files and
computing with Python, nothing else):

```bat
claude -p "<job>" --model haiku --output-format json --tools "Read,Bash,PowerShell" --allowedTools "Read,Bash(python *),PowerShell(python *)" --append-system-prompt "Compute every number with Python (python -c or a short script) and answer from its output; never count, add or round by hand." --permission-mode dontAsk --strict-mcp-config --safe-mode --disable-slash-commands --max-turns 6 --max-budget-usd 0.50 --no-session-persistence
```

**Skills runtime** (the agent of this course: your tested scripts as skills):

```bat
claude -p "<job>" --model haiku --output-format json --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)" --permission-mode dontAsk --setting-sources project --strict-mcp-config --max-turns 8 --max-budget-usd 0.50 --no-session-persistence
```

| Option | What it does for cost and safety |
|---|---|
| `--max-turns N` | stops a job that goes in circles |
| `--max-budget-usd 0.50` | stops a job when its API-price estimate reaches the amount (only with `claude -p`) |
| `--permission-mode dontAsk` | refuses every tool that is not allowed, instead of waiting for an answer |
| `--exclude-dynamic-system-prompt-sections` | moves per-machine details out of Claude Code's own system prompt. Then many runs on different machines share one prompt cache (only with Claude Code's prompt) |

**Test them on your own jobs:** `python tools/harness_profile_compare.py --model haiku --runs 2` runs
both rounds. Add your agent's real jobs to its `tasks()`, each with a regular expression for the right
answer. Then run them with `--tasks <name>`.

## Step 1 - Check that the Agent SDK is installed

**What:** the **Claude Agent SDK** is a Python package (`claude-agent-sdk`). It lets a Python program
use Claude Code: the same skills, the same tools, and the same login.

**Why:** every program in Parts 0 to 2 imports it.

**Run:**

```bat
python -c "import claude_agent_sdk; print(claude_agent_sdk.__version__)"
```

**Expected result:**

```text
0.2.168
```

**How to read it:** the SDK is installed in your venv (this lesson was tested with version 0.2.168).

**If you see something else:** `ModuleNotFoundError: No module named 'claude_agent_sdk'` means it is
not installed in **this** Python. Install it once, in the activated window:

```bat
python -m pip install -r agent\requirements.txt
```

## Part 0 - What the SDK does when your program asks Claude

### Step 2 - See which program the SDK starts

**What:** `tools\show_sdk_command.py` prints what the SDK would start for `agent\run_agent.py`,
without starting it. It costs nothing.

**Why:** the SDK doesn't contain its own AI. It **starts the Claude Code program in the background**
and talks to it. Seeing the exact program and options takes the mystery out of it.

**Run:**

```bat
python tools/show_sdk_command.py --model haiku
```

**Expected result:**

```text
The SDK would start this program:
    C:\pyenvsmy\claudeclioct26\Lib\site-packages\claude_agent_sdk\_bundled\claude.exe
in this folder (cwd):
    E:\may10\claudecodecli_and_python
with these options:
    --output-format
    stream-json
    --verbose
    --system-prompt

    --allowedTools
    Skill,Read,Bash(python *),PowerShell(python *)
    --max-turns
    15
    --model
    haiku
    --setting-sources=project
    --input-format
    stream-json
```

**How to read it:**

| Part | Meaning |
|---|---|
| **The program** | a `claude.exe` that came **inside the pip package** (`_bundled`). It is a second copy of Claude Code. It reads the same login file as your normal `claude`, so it uses your Pro plan |
| **The folder** | the project folder. That is where Claude Code finds `.claude\skills\` |
| `--output-format stream-json`, `--input-format stream-json` | the SDK and Claude Code talk in JSON lines: one line per message, in both directions |
| `--allowedTools ...` | these tools run without permission questions |
| `--max-turns 15` | the most turns allowed |
| `--model haiku` | the model |
| `--setting-sources=project` | load only this project's skills and settings |
| **The empty line after `--system-prompt`** | an empty system prompt. The system prompt is the long set of instructions that normally tells Claude how to behave as Claude Code. An SDK agent gets only the tools, the skills and your question. To get the full normal behavior, add `system_prompt={"type": "preset", "preset": "claude_code"}` to the options |

**Your question is not in the list.** The SDK sends it separately, as a JSON line on the program's
input (stdin). It reads Claude's steps back as JSON lines from its output (stdout). This works exactly
like the pipe in Lesson 3, Step A4.

### Step 3 - Compare with your normal Claude Code

**What:** `where claude` shows which `claude.exe` cmd starts when you type `claude`.

**Why:** to see that the SDK uses a different copy of the same program, and that both share one login.

**Run:**

```bat
where claude
```

**Expected result:**

```text
C:\Users\Workstation\.local\bin\claude.exe
```

**How to read it:** your normal `claude` is a different file from the SDK's copy in Step 2. Both read
your login from `C:\Users\<you>\.claude\.credentials.json`. The SDK prefers its own copy. To make it
use your normal one, add `cli_path=r"C:\Users\Workstation\.local\bin\claude.exe"` to
`ClaudeAgentOptions`.

So this is **headless mode**, the same as `claude -p`: no window, and nobody to answer permission
questions. That is why a program must allow its tools in advance with `allowed_tools`.

| | `claude` (normal window) | `claude -p "..."` | Agent SDK |
|---|---|---|---|
| Who starts `claude.exe` | you | you, or a program | the SDK, in the background |
| Which `claude.exe` | your normal one | your normal one | the copy inside the pip package |
| Your question goes in through | the keyboard | the command line | a JSON line on stdin |
| The answer comes back as | text on the screen | text, or JSON | Python objects |
| Permission questions | you answer them | nobody can, so allow tools in advance | nobody can: `allowed_tools`, or a Python function `can_use_tool` |

## Part 1 - An agent program that uses the skills

### Step 4 - Run the agent program

**What:** `agent\run_agent.py` asks Claude one question through the SDK, and prints each step.

**Why:** to see that your program gets the same skill choice and script runs as the normal window,
step by step.

**Run:** (`--model haiku` uses the small model, which saves your allowance)

```bat
python agent\run_agent.py --model haiku "Which region sold the most in data/sales.csv?"
```

**Expected result** (a real run, shortened; your answer will be worded a little differently):

```text
[init] auth: claude.ai subscription (Pro/Max usage, no API billing)
[init] model: claude-haiku-5-5
[init] skills discovered: ['analyzing-csv', 'analyzing-excel', 'analyzing-text', ...]

[skill] Claude picked: analyzing-csv
[tool]  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/analyzing-csv/scripts/csv_tool.py" summary data/sales.csv
[tool]  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/analyzing-csv/scripts/csv_tool.py" groupby data/sales.csv --by region --value amount --agg sum
[claude] North sold the most in `data/sales.csv`, with total `amount` of 2,150.0. The other regions were East at 910.0, West at 900.0 and South at 670.0.

[done] success, turns=5, cost≈$0.0028 (API list-price estimate)
```

(Without `--model haiku`, the default model, Opus, is used: the same steps cost about $0.20.
Claude may also use the PowerShell tool instead of Bash; both are allowed.)

**How to read it:** the program prints a label before each step:

| Label | Meaning |
|---|---|
| `[init]` | The session started: which login (your Pro plan), which model, and which skills were found |
| `[skill]` | Claude chose a skill |
| `[tool]` | Claude ran a tool; here Bash ran the skill's script |
| `[claude]` | Claude's answer |
| `[done]` | The end: success or error, the number of turns, and the cost estimate (not a charge on Pro) |

Claude followed the skill's instructions in order: first `summary`, then `groupby`. This is exactly as in
the normal `claude` window, but now your own program receives each step.

**If you see something else:**

- `[init] auth: ANTHROPIC_API_KEY - billed per token to that API account!`: an API key is set, and
  that account would pay. Remove it (Lesson 0, section 1).
- A `[refused]` line: a tool call failed, for example a tool that is not in `allowed_tools`, or a skill
  that is not offered (Step 6). The text after it says why.

### Step 5 - Read the important part of the program

**What:** the core of `agent\run_agent.py`.

**Why:** you will copy this for your own agents.

```python
options = ClaudeAgentOptions(
    cwd=str(PROJECT_ROOT),          # the project folder; skills are read from its .claude/skills
    setting_sources=["project"],    # load only this project's skills and settings
    skills="all",                   # or a list, for example ["converting-units", "calculating-dates"]
    allowed_tools=["Skill", "Read", "Bash(python *)", "PowerShell(python *)"],
    max_turns=15,
)

async for message in query(prompt=prompt, options=options):
    if isinstance(message, SystemMessage) and message.subtype == "init":
        print(message.data["skills"])                 # -> the [init] line
    elif isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, ToolUseBlock) and block.name == "Skill":
                print("picked:", block.input["skill"])    # -> the [skill] line
```

**How it works:**

| Line | What it does | Why |
|---|---|---|
| `cwd=str(PROJECT_ROOT)` | starts Claude Code in the project folder | Claude Code finds skills in `.claude\skills\` of the folder it starts in |
| `setting_sources=["project"]` | loads the project's settings and skills, not your personal ones | the agent behaves the same on every computer |
| `allowed_tools=[...]` | the tools that may run without a question | nobody can answer permission questions. Without `"PowerShell(python *)"`, the run would stop on Windows, where Claude often uses PowerShell |
| `max_turns=15` | stops after 15 turns | a run that goes wrong can't use up your allowance |
| `query(prompt=..., options=...)` | sends the question | |
| `async for message in ...` | receives the steps one by one, **while** Claude works | you can print each step at once |
| `SystemMessage`, `AssistantMessage`, `ResultMessage` | the kinds of steps: the session start, Claude used a tool or wrote text, and the end | you check the kind with `isinstance` |
| `ToolUseBlock` with `block.name == "Skill"` | Claude called the Skill tool. `block.input["skill"]` is the skill's name | the same Skill tool call you see in the normal window (Lesson 2) |

The full program is `agent\run_agent.py`. Open it with `notepad agent\run_agent.py`.

### Step 6 - Make an agent that knows only some skills

**What:** `--skills` sets the `skills` option to a list.

**Why:** a specialized agent should be offered only the skills it needs. Fewer skills mean an easier
choice and a smaller menu.

**Run:**

```bat
python agent\run_agent.py --model haiku --skills converting-units,calculating-dates "How many km is a marathon?"
```

**Expected result** (a real run):

```text
[init] auth: claude.ai subscription (Pro/Max usage, no API billing)
[init] model: claude-haiku-5-5
[init] skills discovered: ['analyzing-csv', 'analyzing-excel', ...]

[skill] Claude picked: converting-units
[tool]  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/converting-units/scripts/convert.py" convert 26.2 mi km
[claude] A marathon is **42.195 km** (about 26.2 miles). ...
[done] success, turns=4, cost≈$0.0045 (API list-price estimate)
```

**How to read it:** Claude is **offered** only these two skills. The `[init]` line still lists all
skills found on disk, because the list only filters what Claude is offered. With different `--skills`
lists, you can make several specialized agents from one set of skills.

**The skills list is not a lock.** A test with only `converting-units` allowed asked: "Use the
calculating-dates skill to tell me what weekday 2026-12-25 is." Two runs, two behaviors:

- Run 1: Claude tried the Skill tool. Claude Code **refused** (the skill is not in the list), and Claude
  worked out the answer without it.
- Run 2: Claude found `.claude\skills\calculating-dates\SKILL.md` with its Read tool and ran `dates.py`
  itself, because `allowed_tools` allows `python` commands.

So the list only decides what Claude is offered. To really keep an agent away from a skill, give that
agent its own project folder (`cwd`) that contains only its skills.

## Part 2 - Your own Python functions as tools (no skills)

### Step 7 - Run the tools program

**What:** `agent\custom_tools_agent.py` gives Claude three Python functions as **tools**, and no
skills and no shell.

**Why:** a skill makes Claude run a **command** and read printed text. A tool lets Claude call your
**function directly**, with checked parameters. This is the other way to connect Claude to your Python.

**Run:**

```bat
python agent\custom_tools_agent.py "How many km is 26.2 miles, and what weekday is 2026-12-25?"
```

**Expected result** (a real run):

```text
[tool] mcp__tutor__convert_units({'value': 26.2, 'from_unit': 'mile', 'to_unit': 'km'})
[tool] mcp__tutor__weekday({'date': '2026-12-25'})

- 26.2 miles is about 42.16 km. ...
- 2026-12-25 is a Friday. It falls in ISO week 52.
```

**How to read it:** Claude **called two Python functions directly**. The `[tool]` lines show the
function names and, in parentheses, the values Claude chose for the parameters. Claude wrote `'mile'`
instead of `'mi'`, and it still worked, because the `convert()` function knows such alternative names.

### Step 8 - Read how a function becomes a tool

**What:** the parts of `agent\custom_tools_agent.py` that make a tool.

**Why:** to write tools for your own functions.

```python
@tool("convert_units", "Convert a number between units of length, mass, ...",
      {"value": float, "from_unit": str, "to_unit": str})
async def convert_units(args):
    return as_result(convert_module.convert(args["value"], args["from_unit"], args["to_unit"]))
```

**How it works:**

- `@tool(...)` turns the function below it into a tool. It takes three things. The first is the
  **name** (`convert_units`). The second is a **description**: Claude reads it to decide when to use the
  tool, like a skill's description. The third is the **parameters**, with their types (a number and two
  texts).
- When Claude uses the tool, the function receives `args`, a dictionary such as
  `{"value": 26.2, "from_unit": "mile", "to_unit": "km"}`. The types are checked before your function runs.
- It calls the **same `convert()` function** that the `converting-units` skill runs. `as_result(...)`
  wraps the returned dictionary in the form the SDK expects.

```python
def sdk_tool_server():
    ...                                  # the three @tool functions, like the one above
    return create_sdk_mcp_server(name="tutor", version="1.0.0",
                                 tools=[convert_units, weekday, add_business_days])

options = ClaudeAgentOptions(
    mcp_servers={"tutor": sdk_tool_server()},
    allowed_tools=["mcp__tutor__*"],
    tools=[],
    setting_sources=[],
)
```

| Line | What it does |
|---|---|
| `create_sdk_mcp_server(...)` | collects the three tools into a "tool server" named `tutor`. It runs inside your Python program. (MCP is the standard way to give Claude extra tools) |
| `allowed_tools=["mcp__tutor__*"]` | Claude Code names these tools `mcp__<server>__<tool>`, as you saw in the `[tool]` lines. The `*` allows all tools of the `tutor` server |
| `tools=[]` | removes the built-in tools (Read, Bash, ...), so Claude can use **only** your functions |
| `setting_sources=[]` | loads no skills from disk |

**The same tools with `claude -p`:** add `--cli`.

```bat
python agent\custom_tools_agent.py --cli "How many km is 26.2 miles, and what weekday is 2026-12-25?"
```

**Expected result** (a real run, 8 seconds):

```text
[init] auth: claude.ai subscription
[tool] mcp__tutor__convert_units({'value': 26.2, 'from_unit': 'mi', 'to_unit': 'km'})
[tool] mcp__tutor__weekday({'date': '2026-12-25'})

- **26.2 miles is about 42.16 km** (42.164813). That's roughly the length of a marathon.
- **2026-12-25 is a Friday**, in ISO week 52.
```

**How it works:** `claude -p` can't call functions inside your Python program. So with `--cli`, a
separate program serves the same three tools: `agent\tutor_mcp_server.py`. Claude Code starts it
itself (`--mcp-config` says how). That program shows what MCP really is: it reads one JSON
message per line on stdin, and answers each one on stdout:

| Message from Claude Code | The server's answer |
|---|---|
| `initialize` | its name, and "I have tools" |
| `tools/list` | each tool's name, description, and parameters (as JSON Schema) |
| `tools/call` | runs one function with Claude's values, and returns its result as JSON text |

It uses only the standard library: no SDK, no `mcp` package. A stand-alone tool server has a bonus:
the interactive `claude` window can use it too, after `claude mcp add tutor -- python agent/tutor_mcp_server.py`
(`claude mcp remove tutor` removes it again).

**Skills or tools?** Use both:

| | Skill + script | `@tool` function |
|---|---|---|
| Can carry step-by-step know-how (checklists, rules) | **yes**: the whole SKILL.md | only a short description |
| How the code runs | Claude runs a shell command and reads the printed JSON | Claude calls the function directly with checked parameters |
| Works in the normal `claude` window, without a program | **yes** | only as a separate tool server program, like `tutor_mcp_server.py` |
| Best for | jobs with several steps, files, team rules | single exact actions: look up, convert, call a web service |

## Part 3 - Ask Claude from Python with only Pro (no API key)

**The problem:** with an API key, a Python program would use the `anthropic` package. **Pro gives you
no API key**, so that package can't log in.

**The solution:** your program asks **Claude Code**, which has your login, with `claude -p`.

### Step 9 - Ask with `claude -p` directly in cmd

**What:** `-p` is headless mode: Claude Code answers one question, prints the answer, and ends.

**Why:** first see it by hand. Step 10 then does exactly the same from Python.

**Run:**

```bat
claude -p "What is 17 * 23? Answer with the number only." --model haiku
```

**Expected result:**

```text
391
```

**How to read it:** no window, no conversation: one question, one answer, with your Pro login.

**Now ask for the answer as JSON,** which is easy for a program to read:

**Run:**

```bat
claude -p "What is 17 * 23? Answer with the number only." --model haiku --output-format json
```

**Expected result** (the important fields of a real run; the answer was worded differently this time):

```text
{
 "type": "result",
 "subtype": "success",
 "is_error": false,
 "result": "17 * 23 = 391",
 "num_turns": 1,
 "duration_ms": 3660,
 "total_cost_usd": 0.00236645
}
```

**How to read it:** `result` is the answer, `is_error` tells whether it worked, and `total_cost_usd`
is the cost estimate (not a charge on Pro). A Python program can run this command and read `result`.

### Step 10 - The same from a Python program

**What:** `agent\ask_claude.py` does Step 9 with Python's `subprocess` module. It needs only the
standard library.

**Why:** this is how you use Claude as a normal "question in, answer out" LLM in your own Python code,
with only Pro.

**Run:**

```bat
python agent\ask_claude.py "Explain a Python decorator in two sentences."
```

**Expected result** (a real run):

```text
A Python decorator is a function that takes another function as input, wraps it with extra behavior, and returns the modified function, letting you change or extend its behavior without editing its code. You apply it with the `@` syntax above a function definition, ...

--- {"is_error": false, "model_usage": ["claude-haiku-5-5"], "thinking_tokens": 0, "cost_estimate_usd": 0.00039922, "duration_ms": 4288} (cost is an API list-price estimate; on Pro nothing is charged)
```

**Run:** (structured output: you describe the shape of the JSON, and the answer follows it)

```bat
python agent\ask_claude.py --schema "List three European capitals."
```

**Expected result:**

```text
{
  "capitals": [
    {"country": "France", "capital": "Paris"},
    {"country": "Germany", "capital": "Berlin"},
    {"country": "Italy", "capital": "Rome"}
  ]
}
```

**How it works,** the important part of the program:

```python
cmd = [
    claude, "-p", question,
    "--output-format", "json",      # print one JSON object: answer, usage, cost estimate
    "--model", model,
    "--system-prompt", system,      # your own instructions instead of Claude Code's coding instructions
    "--tools", "",                  # no tools at all: just a question and an answer
    "--disable-slash-commands",     # no skills either
    "--no-session-persistence",     # don't save it in the session list
]
data = json.loads(subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8").stdout)
answer = data["result"]
```

- `subprocess.run` runs the command like typing it in cmd, and `capture_output=True` collects what it
  prints instead of showing it.
- `json.loads` turns the printed JSON into a Python dictionary. `data["result"]` is the answer.
- `--schema` adds `--json-schema` with a description of the wanted JSON shape. The answer is then
  in `data["structured_output"]`.

**Rules:**

| Rule | Why |
|---|---|
| **For your own use only** | a program for other people must use an API key (Lesson 0, section 5) |
| **Never copy the login token** out of `.credentials.json` into your own code | it is a password to your account. Always go through `claude` or the SDK |
| **Don't add `--bare`** | that mode ignores your Pro login and expects an API key |
| **Watch for `ANTHROPIC_API_KEY`** | if it is set, `claude -p` uses it and bills that API account. `ask_claude.py` warns you about this |

## Part 4 - `claude -p` or the SDK: the same jobs both ways

**The idea:** both ways run the **same** Claude Code program, with the same login, the same skills,
the same models and the same allowance. The SDK even starts `claude.exe` itself (Step 2). So the
question is never "which one is smarter", only "**how much does my Python program need to take part
while Claude works?**". This part shows it with real runs. First comes one job done both ways, then jobs
where `claude -p` is simpler, then jobs where the SDK is simpler. Those are done both ways too:
every agent program of the course has a `claude -p` way. The option `--cli` switches it on (Step 16
lists them).

Every run below used Haiku and was copied from the course machine. Times are wall-clock times,
measured in cmd.

### Step 11 - The same job both ways

**What:** one skills job, `Build a pivot of amount by region and product from data/sales.xlsx.`,
first with `claude -p`, then with `run_agent.py`.

**Why:** to compare what you get back, when the job and the result are the same.

**Run, way 1:** `claude -p` (one command, nothing to install)

```bat
claude -p "Build a pivot of amount by region and product from data/sales.xlsx." --model haiku --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)"
```

**How it works:** `--allowedTools` lists the tools that may run without a question, the same list as
`allowed_tools` in `run_agent.py`. Without `Skill` in it, the skill would not load (Lesson 7, Step 10).

**Expected result** (a real run, 22 seconds):

```text
Here is the sum of `amount` by region (rows) and product (columns) from the `Sales` sheet of `data/sales.xlsx`:

| region | Gadget | Gizmo | Widget | Total |
|--------|-------:|------:|-------:|------:|
| East   | 160    | 600   | 150    | 910   |
| North  | 0      | 1650  | 500    | 2150  |
| South  | 320    | 150   | 200    | 670   |
| West   | 400    | 0     | 500    | 900   |
| **Total** | **880** | **2400** | **1350** | **4630** |

Gizmo is the largest product at 2400, and North is the largest region at 2150. I used the `Sales` sheet; the `Targets` sheet was not included.
```

**Run, way 2:** the SDK program

```bat
python agent\run_agent.py --model haiku "Build a pivot of amount by region and product from data/sales.xlsx."
```

**Expected result** (a real run, 18 seconds; the `skills discovered` line is left out):

```text
[init] auth: claude.ai subscription (Pro/Max usage, no API billing)
[init] model: claude-haiku-5-5

[skill] Claude picked: analyzing-excel
[tool]  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/analyzing-excel/scripts/excel_tool.py" sheets data/sales.xlsx
[tool]  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/analyzing-excel/scripts/excel_tool.py" pivot data/sales.xlsx --sheet Sales --index region --columns product --values amount --agg sum
[claude] Here is the sum of `amount` by region (rows) and product (columns), from the `Sales` sheet of `data/sales.xlsx`:
...the same table...
[done] success, turns=5, cost≈$0.0019 (API list-price estimate)
```

**How to read it:**

| | `claude -p` | `run_agent.py` (SDK) |
|---|---|---|
| The answer | the same table | the same table |
| What you get back | only the final text | every step: the skill, each command, the answer, turns and cost |
| Time | about 20 seconds | about 20 seconds: the SDK starts the same `claude.exe` |
| What you needed | one command | the SDK (about 270 MB) and a 100-line Python program |

**Good to know:** `claude -p` can show the steps too. With `--output-format stream-json --verbose`,
it prints one JSON line per step, and your program reads them. `tools\routing_eval.py` does exactly
that (Lesson 5, Test 4). The SDK reads the same lines for you, and turns them into Python objects.
So for one job, the SDK is more convenient, not more capable.

**Run, way 3:** the same program, the `claude -p` way

```bat
python agent\run_agent.py --cli --model haiku "Build a pivot of amount by region and product from data/sales.xlsx."
```

**Expected result** (a real run, 18 seconds; the `skills discovered` line is left out):

```text
[init] auth: claude.ai subscription (Pro/Max usage, no API billing)
[init] model: claude-haiku-5-5

[skill] Claude picked: analyzing-excel
[tool]  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/analyzing-excel/scripts/excel_tool.py" sheets data/sales.xlsx
[tool]  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/analyzing-excel/scripts/excel_tool.py" pivot data/sales.xlsx --sheet Sales --index region --columns product --values amount --agg sum
[claude] Here is the sum of `amount` by region and product from the `Sales` sheet of `data/sales.xlsx`:
...the same table...
[done] success, turns=5, cost≈$0.0036 (API list-price estimate)
```

**How it works:** with `--cli`, `run_agent.py` doesn't use the SDK at all:

| Function | What it does |
|---|---|
| `build_cli_command()` | writes the SDK options as the flags the SDK itself passes to `claude.exe` (Step 2): `--system-prompt ""`, `--allowedTools "Skill,Read,Bash(python *),PowerShell(python *)"`, `--max-turns 15`, `--setting-sources project`, plus `-p "<question>" --output-format stream-json --verbose` |
| `run_cli()` | starts that command with `subprocess`, and reads its output line by line, while Claude works |
| `print_event()` | prints each JSON line with the same labels as `print_message()` does for the SDK's objects |

The steps and the answer are the same, and the `--cli` way needs only the standard library.

**The one difference: `--skills`.** The SDK tells `claude.exe` in its start-up message to offer only
the listed skills. `claude -p` has no flag for that. With `--cli --skills converting-units`, Claude
still sees all skills. Only the listed ones are pre-approved (`Skill(converting-units)`), and Claude
Code refuses the others.

### Step 12 - Where `claude -p` wins: text in, text out, from any command line

**What:** you send a file into Claude through a pipe, and save the answer in a file. No Python at all.

**Why:** this is the most common small job: summarize, translate, check a text. With `claude -p`, it
is one line in cmd, a `.bat` file, or any program that can start a command.

**Run:**

```bat
type data\article.txt | claude -p "Summarize this text in 3 short bullet points." --model haiku > summary.txt
```

```bat
type summary.txt
```

**How it works:**

| Part | What it does |
|---|---|
| `type data\article.txt` | prints the article |
| `\|` | sends that text into `claude -p` as stdin, instead of to the screen. Claude gets the text together with your prompt |
| `> summary.txt` | saves what `claude -p` prints in a file, instead of showing it |

**Expected result** (a real run, 7 seconds):

```text
- Language models get exact tasks like adding a column of numbers approximately right, which isn't good enough for invoices, deadlines, or doses. Pair them with small, well-tested tools and tell them when to use each one.
- A skill divides the work: its description says when it applies, its body explains how to do the job, and its script handles the part that must be exact. The model picks the skill, runs the script, and explains the result.
- Keeping the logic in a testable, reviewable file keeps prompts short, saves context space, and stops answers from drifting. Start with one skill, watch where the model hesitates, and write the next one there.
```

Delete the practice file afterwards: `del summary.txt`

### Step 13 - Where `claude -p` wins: a scheduled job without Python

**What:** `agent\daily_report.bat`, a job for Windows Task Scheduler. It asks one question with the
Excel skill, and saves the answer in `reports\daily_report.txt`.

**Why:** a scheduled job runs when nobody is at the computer. It must be small and need nothing
but Claude Code. Here there is no Python program and no SDK.

**Run:** (`type` shows the file, `call` runs it)

```bat
type agent\daily_report.bat
```

```bat
call agent\daily_report.bat
```

**The file:**

```bat
@echo off
call C:\pyenvsmy\claudeclioct26\Scripts\activate.bat
cd /d "%~dp0.."
if not exist reports mkdir reports
claude -p "Which region has the highest total amount in data/sales.xlsx? Answer in one sentence." --model haiku --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)" --no-session-persistence > reports\daily_report.txt
type reports\daily_report.txt
```

**How it works,** line by line:

| Line | Why it is there |
|---|---|
| `call ...\activate.bat` | a scheduled task has no prepared cmd window, so the job activates the venv itself. Without it, the Excel skill gets the "pandas is not installed" message (Lesson 0, "What happens if you forget to activate") |
| `cd /d "%~dp0.."` | `%~dp0` is the folder of the `.bat` file (`agent\`), and `..` is one folder up: the project folder, where the skills are |
| `if not exist reports mkdir reports` | creates the folder for the answer, the first time |
| `claude -p ... --no-session-persistence > reports\daily_report.txt` | asks the question and saves the answer. `--no-session-persistence` keeps the daily runs out of your session list |
| `type reports\daily_report.txt` | shows the answer, for when you run the job by hand |

**Expected result** (a real run, 17 seconds):

```text
North has the highest total amount in data/sales.xlsx, at 2,150 across the Sales sheet (ahead of West at 900, East at 910 and South at 670).
```

**To run it every morning at 8:00,** Windows Task Scheduler can start it. This command creates such a
task (it was not run on the course machine, because it really creates a task):

```bat
schtasks /create /tn "Sales report" /tr "E:\may10\claudecodecli_and_python\agent\daily_report.bat" /sc daily /st 08:00
```

To remove the task again: `schtasks /delete /tn "Sales report" /f`. The task runs as you, with your
saved login. For a task that runs while you are logged out, see `claude setup-token` in Lesson 0,
section 5.

### Step 14 - Where the SDK wins: a conversation with follow-up questions

**What:** `agent\chat_agent.py` asks two questions in **one** conversation. The second one, "And
which region sold the least?", only makes sense together with the first.

**Why:** a chat program, or any program that asks follow-up questions, needs Claude to remember the
earlier questions and answers.

**Run:**

```bat
python agent\chat_agent.py --model haiku
```

**Expected result** (a real run; the `skills discovered` line is left out):

```text
[you]   Which region sold the most in data/sales.csv?
[init] auth: claude.ai subscription (Pro/Max usage, no API billing)
[init] model: claude-haiku-5-5

[tool]  Read: E:\may10\claudecodecli_and_python\data\sales.csv
[claude] **North** sold the most in `data/sales.csv`, with a total amount of **2,150** across four orders.
...a table of all four regions...

[done] success, turns=2, cost≈$0.0011 (API list-price estimate)
[time]  question 1 took 6.2s

[you]   And which region sold the least?
[claude] **South** sold the least by amount, with a total of 670. By units, **East** sold the least, with 12 against South's 13.

[done] success, turns=1, cost≈$0.0015 (API list-price estimate)
[time]  question 2 took 1.2s
```

**How to read it:**

- Claude understood "the least" without being told the file again: the first question and answer are
  still in the conversation.
- The second question took **1.2 seconds**, because `claude.exe` was already running.
- In this run, Claude read the small CSV file directly, instead of using the skill. `Read` is in
  `allowed_tools`, so this is allowed. With a bigger file, or the Excel file, Claude uses the skill.

**How it works,** the core of `agent\chat_agent.py`:

```python
async with ClaudeSDKClient(options=build_options("all", model)) as client:   # starts claude.exe once
    for question in questions:
        await client.query(question)                     # same session: Claude sees the earlier turns
        async for message in client.receive_response():  # this question's steps, up to its ResultMessage
            print_message(message)
```

`ClaudeSDKClient` keeps one `claude.exe` and one conversation open until the `async with` block ends.
`build_options` and `print_message` come from `run_agent.py`, so all three agent programs work the
same way. **Try it:** `python agent\chat_agent.py --model haiku --interactive` lets you type your own
questions. An empty line ends the chat.

**The same program with `claude -p`:** add `--cli`.

```bat
python agent\chat_agent.py --cli --model haiku
```

**Expected result** (a real run; the `[init]` lines are left out):

```text
[you]   Which region sold the most in data/sales.csv?
[tool]  Read: E:\may10\claudecodecli_and_python\data\sales.csv
[claude] **North** sold the most, with total sales of **2,150** (by `amount`).
...a table of all four regions...
[done] success, turns=2, cost≈$0.0024 (API list-price estimate)
[time]  question 1 took 8.4s

[you]   And which region sold the least?
[claude] **South** sold the least, with total sales of **670** (by `amount`).
...
[done] success, turns=1, cost≈$0.0028 (API list-price estimate)
[time]  question 2 took 5.6s
```

**How to read it:** Claude remembered the first question here too. But each question started a new
`claude` process, which loaded the saved conversation from disk again. That took **5.6 seconds** for a
one-turn follow-up. The SDK way, run the same day on the same machine, took **0.9 seconds** for it.

**How `--cli` does it,** in `chat_cli()`: the last JSON line of each answer (the `result`) contains a
`session_id`. The program keeps it, and passes it to the next question with `--resume`:

```python
result = run_cli(build_cli_command(claude, question, "all", model, resume=session_id))
session_id = result.get("session_id") or session_id   # the next question continues this conversation
```

**The same by hand, in cmd:** ask the first question with `--output-format json`:

```bat
claude -p "Build a pivot of amount by region and product from data/sales.xlsx." --model haiku --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)" --output-format json
```

**Expected result** (the important fields of a real run):

```text
"result": "Here is the sum of `amount` by region and product, ...",
"num_turns": 5,
"duration_ms": 16128,
"session_id": "da79f480-1a45-4aad-a6b9-71243cdf4e3a"
```

Then pass **your** `session_id` (yours is different) to `--resume`:

```bat
claude -p "Which product sold the most in that pivot?" --resume da79f480-1a45-4aad-a6b9-71243cdf4e3a --model haiku --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)" --output-format json
```

**Expected result** (a real run, 5.8 seconds):

```text
"result": "Gizmo sold the most, with 2400 in total `amount`. That is 52% of the 4630 grand total. Widget is second at 1350 and Gadget is third at 880.",
"num_turns": 1,
"session_id": "da79f480-1a45-4aad-a6b9-71243cdf4e3a"
```

**How to read it:** Claude remembered the pivot. But each question started a new `claude.exe`, which
loaded the saved conversation again. That took 5.8 seconds for a one-turn follow-up, against 1.2
seconds with `ClaudeSDKClient`. And your program had to read `session_id` from the first answer, and pass it on.
(`--continue` instead of `--resume <id>` continues the most recent conversation in this folder. That
is shorter, but if you used `claude` in between, it continues the wrong one.)

### Step 15 - Where the SDK wins: your Python decides about every tool call

**What:** `agent\guarded_agent.py` runs the skills, but a Python function in the program approves or
refuses **every** shell command and every file change, before it happens.

**Why:** `allowed_tools` and `--allowedTools` are fixed lists, written before Claude starts. Real
programs often need rules with judgment and memory: "only skill scripts", "only files in `data\`",
"at most 6 commands per run", "write each decision to a log".

**Run:**

```bat
python agent\guarded_agent.py --model haiku "Which region sold the most in data/sales.csv? Save the answer in report.txt."
```

**Expected result** (a real run, 18 seconds; the `[init]` lines are left out, and long paths in the
`[guard]` lines are shortened):

```text
[skill] Claude picked: analyzing-csv
[tool]  Bash: head -n 5 data/sales.csv; echo; wc -l data/sales.csv
[guard] DENY  Bash: head -n 5 data/sales.csv; echo; wc -l data/sales.csv  (only python commands that run a skill script are allowed; use a skill)
[refused] PreToolUse:Bash hook error: only python commands that run a skill script are allowed; use a skill
[tool]  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/analyzing-csv/scripts/csv_tool.py" summary data/sales.csv
[guard] ALLOW Bash: python "E:/.../analyzing-csv/scripts/csv_tool.py" summary data/sales.csv  (skill script, command 1 of 6)
[tool]  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/analyzing-csv/scripts/csv_tool.py" groupby data/sales.csv --by region --value amount --agg sum
[guard] ALLOW Bash: python "E:/.../analyzing-csv/scripts/csv_tool.py" groupby data/sales.csv ...  (skill script, command 2 of 6)
[tool]  Write: E:\may10\claudecodecli_and_python\report.txt
[guard] DENY  Write: E:\may10\claudecodecli_and_python\report.txt  (files may only be written inside data/, not E:\may10\claudecodecli_and_python\report.txt)
[refused] PreToolUse:Write hook error: files may only be written inside data/, not E:\may10\claudecodecli_and_python\report.txt
[tool]  Write: E:\may10\claudecodecli_and_python\data\report.txt
[guard] ALLOW Write: E:\may10\claudecodecli_and_python\data\report.txt  (writing inside data/ is allowed)
[claude] **North** sold the most in `data/sales.csv`, with a total amount of 2150.0. ...

I couldn't save the answer as `report.txt` in the project root. A file-write hook only allows writes inside `data/`, so I saved it as **`data/report.txt`** instead. ...

[done] success, turns=8, cost≈$0.0064 (API list-price estimate)
```

**How to read it:** five decisions, each with its reason:

| # | Planned call | Decision | What happened next |
|---|---|---|---|
| 1 | `head ...; wc -l ...` | **denied**: not a skill script | Claude read the reason, and used the skill's script instead |
| 2 | the skill's `summary` command | **allowed**, command 1 of 6 | it ran |
| 3 | the skill's `groupby` command | **allowed**, command 2 of 6 | it ran |
| 4 | Write `report.txt` in the project folder | **denied**: outside `data\` | Claude chose another place |
| 5 | Write `data\report.txt` | **allowed** | Claude saved the answer there, and told you why |

Delete the practice file afterwards: `del data\report.txt`

**How it works:** the rules are plain Python in `agent\guard.py`, so the tests can check them
without Claude (`python -m unittest discover -s tests -k AgentGuard -v`, 5 tests). `guarded_agent.py`
connects them to Claude Code as a **PreToolUse hook**, a Python function inside your program:

```python
async def check_tool(hook_input, tool_use_id, context):
    allowed, reason = guard.check(hook_input["tool_name"], hook_input["tool_input"])
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "permissionDecision": "allow" if allowed else "deny",
                                   "permissionDecisionReason": reason}}

options.hooks = {"PreToolUse": [HookMatcher(matcher="Bash|PowerShell|Write|Edit", hooks=[check_tool])]}
```

| Part | What it does |
|---|---|
| `HookMatcher(matcher="Bash\|PowerShell\|Write\|Edit", ...)` | Claude Code calls `check_tool` before every call of these four tools |
| `guard.check(...)` | your rules. `guard` is one object for the whole run, so it can count commands |
| `"permissionDecision": "deny"` | the call doesn't run. Claude gets `permissionDecisionReason` as the reason, and can try another way |

**Why a hook, and not `can_use_tool`?** The first version of this program used the SDK's
`can_use_tool` function. In its real run, the guard never saw the skill's `python` commands. Claude
Code asks `can_use_tool` only about calls that **no allow rule** covers, and the skill's
`allowed-tools: Bash(python *)` is such a rule. A PreToolUse hook runs before every matching call,
whatever the rules say.

**The same program with `claude -p`:** add `--cli`.

```bat
python agent\guarded_agent.py --cli --model haiku "Which region sold the most in data/sales.csv? Save the answer in report.txt."
```

**Expected result** (a real run, 15 seconds; the `[init]` lines are left out, the answer is shortened):

```text
[tool]  Read: E:\may10\claudecodecli_and_python\data\sales.csv
[tool]  Write: E:\may10\claudecodecli_and_python\report.txt
[guard] DENY  Write: E:\may10\claudecodecli_and_python\report.txt  (files may only be written inside data/, not E:\may10\claudecodecli_and_python\report.txt)
[refused] PreToolUse:Write hook error: files may only be written inside data/, not E:\may10\claudecodecli_and_python\report.txt
[claude] The write hook only allows files inside `data/`, so I'll save the report there instead.
[tool]  Write: E:\may10\claudecodecli_and_python\data\report.txt
[guard] ALLOW Write: E:\may10\claudecodecli_and_python\data\report.txt  (writing inside data/ is allowed)
[claude] North sold the most, with a total amount of 2150 across four rows. ...
[done] success, turns=4, cost≈$0.0086 (API list-price estimate)
```

This time, Claude read the small CSV file with `Read`, which the guard allows, so there was no shell
command to judge. The same rules decided about both writes. Delete `data\report.txt` again.

**How `--cli` does it:** with `claude -p`, the hook can't be a function inside your program. It is a
separate program, `agent\guard_hook.py`, which Claude Code starts before each matching tool call. It
uses the same rules from `guard.py`:

| | SDK way | `--cli` way |
|---|---|---|
| Where the hook is | `check_tool()`, a function in the program | `agent\guard_hook.py`, its own program |
| How it is switched on | `options.hooks = {"PreToolUse": [HookMatcher(...)]}` | `--settings` with the same hook as JSON, made by `hook_settings()` in `run_agent.py` |
| How it gets the planned call | a Python dictionary | the same data as JSON on stdin |
| How it answers | returns the dictionary | prints the same dictionary as JSON on stdout |
| The command counter | a number in the `Guard` object, in memory | a temporary file named by the environment variable `GUARD_STATE`: each call is a new process, which remembers nothing |
| The `[guard]` lines | printed by the function | written to stderr; `--include-hook-events` makes Claude Code pass them back as JSON lines |

A hook script like this also works in `.claude\settings.json`, for the interactive `claude` window
(Lesson 9, Exercise 8). Then it applies to every Claude Code session in the project.

### Step 16 - Which one to choose

Every job in this part can be done both ways. The difference is how much of the work your program
does itself. Here is the whole picture:

| Your situation | Simpler with | Why | Shown in |
|---|---|---|---|
| One question from cmd, a `.bat` file, or another program | `claude -p` | one command, nothing to install | Steps 9, 11 |
| Summarize, translate or check a file, and save the answer | `claude -p` with `\|` and `>` | text in, text out, no program needed | Step 12 |
| A scheduled job | `claude -p` in a `.bat` file | small, no Python program, no SDK | Step 13 |
| A computer where you can't install the SDK | `claude -p` | it needs only Claude Code | |
| Claude as an LLM inside your Python program, one question at a time | `claude -p` through `subprocess` | standard library only | Step 10 |
| Show each step while it happens | either | the SDK gives Python objects; with `claude -p` you read JSON lines (`run_agent.py --cli`) | Steps 4, 11 |
| Many test questions, stop each run as soon as Claude chose a skill | either | `routing_eval.py`, with `--sdk` for the SDK way | Lesson 5 |
| A chat, or many quick follow-up questions | the SDK (`ClaudeSDKClient`) | one process stays open: 0.9 seconds per follow-up, against 5.6 seconds with `--resume` | Step 14 |
| Your own rules decide about each tool call | the SDK (a Python hook) | the rule is a function with your program's memory; with `claude -p` it is a hook script with a state file | Step 15 |
| Your Python functions as tools | the SDK (`@tool`) | the functions run inside your program; with `claude -p` you write a separate tool server program | Steps 7, 8 |

**Rule of thumb:** start with `claude -p`. Switch to the SDK as soon as your Python program must
**take part while Claude works**. For example, it must hold a conversation, decide about tool calls
with its own data, or offer its own functions. All of it works with `claude -p` too, but then you write
the extra pieces yourself. You keep a session id, write a hook script, and write a tool server.

**Every program of the course, both ways:**

| Program | Default | Other way | What the other way needs |
|---|---|---|---|
| `agent\ask_claude.py` | `claude -p` | `--sdk` | the SDK |
| `agent\api_equivalent.py` | `claude -p` | `--sdk` | the SDK |
| `agent\run_agent.py` | the SDK | `--cli` | nothing: the same flags the SDK passes (only `--skills` works differently, Step 11) |
| `agent\chat_agent.py` | the SDK | `--cli` | `--resume <session_id>` for each follow-up |
| `agent\guarded_agent.py` | the SDK | `--cli` | the hook script `agent\guard_hook.py` |
| `agent\custom_tools_agent.py` | the SDK | `--cli` | the tool server `agent\tutor_mcp_server.py` (Step 8) |
| `agent\effort_probe.py` | the SDK | `--cli` | the hook script `agent\effort_hook.py` (Step 24) |
| `tools\run_cost.py` | `claude -p` | `--sdk` | the SDK (Step 28) |
| `tools\routing_eval.py` | `claude -p` | `--sdk` | the SDK (Lesson 5, Step 8) |

The `--cli` ways need only the standard library. One unit test proves it: it blocks every import of
the SDK, then loads all `--cli` parts (`python -m unittest discover -s tests -k need_no_sdk -v`). All
tests of both ways: `-k BothWays` (19 tests).

## Part 5 - Reasoning effort: how much Claude thinks

**The idea:** before it answers, Claude **thinks**: it reasons in tokens that you don't see by default
(Lesson 0, section 7). Thinking tokens count as output tokens, so they use your Pro allowance.
**Effort** tells Claude how much to think. With an API key, you would pass it in your request. With
Pro, you pass it to Claude Code, and Claude Code sends it for you. It works the same in `claude -p` and
in the SDK.

### Step 17 - Where to set the effort

| Where | How | Example |
|---|---|---|
| `claude -p` | the option `--effort` | `claude -p "..." --model sonnet --effort low` |
| Agent SDK | the option `effort=` | `ClaudeAgentOptions(model="sonnet", effort="low")` |
| this course's programs | the option `--effort` | `python agent\ask_claude.py --effort low "..."`, `python agent\run_agent.py --effort low "..."` |
| the interactive `claude` window | the command `/effort` | `/effort low` |
| default for every session | the setting `effortLevel` in `settings.json`, or the environment variable `CLAUDE_CODE_EFFORT_LEVEL` | `"effortLevel": "low"` |
| one skill, while it runs | `effort:` in its SKILL.md frontmatter | `effort: low` (Part 6) |

**The levels:** `low`, `medium`, `high`, `xhigh`, `max`. Without a setting, the model's default is
used. The Claude Code documentation says:

| Fact | What it means for you |
|---|---|
| Opus 5.5, Sonnet 5.5 and Haiku 5.5 already default to `medium` | only `low` can save anything compared with the default |
| You can't turn thinking off on these models. `MAX_THINKING_TOKENS=0` and the SDK's `thinking={"type": "disabled"}` have no effect on them | effort is the only control |
| Effort is a hint, not a limit | Claude still decides per question how much to think. An easy question may get no thinking at all |
| "You are charged for all thinking tokens generated, even when collapsed or redacted" | hidden thinking still uses your allowance |

### Step 18 - Measure it yourself

**What:** you ask the same question with `--effort low` and with `--effort high`, and compare the
thinking tokens.

**Why:** effort helps more on some models and questions than on others. Measuring is the only way to
know for your own jobs.

**Run:** (each run uses a little allowance)

```bat
python agent\ask_claude.py --model sonnet --effort low "How many integers from 1 to 10000 are divisible by 3 or by 5, but not by 7? Answer with the number only."
```

```bat
python agent\ask_claude.py --model sonnet --effort high "How many integers from 1 to 10000 are divisible by 3 or by 5, but not by 7? Answer with the number only."
```

**Expected result** (real runs):

```text
4001

--- {"is_error": false, "model_usage": ["claude-sonnet-5-5"], "thinking_tokens": 98, "cost_estimate_usd": 0.0066911, "duration_ms": 4817} ...
```

```text
4001

--- {"is_error": false, "model_usage": ["claude-sonnet-5-5"], "thinking_tokens": 140, "cost_estimate_usd": 0.0071031, "duration_ms": 5018} ...
```

**How to read it:** both answers are right (4001). `thinking_tokens` is how much Claude thought:
98 with `low`, 140 with `high`. `ask_claude.py` reads it from `modelUsage` in the JSON that
`claude -p --output-format json` prints. Without `ask_claude.py`, you find it there yourself.

**More real measurements,** 3 runs per level, the same question:

| Model | `--effort low` | `--effort high` | Answers |
|---|---|---|---|
| Sonnet 5.5 | 94, 88, 91 thinking tokens (median 91) | 120, 103, 171 (median 120) | all 4001 |
| Haiku 5.5 | 354, 280, 321 (median 321) | 345, 298, 317 (median 317) | all 4001 |

| What the measurements show | Why it matters |
|---|---|
| On Sonnet, `low` thought about 25% less than `high` | effort works, but the saving on one short question is small |
| On Haiku, effort made no measurable difference | the small model decides its thinking itself; don't expect savings there |
| The model matters much more. In these runs, one question cost about **$0.0004 to $0.001 on Haiku**, and **about $0.007 on Sonnet** (API-price estimates) | choosing the model is the biggest lever for your allowance |
| But a cheaper model also makes more mistakes. In Lesson 0, section 4, Haiku chose no skill in 3 of 20 routing tests, and Opus passed all 20 | test a cheaper model on your own jobs before you rely on it |

**Don't compare the cost of single runs.** The first run in a series also pays for writing the cache
(the reusable start of the request). So it can look more expensive, although it thought less.
Compare `thinking_tokens`.

### Step 19 - Effort in your agent programs

**What:** `run_agent.py` and `ask_claude.py` both accept `--effort`.

**Run:**

```bat
python agent\run_agent.py --model haiku --effort low "Which region sold the most in data/sales.csv?"
```

**Expected result** (a real run; the `skills discovered` line is left out):

```text
[init] auth: claude.ai subscription (Pro/Max usage, no API billing)
[init] model: claude-haiku-5-5

[skill] Claude picked: analyzing-csv
[tool]  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/analyzing-csv/scripts/csv_tool.py" summary data/sales.csv
[tool]  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/analyzing-csv/scripts/csv_tool.py" groupby data/sales.csv --by region --value amount --agg sum
[claude] North sold the most in `data/sales.csv`, with a total amount of 2,150.0. The other regions were East at 910.0, West at 900.0 and South at 670.0.

[done] success, turns=5, cost≈$0.0055 (API list-price estimate)
```

**How it works:** one more option in `build_options()` in `run_agent.py`:

```python
return ClaudeAgentOptions(
    ...
    model=model,      # None = your Claude Code default; "haiku" uses less of your plan
    effort=effort,    # None = the model's default; "low" thinks less, "high" more
)
```

In `ask_claude.py`, the `claude -p` way adds `["--effort", effort]` to the command, and the SDK way
passes `effort=effort`. Try the SDK way with the question from Step 18:

```bat
python agent\ask_claude.py --sdk --model sonnet --effort low "How many integers from 1 to 10000 are divisible by 3 or by 5, but not by 7? Answer with the number only."
```

**Expected result** (a real run):

```text
4001

--- {"is_error": false, "thinking_tokens": 85, "cost_estimate_usd": 0.0056171, "duration_ms": 1936} ...
```

85 thinking tokens: the same range as the `claude -p` runs with `low` in Step 18.

**Also good to know:** `claude -p` has `--max-budget-usd`, which stops a run above an estimated cost.
It was not tested with a Pro login while writing this course.

### Step 20 - Your API code, translated to Pro

**What:** `agent\api_equivalent.py` does what this typical API program does, with your Pro login
instead of an API key. It has the same settings at the top: `MODEL`, `EFFORT`, `MAX_TOKENS`, `PROMPT`.

```python
import anthropic

client = anthropic.Anthropic()          # needs ANTHROPIC_API_KEY; billed separately from Pro
response = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=4096,
    thinking={"type": "adaptive"},
    output_config={"effort": "low"},
    messages=[{"role": "user", "content": "Explain Python decorators briefly."}],
)
print(response.content[0].text)
print("Input tokens:", response.usage.input_tokens)
print("Output tokens:", response.usage.output_tokens)
```

**Why:** you know the API way. This step shows each part's Pro counterpart, so you can move your own
API code over.

**Each part, translated:**

| API code | Pro with `claude -p` | Pro with the Agent SDK |
|---|---|---|
| `client = anthropic.Anthropic()` | no client: the `claude` program holds your login | `query(...)` starts Claude Code with your login |
| `model="claude-sonnet-5-5"` | `--model sonnet` (or the full ID) | `model="sonnet"` |
| `output_config={"effort": "low"}` | `--effort low` | `effort="low"` |
| `thinking={"type": "adaptive"}` | nothing to set: the 5.5 models always think adaptively | the same |
| `max_tokens=4096` | the environment variable `CLAUDE_CODE_MAX_OUTPUT_TOKENS=4096` | `env={"CLAUDE_CODE_MAX_OUTPUT_TOKENS": "4096"}` |
| `system="..."` | `--system-prompt "..."` | `system_prompt="..."` |
| `messages=[{"role": "user", "content": ...}]` | the text after `-p` | `prompt=...` |
| no tools | `--tools ""` | `tools=[]` |
| `response.content[0].text` | `data["result"]` from `--output-format json` | `ResultMessage.result` |
| `response.usage` | `data["usage"]` | `ResultMessage.usage` |
| billed per token to the API account | uses your Pro allowance | the same |

Not every API parameter has a Claude Code option, for example `temperature`.

**How it works,** the core of the `claude -p` way:

```python
cmd = [
    claude, "-p", prompt,
    "--model", model,                   # model=MODEL
    "--effort", effort,                 # output_config={"effort": EFFORT}
    "--system-prompt", SYSTEM,          # system=...
    "--output-format", "json",          # one JSON object: the answer and the usage
    "--tools", "",                      # no tools: a plain question and answer, like the API call
    "--disable-slash-commands",         # no skills either
    "--no-session-persistence",         # don't save it as a resumable session
]
env = {**os.environ, "CLAUDE_CODE_MAX_OUTPUT_TOKENS": str(MAX_TOKENS)}     # max_tokens=MAX_TOKENS
data = json.loads(subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env).stdout)
print(data["result"])
```

**Run:** (with the settings at the top of the file: Sonnet, `low`)

```bat
python agent\api_equivalent.py
```

**Expected result** (a real run, the answer shortened):

```text
A decorator is a function that takes another function and returns a modified version of it, letting you add behavior without changing the original code.
...
Input tokens: 830 (new 2, written to cache 828, read from cache 0)
Output tokens: 343 (of which thinking 0)
```

**Now change only the effort,** on Opus, with a question that needs reasoning:

```bat
python agent\api_equivalent.py --model opus --effort low --prompt "How many integers from 1 to 10000 are divisible by 3 or by 5, but not by 7? Answer with the number only."
```

```bat
python agent\api_equivalent.py --model opus --effort high --prompt "How many integers from 1 to 10000 are divisible by 3 or by 5, but not by 7? Answer with the number only."
```

**Expected result** (two real runs):

```text
4001

Input tokens: 4309 (new 2, written to cache 4307, read from cache 0)
Output tokens: 77 (of which thinking 73)
```

```text
4001

Input tokens: 4305 (new 2, written to cache 1358, read from cache 2945)
Output tokens: 100 (of which thinking 96)
```

**How to read it:**

| Line | Meaning |
|---|---|
| `Input tokens: 4309` | everything sent to the model. Your prompt is only a few tokens. Claude Code adds its own text (settings, environment), even with `--system-prompt` and `--tools ""`. In these runs, it was 830 to 4,309 tokens. With the API, only your system prompt and message would be sent |
| `new 2, written to cache ..., read from cache ...` | Claude Code caches the text it sends; reading from the cache is cheaper. The second run re-used 2,945 tokens from the first |
| `Output tokens: 77 (of which thinking 73)` | what Claude wrote. Thinking counts as output, as with the API |
| `low` 73 thinking against `high` 96 | the same model with a different effort, the same right answer (4001). The decorator question had 0 thinking at both levels: easy questions get no thinking |

**The same through the SDK:** `python agent\api_equivalent.py --sdk`. A real run printed an answer of
the same kind, and `Input tokens: 4026 (new 2, written to cache 1107, read from cache 2917)`,
`Output tokens: 467 (of which thinking 0)`.

## Part 6 - Control the effort of each skill, with the same model

**The idea:** you keep one model, for example Opus, for everything. But a lookup skill that runs one
Python command doesn't need deep thinking, while a skill that must interpret results does. So you set
the effort for the whole session, and you let each skill set its own effort while it runs. Everything
in this part was measured with Opus 5.5.

### Step 21 - Set the effort for a whole session

**What:** the ways to choose the effort for everything Claude does in a session, with the same model.

**Why:** the session effort is used for every step that no skill changes, for example the step where
Claude chooses a skill.

| Where | How | Example |
|---|---|---|
| when you start Claude Code | `--effort` | `claude --model opus --effort low` |
| inside a running session | `/effort` | `/effort low`, later `/effort high`. `/effort auto` goes back to the default |
| for one prompt only | the word `ultrathink` anywhere in your prompt | `ultrathink: check these invoice totals` |
| for every session | `"effortLevel": "low"` in `settings.json` | (Lesson 0, section 7 shows how to edit that file) |
| for every session started from one cmd window | the environment variable `CLAUDE_CODE_EFFORT_LEVEL` | `set CLAUDE_CODE_EFFORT_LEVEL=low`, then `claude` |
| `claude -p` | `--effort` | `claude -p "..." --model opus --effort low` |
| the Agent SDK | `effort=` | `ClaudeAgentOptions(model="opus", effort="low")` |
| this course's programs | `--effort` | `python agent\run_agent.py --model opus --effort low "..."` |

Without any of these, Opus 5.5, Sonnet 5.5 and Haiku 5.5 use `medium` (Part 5).

### Step 22 - Give each skill its own effort

**What:** one line in a skill's frontmatter: `effort: low` (or `medium`, `high`, `xhigh`, `max`).

**Why:** the Claude Code documentation says frontmatter effort "applies when that skill or subagent is
active, overriding the session level". So each skill can bring the effort its job needs.

**How to see it:** `agent\effort_probe.py` is `run_agent.py` plus a hook that prints the effort level
Claude Code reports before each tool call. (A hook gets this level in its input, as `effort.level`.)

**Run 1:** without an `effort:` line. Since Step 27, the project's `converting-units` has
`effort: low` as the last frontmatter line. Open `.claude\skills\converting-units\SKILL.md` in
Notepad, delete that line, and save. Then run:

```bat
python agent\effort_probe.py --model opus "Convert 26.2 miles to kilometers."
```

**Expected result** (a real run):

```text
[skill] Claude picked: converting-units
[effort] medium before Skill: converting-units
[tool]  PowerShell: python "E:/may10/claudecodecli_and_python/.claude/skills/converting-units/scripts/convert.py" convert 26.2 mi km
[effort] medium before PowerShell: python "E:/may10/claudecodecli_and_python/.claude/skills/converting-units/scripts/conv
[claude] 26.2 miles is about **42.16 km** (42.164813 km). ...
[done] success, turns=4, cost≈$0.1896 (API list-price estimate)
[usage] claude-opus-5-5: output 321 tokens, of which thinking 21
```

**Do:** put the line `effort: low` back, just before the second `---`, and save.

**Run 2:** the same command again.

**Expected result** (a real run):

```text
[skill] Claude picked: converting-units
[effort] medium before Skill: converting-units
[tool]  PowerShell: python "E:/may10/claudecodecli_and_python/.claude/skills/converting-units/scripts/convert.py" convert 26.2 mi km
[effort] low    before PowerShell: python "E:/may10/claudecodecli_and_python/.claude/skills/converting-units/scripts/conv
[claude] 26.2 miles is **42.16 km**. The exact figure is 42.164813 km, using 1 mile = 1.609344 km. ...
[done] success, turns=4, cost≈$0.0371 (API list-price estimate)
[usage] claude-opus-5-5: output 265 tokens, of which thinking 0
```

**How to read it:**

| Line | What it shows |
|---|---|
| `[effort] medium before Skill` | Claude chose the skill with the **session** effort: `medium`, Opus's default. The skill wasn't active yet |
| `[effort] low before PowerShell` | after the skill loaded, its `effort: low` was in effect, for running the script and writing the answer |
| `thinking 0` (without the line: 21) | Claude didn't think at all for the rest of the job |

It also works when you start the skill yourself: `python agent\effort_probe.py --model opus "/converting-units 26.2 mi km"`
showed `[effort] low` before the command, and `thinking 0`.

**Don't compare the `cost≈` numbers of these two runs:** the first run in a series also pays for
writing the cache (Part 5, Step 18). Compare the thinking tokens.

The file is now as it is in the project again.

### Step 23 - Which effort wins?

**What:** three more real runs, with the skill's `effort:` against the session's effort.

| Session | Skill | Effort before the Skill call | Effort after the skill loaded |
|---|---|---|---|
| `--effort high` | `effort: low` | high | **low**: the skill wins |
| `--effort low` | `effort: high` | low | **high**: the skill wins |
| `set CLAUDE_CODE_EFFORT_LEVEL=high` | `effort: low` | high | **high**: the environment variable wins |

**How to read it:** this matches the documentation: frontmatter effort overrides the session level
"but not the environment variable". So don't set `CLAUDE_CODE_EFFORT_LEVEL` permanently if you want
your skills' effort lines to work. Use `--effort`, `/effort` or `effortLevel` for the session instead.

### Step 24 - How a skill gets its own effort, request by request

**The puzzle:** a skill's instructions are only text that is added to Claude's context. Text can't
change how much the model thinks. So how can a skill have its own effort?

**The answer:** the `effort:` line is not read by Claude, but by **Claude Code**, the program. A
SKILL.md has text for Claude, and settings for Claude Code:

| Part of the SKILL.md | Read by | What happens with it |
|---|---|---|
| `description:` | Claude | it is in the skill list Claude gets with every request (Lesson 2) |
| the instructions after the second `---` | Claude | Claude Code adds them to the conversation when the skill is loaded |
| `allowed-tools:`, `effort:`, `model:`, `context:`, `disable-model-invocation:` | Claude Code | settings for how Claude Code runs this skill. Claude doesn't obey them; Claude Code applies them |

**Every step is a new request.** Claude Code doesn't hold one long call to the model. For every step,
it sends a new request, with the model name, the **effort level**, its instructions and tools, and the
whole conversation so far. (That is why Step 28 shows the context being re-read at every step.) So the
effort is a setting of each request, like the model name: it is not text in the prompt.

**The steps of a real run,** where `converting-units` has `effort: low` and the session uses `medium`:

| # | Who | What happens | Effort of the request |
|---|---|---|---|
| 1 | Claude Code | sends request 1: your question, and the skill list | **medium**: the session |
| 2 | Claude | answers: "call the Skill tool with `converting-units`" | |
| 3 | Claude Code | runs the Skill tool: adds the skill's instructions to the conversation, and notes `effort: low` for the rest of this answer | |
| 4 | Claude Code | sends request 2: the conversation, now with the instructions | **low**: the skill |
| 5 | Claude | answers: "run `python ... convert.py convert 26.2 mi km`" | |
| 6 | Claude Code | runs the Python script on your computer (no tokens), and adds the printed JSON to the conversation | |
| 7 | Claude Code | sends request 3 | **low** |
| 8 | Claude | writes the answer for you | |
| 9 | you | type your next prompt: its requests use **medium** again | |

It is the same agent, the same model and the same conversation all the time. Only the effort setting
that Claude Code sends with the later requests changes.

**See it yourself:** `effort_probe.py` accepts several prompts, and asks them one after the other in
the same conversation.

**Run:** (uses a little allowance)

```bat
python agent\effort_probe.py --model sonnet "Convert 26.2 miles to kilometers." "Now read the file data/article.txt and tell me its first sentence."
```

**Expected result** (a real run; the `[usage]` lines are left out):

```text
[you]   Convert 26.2 miles to kilometers.
[skill] Claude picked: converting-units
[effort] medium before Skill: converting-units
[tool]  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/converting-units/scripts/convert.py" convert 26.2 mi km
[effort] low    before Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/converting-units/scripts/conv
[claude] 26.2 miles is about **42.16 km**. That's marathon distance, and the script gave 42.164813 km.

[done] success, turns=4, cost≈$0.0179 (API list-price estimate)

[you]   Now read the file data/article.txt and tell me its first sentence.
[tool]  Read: E:\may10\claudecodecli_and_python\data\article.txt
[effort] medium before Read: E:\may10\claudecodecli_and_python\data\article.txt
[claude] The file opens with a title, "Why small tools beat big prompts". The first sentence of the body text is: ...

[done] success, turns=2, cost≈$0.0258 (API list-price estimate)
```

**How to read it:** in the first answer, the effort was `medium` until the skill was loaded, then `low`
(steps 1 to 8 of the table). The second prompt didn't use a skill: its request went out with `medium`
again (step 9). The skill's effort lasted until the end of its answer, and no longer.

**The same with `claude -p`:** add `--cli` to the same command. The hook is then the script
`agent\effort_hook.py`, and the second prompt continues the conversation with `--resume`. A real run
printed the same levels: `medium` before the Skill, `low` before the script's command, and `medium`
again before the `Read` of the second prompt. Both ways print the line with the same function:
`effort_line()` in `effort_hook.py`.

### Step 25 - A forked skill: its own agent, model and effort

**What:** with `context: fork` in its frontmatter, a skill doesn't run in your conversation. Claude Code
starts a separate helper agent (a **subagent**) for it. The Claude Code documentation says: "The
skill content becomes the subagent's prompt. The subagent doesn't see your conversation history."
And with `context: fork`, the skill's `model:` "sets the forked subagent's model".

**Why:** in Step 22, the skill changed only the effort of the main agent's requests. A forked skill is a
second agent, with its own requests. So it can have its own model too, also when Claude chose the
skill by itself. (Without `context: fork`, the skill's `model:` line was not used when Claude chose the
skill: Step 28.)

**Do:** open `.claude\skills\converting-units\SKILL.md` in Notepad. After the line `effort: low`, add two
lines, so the frontmatter ends like this:

```text
effort: low
context: fork
model: haiku
---
```

Save the file.

**Run:** the main agent uses Opus

```bat
python agent\effort_probe.py --model opus "Convert 26.2 miles to kilometers."
```

**Expected result** (a real run):

```text
[skill] Claude picked: converting-units
[effort] medium before Skill: converting-units
[tool]  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/converting-units/scripts/convert.py" convert 26.2 mi km
[effort] low    before Bash (in subagent general-purpose): python "E:/may10/claudecodecli_and_python/.claude/skills/converting-units/scripts/conv
[claude] 26.2 miles is **42.164813 km**, or about **42.16 km**. That's the length of a marathon. ...
[done] success, turns=2, cost≈$0.0275 (API list-price estimate)
[usage] claude-opus-5-5: output 181 tokens, of which thinking 22
[usage] claude-haiku-5-5: output 157 tokens, of which thinking 0
```

**How to read it:**

| Line | What it shows |
|---|---|
| `[effort] medium before Skill` | the main agent (Opus, `medium`) chose the skill |
| `[effort] low before Bash (in subagent general-purpose)` | the subagent ran the script, at the skill's `low` effort. `general-purpose` is the default kind of subagent (the `agent:` line can choose another) |
| `[usage] claude-opus-5-5 ...` | the main agent's work: choosing the skill, and writing your answer from the subagent's result |
| `[usage] claude-haiku-5-5 ...` | the subagent's work, on Haiku, with no thinking |

**Clean up:** remove the two lines `context: fork` and `model: haiku` again, and save.

**Ordinary or forked skill?**

| | Ordinary skill | Skill with `context: fork` |
|---|---|---|
| Who runs it | the same agent, in your conversation | a separate subagent, with its own context |
| Sees your conversation | yes | no: the instructions must contain everything it needs |
| Its own `effort:` | yes (Step 22) | yes |
| Its own `model:` | in these tests only when you start it with `/skill-name` (Step 28) | yes, also when Claude chooses it |
| Extra cost | none | the subagent builds its own context from the start |
| Good for | short jobs: run a script, report the result | jobs that need another model, or big reading jobs that would fill your conversation (Lesson 4, Step 5) |

### Step 26 - Low or high: prove it with two copies of one skill

**What:** an experiment where **only** the effort differs. You make two copies of `calculating-dates`
that are identical except for two frontmatter lines, and ask the same question through each.

**Why:** to prove that the same agent really works with a different effort when a different skill
runs. The system prompt and the model stay the same. You also see what that changes in the result.

**Do:**

1. Make the two copies:
   ```bat
   xcopy /e /i .claude\skills\calculating-dates .claude\skills\dates-low
   ```
   ```bat
   xcopy /e /i .claude\skills\calculating-dates .claude\skills\dates-high
   ```
   **Expected result,** for each copy: the copied files, and `5 File(s) copied` (your number can
   differ: Python's `__pycache__` files are copied too, if they exist).
2. Open `.claude\skills\dates-low\SKILL.md` in Notepad. Change `name: calculating-dates` to
   `name: dates-low`, and `effort: high` to `effort: low`. Save.
3. Open `.claude\skills\dates-high\SKILL.md`. Change only the name: `name: dates-high`. It keeps
   `effort: high`. Save.

Now the two files differ only in `name:` and `effort:`. Both copies are in the project at the same
time, so every run below gets **the same** system prompt and skill list.

**Run:** the same question through each copy, with `/name` so you choose the copy. Each command is a
fresh session. Run each twice. (Each run uses some allowance, more with Opus.)

```bat
python agent\effort_probe.py --model opus "/dates-low How many working days are there from 2026-12-21 to 2027-01-08, if 2026-12-24, 2026-12-25, 2026-12-31 and 2027-01-01 are holidays? Answer with the number and one sentence."
```

```bat
python agent\effort_probe.py --model opus "/dates-high How many working days are there from 2026-12-21 to 2027-01-08, if 2026-12-24, 2026-12-25, 2026-12-31 and 2027-01-01 are holidays? Answer with the number and one sentence."
```

**Expected result** (real runs on the course machine, round 1, shortened):

```text
/dates-low
[tool]  PowerShell: python ".../dates-low/scripts/dates.py" business_days_between --start 2026-12-21 --end 2027-01-08 --holidays ...
[effort] low    before PowerShell: ...
[tool]  Grep: {'pattern': 'def business_days_between', ...}
[effort] low    before Grep:
[claude] **11 working days** if you count both 2026-12-21 (a Monday) and 2027-01-08. The script reported 10 because it doesn't count the start date. ...
[usage] claude-opus-5-5: output 595 tokens, of which thinking 171
```

```text
/dates-high
[tool]  PowerShell: python ".../dates-high/scripts/dates.py" business_days_between --start 2026-12-21 --end 2027-01-08 --holidays ...
[effort] high   before PowerShell: ...
[claude] The script returned 10, but counting by hand I get 11: 3 + 3 + 5 across the three weeks. I'll check whether the script leaves out one of the end dates.
[tool]  PowerShell: python ".../dates-high/scripts/dates.py" --list
[effort] high   before PowerShell: ...
[claude] **11 working days.** ... The script's `business_days_between` returned **10** because it doesn't count the start date. ...
[usage] claude-opus-5-5: output 677 tokens, of which thinking 192
```

**All four runs:**

| Round | Skill copy | Effort at every step | Thinking tokens | Steps after the first command | Answer |
|---|---|---|---|---|---|
| 1 | `dates-low` | low | 171 | read the function with Grep | 11; the script counts from the day after the start |
| 1 | `dates-high` | high | 192 | said "I'll check", ran `--list` | 11; the same explanation |
| 2 | `dates-low` | low | 175 | ran `--list` | 11; the same explanation |
| 2 | `dates-high` | high | 201 | said "I'll check", ran `--list` | 11; the same explanation |

**How to read it:**

- **The proof:** same project, same system prompt and skill list, same model (Opus), same question,
  and instructions that are identical word for word. Only the `effort:` line differs. The hook
  reported `low` at every step of `/dates-low`, and `high` at every step of `/dates-high`. Claude Code
  sent each request with the skill's effort (Step 24).
- **The effect:** `high` thought more in both rounds, but only about 12% to 15% more (192 against 171,
  201 against 175). Both copies checked how the script counts, and all four answers were right.
  `business_days_between` counts the days **after** the start date, up to and including the end date.
  So it gives 10 where you'd count 11.
- **An earlier single pair of runs** of this question, when Claude chose the skill itself, gave 208
  thinking tokens with `low` and 373 with `high`. There, the `low` run explained the script wrongly
  ("doesn't count the end date"). The four runs above show that this was not the rule: `low` was right
  every time. One pair of runs is too little to judge an effort level.
- **So:** effort reliably changes the setting, but how much it changes the thinking depends on the
  question. Here the difference was small. `low` fits skills where the script does the work and
  Claude reports the result. For skills where Claude must check or interpret, try both levels on
  your own questions, several times, before you decide.

**One request, one effort:** the effort belongs to a whole request. Inside one request, all the text is
handled with the same effort. A skill changes the effort of the requests that are sent while it is
active (Step 24). It can't give one part of a request's text a different effort.

**Clean up:** delete both copies:

```bat
rmdir /s /q .claude\skills\dates-low
```

```bat
rmdir /s /q .claude\skills\dates-high
```

### Step 27 - Plan the effort of your skills

**What:** the effort that each skill of this project has, as the last line of its frontmatter, with
the reason. Check any of them with `effort_probe.py`, and change the line if your questions need more
or less thinking.

**See them all:**

```bat
findstr /s /b "effort:" .claude\skills\SKILL.md
```

**Expected result:**

```text
.claude\skills\analyzing-csv\SKILL.md:effort: low
.claude\skills\analyzing-excel\SKILL.md:effort: low
.claude\skills\analyzing-text\SKILL.md:effort: low
.claude\skills\calculating-dates\SKILL.md:effort: high
.claude\skills\calculating-invoices\SKILL.md:effort: high
.claude\skills\clear-todos\SKILL.md:effort: low
.claude\skills\converting-units\SKILL.md:effort: low
.claude\skills\plotting-charts\SKILL.md:effort: medium
.claude\skills\tracking-todos\SKILL.md:effort: low
```

| Skill | Effort | Why |
|---|---|---|
| `converting-units` | low | one command; Claude only reports the result (Step 22) |
| `tracking-todos`, `clear-todos` | low | one command each; the script does all the work |
| `analyzing-text` | low | one command; the numbers come from the script |
| `analyzing-csv`, `analyzing-excel` | low | usually one or two commands; raise it to `medium` if your questions need several steps |
| `plotting-charts` | medium | Claude also looks at the PNG and checks it against the numbers |
| `calculating-invoices` | high | money: Claude writes the invoice JSON, and must fix every problem `validate` reports |
| `calculating-dates` | high | the question often needs checking how the script counts (Step 26) |

**What the effort does not change:** the Python interpreter, its packages, and the script's result.
The script runs the same and costs no tokens. Effort only changes how much Claude thinks around it.

### Step 28 - Where the tokens of a skill run go

**What:** `tools\run_cost.py` runs one prompt with `claude -p`, and prints each step with its model,
and the tokens per model.

**Why:** to see how big the thinking part is compared with the rest, before you expect savings.

**Run:** (uses a little allowance)

```bat
python tools/run_cost.py "Convert 26.2 miles to kilometers." --model sonnet
```

**Expected result** (a real run with Sonnet, made before the skill got its `effort: low` line):

```text
Steps:
  1. claude-sonnet-5-5  thinks
  2. claude-sonnet-5-5  Skill converting-units
  3. claude-sonnet-5-5  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/converting-units/sc
  4. claude-sonnet-5-5  writes the answer

Tokens per model:
  claude-sonnet-5-5: context re-read 110,413, new context 10,929, output 269 (thinking 31), cost≈$0.0575
```

**How to read it:**

| Part | Meaning |
|---|---|
| `context re-read 110,413` | at **every** step, Claude reads its whole context again: Claude Code's instructions, the tool and skill lists, your question, and the results so far. That is about 27,000 tokens per step. Re-reading from the cache is cheaper than new text, but it still counts |
| `new context 10,929` | text that entered the context for the first time, like the skill's instructions and the script's output |
| `output 269 (thinking 31)` | what Claude wrote, including its thinking |

**The lesson:** for a one-command skill, thinking is a small part of the tokens, so `effort: low`
saves only a little there. On a skill where Claude thinks more, `low` used 11% to 44% less thinking
than `high` in real runs (Step 26). Fewer steps
save tokens too. Let the script do the whole job in one command, and write the SKILL.md so Claude
needs only that one command.

**The same with the SDK:** add `--sdk`. `run_cost.py` then makes the same run with `query()`. Two
options make it the same run as `claude -p`. The first is `system_prompt={"type": "preset", "preset": "claude_code"}`:
Claude Code's own instructions (without it, the SDK sends none, Step 2). The second is
`setting_sources=["user", "project", "local"]`: the settings files that `claude -p` reads. A real run with
Sonnet, the same day as a `claude -p` run:

```text
Steps:
  1. claude-sonnet-5-5  thinks
  2. claude-sonnet-5-5  Skill converting-units
  3. claude-sonnet-5-5  Bash: python "E:/may10/claudecodecli_and_python/.claude/skills/converting-units/sc
  4. claude-sonnet-5-5  writes the answer

Tokens per model:
  claude-sonnet-5-5: context re-read 51,514, new context 27,063, output 243 (thinking 31), cost≈$0.1158
```

It shows the same four steps, and almost the same output (243 against 226 tokens with `claude -p` that
day). The context numbers differ, for two reasons. The SDK starts its own `claude.exe` from the pip
package (Step 2). Here that was Claude Code 2.1.301, against 2.1.308 for the `claude` command, with
slightly different built-in instructions. And its cache was cold, so more text was written to the cache ("new context":
27,063 against 13,634) and less read from it (51,514 against 106,979).

**If you also want a cheaper model:** a skill can set `model: haiku` next to `effort:`. In real
`claude -p` runs, it was used only when you started the skill yourself (`/converting-units 26.2 mi km`:
Haiku, $0.0029 instead of $0.0575). When Claude chose the skill, the run stayed on the session model.
Check it in your window with Ctrl+O, which shows the model of each answer.

## Beyond your own computer (optional)

- Your skill folders also work on claude.ai (upload them there) and with the Claude API (which needs
  an API key). Only 6 frontmatter fields are allowed there (Lesson 4, Step 7).
- "Managed Agents" is an Anthropic service that runs agents on Anthropic's computers. It needs an API
  key. You don't need it for this course.

**Next:** [Lesson 7 - Skills that need pip packages](07-skills-with-pip-packages.md)
