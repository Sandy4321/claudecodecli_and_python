"""Checks every SKILL.md in a skills folder for mistakes, without Claude (Lesson 2, Step 4; Lesson 5, Test 2).

WHAT
    Prints the problems of each skill (ERROR, WARN or INFO), then the pairs of skills whose
    descriptions share many words. It checks:
      - name: present, at most 64 characters, lowercase-with-hyphens, no "anthropic" or "claude",
        the same as the folder name;
      - description: present; at most 1024 characters (the limit of claude.ai and the API), and an
        ERROR above 1536 (Claude Code cuts it there); no XML tags; third person ("Converts ...",
        not "I can ..."); a "Use when ..." sentence, so Claude knows when to choose it;
      - the body: under 500 lines; "${CLAUDE_SKILL_DIR}/..." in quotes; $0, $1, ... that will be
        replaced by the words typed after /skill-name (write a backslash before $ for a real dollar);
      - files: every linked or ${CLAUDE_SKILL_DIR} file exists; paths use forward slashes; a pinned
        python.exe exists; every .py file in the skill compiles;
      - overlap: two descriptions with more than 30% of their words in common may compete.

WHY
    A wrong SKILL.md often fails silently: the skill is never chosen, or a path breaks only on a folder
    with a space. These checks are free and instant. Run them after every change to a skill.

HOW IT WORKS
    skilllib.load_skills() reads the skills. Each check is a rule in check_skill(). The overlap is the
    Jaccard score: shared words divided by all words of the two descriptions, without the "Not for ..."
    sentences.

HOW TO RUN  (in cmd, from the project folder)
    python tools/skills_lint.py                     (checks .claude/skills)
    python tools/skills_lint.py tools/demo_bad_skills  (a folder of broken skills, to see every message)

OUTPUT AND EXIT CODE
    One block per skill, then the overlap list, and at the end "9 skills, 0 error(s)."
    Exit code 1 if any ERROR was found, otherwise 0. WARN and INFO lines are advice.

WHICH WAY TO REACH CLAUDE
    None: it never calls Claude, and costs nothing.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k lint -k demo_bad_skills
       Expected (3 tests; the time differs):
           ...
           ----------------------------------------------------------------------
           Ran 3 tests in 0.234s

           OK
       What they check: that the project's skills pass, that a bad SKILL.md gets every expected message,
       and the result for tools/demo_bad_skills. Add -v to see the name of each test.
    2. By hand: free.
           python tools/skills_lint.py | findstr /c:"error(s)"
               9 skills, 0 error(s).
           python tools/skills_lint.py tools/demo_bad_skills | findstr /c:"error(s)"
               4 skills, 3 error(s).          (exit code 1: echo %errorlevel% after the command without findstr)

IF SOMETHING GOES WRONG
    - "Pinned interpreter not found on this machine": the SKILL.md names a python.exe that doesn't exist
      here (Lesson 7, "Another way").
    - WARN about an overlap: two descriptions share many words; make each one's words more distinct.

FILES IT READS AND WRITES
    Reads the skills folder (it compiles each .py file in memory, and writes nothing).

SEE ALSO
    skilllib.py; tools/demo_bad_skills; Lesson 2, Step 4; Lesson 5, Test 2.
"""

import itertools
import re
import sys
from pathlib import Path

from skilllib import DEFAULT_SKILLS_DIR, load_skills, positive_description, tokens

# Limits from the Agent Skills spec (portable to claude.ai and the API).
NAME_MAX = 64
DESCRIPTION_MAX_PORTABLE = 1024
# Claude Code truncates description + when_to_use at this length in the skill listing.
DESCRIPTION_MAX_CLAUDE_CODE = 1536
BODY_MAX_LINES = 500
# Jaccard similarity of description words above which two skills may compete.
OVERLAP_WARN = 0.30

