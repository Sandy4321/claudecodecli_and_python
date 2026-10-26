"""The rules of guarded_agent.py, as plain Python without the SDK (Lesson 6, Part 4, Step 15).

WHAT
    Guard.check(tool_name, tool_input) decides about one planned tool call, and returns
    (allowed, reason):
      - Bash and PowerShell: only `python <a script in .claude/skills/> ...`, with no other command
        chained to it (; & | < > or a backtick), and at most MAX_COMMANDS (6) times per run;
      - Write and Edit: only files inside data/;
      - Read, Glob, Grep and Skill: allowed, they only read;
      - every other tool: refused.
    The reason is a sentence Claude can act on, for example "files may only be written inside data/".

WHY
    Kept apart from guarded_agent.py, so the rules can be tested without Claude and without the SDK:
    the AgentGuard tests in tests/test_skill_scripts.py check them.

HOW IT WORKS
    inside(path, folder) resolves a path, relative to the project or absolute, and checks that it lies
    in the folder. PYTHON_SCRIPT_RE finds the script after `python`; CHAINING_RE finds characters
    that would add a second command. The Guard object counts the allowed commands.

HOW TO USE
    Not run on its own. guarded_agent.py imports it; to try the rules by hand:
        cd agent
        python -c "from guard import Guard; print(Guard().check('Write', {'file_path': 'report.txt'}))"
    It prints (False, 'files may only be written inside data/, not report.txt').

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k AgentGuard
       Expected (5 tests; the time differs):
           .....
           ----------------------------------------------------------------------
           Ran 5 tests in 0.010s

           OK
       What they check: skill scripts allowed, other commands and chained commands denied, writes only
       inside data/, the command limit, and reading tools allowed. Add -v to see the name of each test.
    2. By hand: free.
           cd agent
           python -c "from guard import Guard; g = Guard(); print(g.check('Bash', {'command': 'python .claude/skills/converting-units/scripts/convert.py units'})); print(g.check('Bash', {'command': 'del data/sales.csv'}))"
               (True, 'skill script, command 1 of 6')
               (False, 'only python commands that run a skill script are allowed; use a skill')
           cd ..

IF SOMETHING GOES WRONG
    - A skill command is denied: it must start with python, and the script must be inside .claude/skills.
    - ; & | < > or a backtick after the script are denied on purpose: they would add a second command.

FILES IT READS AND WRITES
    None.

SEE ALSO
    guarded_agent.py and guard_hook.py (use these rules); class AgentGuard; Lesson 6, Step 15.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"
DATA_DIR = PROJECT_ROOT / "data"
MAX_COMMANDS = 6

SHELL_TOOLS = {"Bash", "PowerShell"}
WRITE_TOOLS = {"Write", "Edit"}
READ_TOOLS = {"Read", "Glob", "Grep", "Skill"}
# `python "<script>" ...` or `python <script> ...`, optionally started with PowerShell's call operator &.
PYTHON_SCRIPT_RE = re.compile(r'^\s*(?:&\s*)?python(?:\.exe)?\s+(?:"([^"]+)"|(\S+))', re.IGNORECASE)
# Characters that chain a second command or redirect output: python skill.py ; del x
CHAINING_RE = re.compile(r"[;&|<>`]")


def inside(path: str, folder: Path) -> bool:
    """True if path (absolute, or relative to the project) is inside folder."""
    target = Path(path)
    if not target.is_absolute():
        target = PROJECT_ROOT / target
    try:
        target.resolve().relative_to(folder.resolve())
        return True
    except ValueError:
        return False


class Guard:
    def __init__(self, max_commands: int = MAX_COMMANDS):
        self.max_commands = max_commands
        self.commands_run = 0

    def check(self, tool_name: str, tool_input: dict) -> tuple[bool, str]:
        if tool_name in READ_TOOLS:
            return True, "reading is allowed"
        if tool_name in WRITE_TOOLS:
            path = tool_input.get("file_path", "")
            if inside(path, DATA_DIR):
                return True, "writing inside data/ is allowed"
            return False, f"files may only be written inside data/, not {path}"
        if tool_name in SHELL_TOOLS:
            return self._check_command(tool_input.get("command", ""))
        return False, f"the {tool_name} tool is not needed by this agent"

    def _check_command(self, command: str) -> tuple[bool, str]:
        match = PYTHON_SCRIPT_RE.match(command)
        if not match:
            return False, "only python commands that run a skill script are allowed; use a skill"
        script = match.group(1) or match.group(2)
        if script.startswith("-"):
            return False, f"python {script} is not allowed; run a skill script"
        if not inside(script, SKILLS_DIR):
            return False, f"{script} is not a skill script in .claude/skills/"
        rest = command[match.end():]
        if CHAINING_RE.search(rest):
            return False, "run the skill script alone, without ; & | < > or `"
        if self.commands_run >= self.max_commands:
            return False, f"the limit of {self.max_commands} commands for this run is used up"
        self.commands_run += 1
        return True, f"skill script, command {self.commands_run} of {self.max_commands}"
