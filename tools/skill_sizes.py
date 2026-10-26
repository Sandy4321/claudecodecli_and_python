"""Shows the three loading levels of every skill as numbers (Lesson 1, Step 5).

WHAT
    One row per skill: who can start it, the size of its description (level 1), the lines of its
    SKILL.md instructions (level 2), and its extra files with their lines (level 3). At the end: the
    total size of all descriptions, in characters and about how many tokens.

WHY
    To see what each skill costs. Level 1 is in EVERY request, so short descriptions matter. Level 2
    is added only when Claude chooses the skill. Level 3 scripts never enter the context: Claude runs
    them and reads only what they print. A skill can have a large, well-commented script for free.

HOW IT WORKS
    skilllib.load_skills() reads each SKILL.md. The description of a skill that only you can start
    (disable-model-invocation: true) is not in Claude's list, so it is not added to the total.
    About 4 characters of English text make one token. __pycache__ folders are skipped: they hold
    compiled .pyc files that Python writes, and are not part of the skill.

HOW TO RUN  (in cmd, from the project folder)
    python tools/skill_sizes.py
    python tools/skill_sizes.py path/to/skills          (any other skills folder)

OUTPUT  (one row)
    converting-units       Claude or you     334 chars       31 lines   scripts/convert.py (222 lines)

WHICH WAY TO REACH CLAUDE
    None: it never calls Claude, and costs nothing.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k skill_sizes
       Expected (2 tests; the time differs):
           ..
           ----------------------------------------------------------------------
           Ran 2 tests in 0.363s

           OK
       What they check: that it reports the levels of every skill, and skips compiled __pycache__ files.
       Add -v to see the name of each test.
    2. By hand: free.
           python tools/skill_sizes.py | findstr /c:"Level 1 total"
               Level 1 total (in EVERY request): 2,672 characters, about 668 tokens.

IF SOMETHING GOES WRONG
    - A skill is missing from the table: its file must be <folder>/<skill name>/SKILL.md.

FILES IT READS AND WRITES
    Reads the skills folder. Writes nothing.

SEE ALSO
    skilllib.py; Lesson 1, Step 5; Lesson 4, Step 3.
"""

import sys
from pathlib import Path

from skilllib import DEFAULT_SKILLS_DIR, load_skills

# A token is roughly 4 characters of English text. Good enough for a size comparison.
CHARS_PER_TOKEN = 4


def lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8", errors="replace").splitlines())


def extra_files(skill_dir: Path) -> list[Path]:
    """Files besides SKILL.md. Skips __pycache__ folders: Python writes compiled .pyc files there
    when a script imports another one, and they are not part of the skill."""
    return [p for p in sorted(skill_dir.rglob("*"))
            if p.is_file() and p.name != "SKILL.md" and "__pycache__" not in p.parts]


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    args = sys.argv[1:] if argv is None else argv
    skills = load_skills(Path(args[0]) if args else DEFAULT_SKILLS_DIR)
    print(f"{'skill':22} {'who starts it':14} {'level 1':>12} {'level 2':>14}   level 3")
    print(f"{'':22} {'':14} {'description':>12} {'instructions':>14}   extra files (scripts are run, not read)")
    print("-" * 100)
    always = 0
    for s in skills:
        who = "Claude or you" if s.model_invocable else "only you"
        desc = len(s.description)
        if s.model_invocable:
            always += desc
        body = len(s.body.splitlines())
        extras = extra_files(s.dir)
        extra_text = ", ".join(f"{p.relative_to(s.dir).as_posix()} ({lines(p)} lines)" for p in extras) or "-"
        print(f"{s.name:22} {who:14} {desc:>6} chars {body:>8} lines   {extra_text}")
    print("-" * 100)
    print(f"Level 1 total (in EVERY request): {always:,} characters, about {always // CHARS_PER_TOKEN:,} tokens.")
    print("Level 2 is added only for the skill Claude chooses. Level 3 scripts never enter the context:")
    print("Claude runs them and reads only what they print.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