PORTABLE_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def check_skill(skill) -> list[tuple[str, str]]:
    issues = []
    err = lambda msg: issues.append(("ERROR", msg))
    warn = lambda msg: issues.append(("WARN", msg))
    info = lambda msg: issues.append(("INFO", msg))

    if skill.parse_error:
        err(skill.parse_error)
        return issues

    fm = skill.frontmatter
    name = str(fm.get("name", ""))
    if not name:
        warn("No 'name' field; the folder name is used.")
    else:
        if len(name) > NAME_MAX:
            err(f"name is {len(name)} chars (max {NAME_MAX}).")
        if not NAME_RE.match(name):
            err("name must be lowercase letters, digits and single hyphens.")
        if "anthropic" in name or "claude" in name:
            err("name must not contain the reserved words 'anthropic' or 'claude'.")
        if name != skill.dir.name:
            warn(f"name '{name}' differs from folder '{skill.dir.name}' (both will work as /commands; confusing).")

    description = str(fm.get("description", "")).strip()
    if not description:
        err("description is missing - Claude cannot match requests to this skill.")
    else:
        if len(description) > DESCRIPTION_MAX_CLAUDE_CODE:
            err(f"description is {len(description)} chars; Claude Code cuts it at {DESCRIPTION_MAX_CLAUDE_CODE}.")
        elif len(description) > DESCRIPTION_MAX_PORTABLE:
            warn(f"description is {len(description)} chars; claude.ai/API reject more than {DESCRIPTION_MAX_PORTABLE}.")
        if re.search(r"<[^>]+>", description):
            err("description must not contain XML tags.")
        if re.search(r"\b(I can|I will|you can|we can|let me)\b", description, re.IGNORECASE):
            warn("Write the description in third person ('Converts...'), not 'I can' / 'you can'.")
        if skill.model_invocable and not re.search(r"\b(use when|use for|use if|when the user)\b", description, re.IGNORECASE):
            warn("Add a trigger clause such as 'Use when the user asks ...' so Claude knows WHEN to pick it.")

    extra_keys = sorted(set(fm) - PORTABLE_KEYS)
    if extra_keys:
        info(f"Claude Code-only keys {extra_keys} (fine here; remove before uploading to claude.ai/API).")

    body_lines = skill.body.count("\n") + 1
    if body_lines > BODY_MAX_LINES:
        warn(f"Body is {body_lines} lines; keep SKILL.md under {BODY_MAX_LINES} and move details to reference files.")

    for match in re.finditer(r"\$\{CLAUDE_SKILL_DIR\}", skill.body):
        before = skill.body[max(0, match.start() - 1) : match.start()]
        if before != '"':
            line = skill.body[: match.start()].count("\n") + 1
            warn(f"Body line {line}: quote the path - \"${{CLAUDE_SKILL_DIR}}/...\" - it may contain spaces.")
            break

    for match in re.finditer(r"(?<![\\$])\$(\d+)", skill.body):
        line = skill.body[: match.start()].count("\n") + 1
        number = int(match.group(1))
        # Placeholders count from $0: $0 is the first word typed after /skill-name, $5 the sixth.
        warn(f"Body line {line}: '${number}' is replaced by word {number + 1} typed after the skill name "
             f"($0 is the first). Write \\${number} for a literal dollar sign.")

    referenced = set(re.findall(r"\$\{CLAUDE_SKILL_DIR\}/([^\s\"'`)]+)", skill.body))
    referenced |= {link for link in re.findall(r"\]\(([^)#\s]+)\)", skill.body) if "://" not in link}
    for rel in sorted(referenced):
        if not (skill.dir / rel).resolve().exists():
            err(f"Referenced file does not exist: {rel}")
        if "\\" in rel:
            warn(f"Use forward slashes in paths: {rel}")

    # Skills that need pip packages pin an interpreter (a venv's python.exe). It is machine-specific,
    # so check that it exists here.
    allowed = " ".join(map(str, fm.get("allowed-tools") or [])) if isinstance(fm.get("allowed-tools"), list) else str(fm.get("allowed-tools", ""))
    pinned = set(re.findall(r"(?<![\w$])([A-Za-z]:[/\\][^\s\"'`*)]*?python(?:3(?:\.\d+)?)?(?:\.exe)?)(?=[\s\"'`*)]|$)", skill.body + " " + allowed))
    for interpreter in sorted(pinned):
        if Path(interpreter).exists():
            info(f"Pinned interpreter: {interpreter}")
        else:
            warn(f"Pinned interpreter not found on this machine: {interpreter} (create the venv or edit SKILL.md).")

    for script in sorted(skill.dir.rglob("*.py")):
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except SyntaxError as error:
            err(f"{script.relative_to(skill.dir)} line {error.lineno}: {error.msg}")

    return issues


def overlaps(skills) -> list[tuple[float, str, str, list[str]]]:
    words = {
        s.name: set(tokens(positive_description(s.description)))
        for s in skills
        if s.model_invocable and s.description
    }
    found = []
    for a, b in itertools.combinations(sorted(words), 2):
        union = words[a] | words[b]
        if not union:
            continue
        score = len(words[a] & words[b]) / len(union)
        if score >= OVERLAP_WARN:
            found.append((score, a, b, sorted(words[a] & words[b])))
    return sorted(found, reverse=True)


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    skills_dir = Path(argv[0]) if argv else DEFAULT_SKILLS_DIR
    skills = load_skills(skills_dir)
    if not skills:
        print(f"No */SKILL.md found under {skills_dir}")
        return 1

    errors = 0
    for skill in skills:
        issues = check_skill(skill)
        mode = "auto + /command" if skill.model_invocable else "/command only"
        status = "ok" if not any(level != "INFO" for level, _ in issues) else "check"
        print(f"\n[{status}] {skill.name}  ({mode}, description {len(skill.description)} chars)")
        for level, message in issues:
            print(f"   {level:5} {message}")
            errors += level == "ERROR"

    pairs = overlaps(skills)
    print("\nDescription overlap (pairs that may compete for the same request):")
    if not pairs:
        print(f"   none above {OVERLAP_WARN:.2f} - descriptions are well separated")
    for score, a, b, shared in pairs:
        print(f"   WARN  {a} <-> {b}: {score:.2f} shared words {shared}")

    print(f"\n{len(skills)} skills, {errors} error(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
