# Cheat sheet

**Start:** the venv's `activate.bat`, `cd /d E:\may10\claudecodecli_and_python`, `claude`. `set ANTHROPIC`: no API key.

| In a `SKILL.md` | What it does |
|---|---|
| `description:` "Does X. Use when ... Not for Y (use Z)." | level 1: always in context; Claude chooses by it |
| the body: `python "${CLAUDE_SKILL_DIR}/scripts/x.py"` | level 2: read only when the skill is chosen |
| `scripts/*.py`: JSON out; on errors a hint, exit code 1 | level 3: run, never read, so free in context |
| `allowed-tools: Bash(python *)` | its commands run without a permission prompt |
| `disable-model-invocation: true` | only you can start it, with `/name` |
| `effort: low` / `context: fork` with `model: haiku` | its own effort / its own subagent and model |
| `$ARGUMENTS`, `$0`, `$1` | all words after `/name`, the first word, the second word |

| Job | `claude -p` | Agent SDK |
|---|---|---|
| one answer, as JSON | `--output-format json` | `query()`, then `ResultMessage` |
| each step as it happens | `--output-format stream-json --verbose` | each message as a Python object |
| model and effort | `--model haiku --effort low` | `model="haiku"`, `effort="low"` |
| no permission prompts | `--allowedTools "Skill,Bash(python *)"` | `allowed_tools=[...]` |
| a plain LLM call | `--system-prompt "..." --tools ""` | `system_prompt="..."`, `tools=[]` |
| `max_tokens` | `set CLAUDE_CODE_MAX_OUTPUT_TOKENS=4096` | `env={...}` with the same variable |
| follow-up questions | `--resume <session_id>`, new process | `ClaudeSDKClient`, one process, fast |
| your rule on each tool call | a hook script, `--settings` | `HookMatcher` with a function |
| your functions as tools | an MCP server, `--mcp-config` | `@tool`, `create_sdk_mcp_server` |
| **better for** | no install, `.bat`, schedulers, pipes | chats, rules with program state, own tools |

| Effort: which setting wins | |
|---|---|
| 1. `set CLAUDE_CODE_EFFORT_LEVEL=...` | beats everything, also the skills' lines |
| 2. a skill's `effort:` | for the requests while the skill works |
| 3. `--effort`, `/effort`, `effortLevel` | the session; without them, the model's default |

| Check and see | Command |
|---|---|
| SKILL.md mistakes (free) | `python tools/skills_lint.py` |
| scripts and programs (free) | `python -m unittest discover -s tests` (74 tests) |
| Claude's real skill choice | `python tools/routing_eval.py --limit 4 --model haiku` |
| size, cost and effort of a run | `tools/skill_sizes.py`, `tools/run_cost.py`, `agent/effort_probe.py` |
| thinking and every command | **Ctrl+O** in claude; `"showThinkingSummaries": true` in settings |

| Problem | Fix |
|---|---|
| "pandas is not installed", exit code 2 | activate the venv, then start claude again |
| the wrong skill, or none | sharpen "Use when" and "Not for"; run the routing test |
| Claude computes by itself | start the skill with `/name`, or use a stronger model |
