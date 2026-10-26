"""Shows which claude.exe the Agent SDK starts for agent/run_agent.py, and with which options (Lesson 6, Step 2).

WHAT
    Prints the program the SDK would start (the claude.exe that comes with the claude-agent-sdk
    package), the folder it would run in, and its command-line options, one per line.

WHY
    To see that the Agent SDK is not a separate engine. It starts Claude Code (claude.exe) and talks
    to it, so your Pro login, your skills and your settings work the same way. Each option in
    ClaudeAgentOptions becomes a command-line option you know from claude -p: model= becomes
    --model, allowed_tools= becomes --allowedTools, max_turns= becomes --max-turns, and
    setting_sources= becomes --setting-sources. Your question is not in the command: the SDK sends
    it as a JSON line on the program's input (stdin).

HOW IT WORKS
    It builds the options with run_agent.build_options(), and asks the SDK's own transport class to
    build the command. It starts nothing, so it costs nothing. It uses private SDK functions
    (their names start with _), which can change in a future SDK version.

HOW TO RUN  (in cmd, from the project folder, with the venv activated)
    python tools/show_sdk_command.py
    python tools/show_sdk_command.py --model haiku

OPTIONS
    --model NAME     the same --model option as run_agent.py, to see where it goes in the command

NEEDS
    claude-agent-sdk in the Python that runs it (python -m pip install -r agent/requirements.txt).

WHICH WAY TO REACH CLAUDE
    None: it shows the SDK's command, but runs nothing.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k show_sdk_command
       Expected (1 test; the time differs):
           .
           ----------------------------------------------------------------------
           Ran 1 test in 2.519s

           OK
       What it checks: that it prints the bundled claude.exe and the flags of run_agent.py's options
       (skipped where the SDK is not installed). Add -v to see the name of each test.
    2. By hand: free.
           python tools/show_sdk_command.py
               The SDK would start this program:
                   C:/pyenvsmy/claudeclioct26/Lib/site-packages/claude_agent_sdk/_bundled/claude.exe
               in this folder (cwd):
                   E:/may10/claudecodecli_and_python
               with these options:
                   --output-format
                   stream-json
                   --verbose
                   --system-prompt
                                               (an empty line: the empty system prompt)
                   --allowedTools
                   Skill,Read,Bash(python *),PowerShell(python *)
                   --max-turns
                   15
                   --setting-sources=project
                   --input-format
                   stream-json

IF SOMETHING GOES WRONG
    - Exit code 2 and "claude-agent-sdk is not installed in this Python": install it in the venv.
    - AttributeError after an SDK update: the private SDK functions it uses changed (this was written for
      claude-agent-sdk 0.2.168).

FILES IT READS AND WRITES
    None.

SEE ALSO
    agent/run_agent.py (build_options and build_cli_command); Lesson 6, Step 2.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))

try:
    from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport
except ImportError:
    print("claude-agent-sdk is not installed in this Python. Run: python -m pip install -r agent\\requirements.txt")
    sys.exit(2)

import run_agent  # noqa: E402  (agent/run_agent.py, found through the sys.path line above)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", help="the same --model option as run_agent.py")
    args = parser.parse_args()

    options = run_agent.build_options("all", args.model)
    transport = SubprocessCLITransport(prompt="(your question is sent separately, as JSON on stdin)", options=options)
    # Private SDK functions: fine for looking, may change in future SDK versions.
    transport._cli_path = transport._find_cli()
    print("The SDK would start this program:")
    print(f"    {transport._cli_path}")
    print(f"in this folder (cwd):\n    {options.cwd}")
    print("with these options:")
    for part in transport._build_command()[1:]:
        print(f"    {part}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
