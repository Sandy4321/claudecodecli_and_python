"""Shared helpers for the tools in this folder: find the skills, read SKILL.md, and split text into words.

WHAT
    - Skill: one skill, with its folder, its frontmatter (the settings between the --- lines), its
      body (the instructions), and three properties: name (the folder name if there is no name: line),
      description (with when_to_use added, as Claude Code shows it), and model_invocable (False when
      disable-model-invocation: true).
    - parse_skill_file(path) reads one SKILL.md; load_skills(folder) reads every
      <folder>/<skill>/SKILL.md. A broken file gets a parse_error instead of stopping the program.
    - tokens(text): the content words of a text, lowercase, without common words, with simple endings
      cut ("dates" -> "date"). "tax/VAT" counts as "tax/vat", "tax" and "vat".
    - positive_description(text): the description without its last "Not for ..." sentence.

WHY
    skills_lint.py, skill_sizes.py and route_preview.py need the same reading code; keeping it in one
    place keeps them consistent. positive_description() is why every description in this project ends
    with its "Not for ..." sentence: a word counter can't read "not", so that sentence must be easy to
    cut off.

HOW IT WORKS
    The frontmatter is read with PyYAML if it is installed, otherwise with a small reader for the
    simple "key: value" and "- item" lines used here.

HOW TO USE
    Not run on its own. The tools import it:
        from skilllib import load_skills
        for skill in load_skills():
            print(skill.name, len(skill.description))

WHICH WAY TO REACH CLAUDE
    None: it never calls Claude.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k skilllib
       Expected (1 test; the time differs):
           .
           ----------------------------------------------------------------------
           Ran 1 test in 0.008s

           OK
       What it checks: that the Not for sentence is cut off, and how text is split into words. Every
       test of the tools that use it (-k TutorialTools) checks it too. Add -v to see the name of each
       test.
    2. By hand: free.
           cd tools
           python -c "from skilllib import load_skills; print([s.name for s in load_skills() if s.model_invocable])"
               ['analyzing-csv', 'analyzing-excel', 'analyzing-text', 'calculating-dates', 'calculating-invoices', 'converting-units', 'plotting-charts', 'tracking-todos']
           cd ..
               (8 names: clear-todos is missing, because only you can start it)

IF SOMETHING GOES WRONG
    - A skill gets a parse_error: its SKILL.md must start on line 1 with ---, and end the settings with ---.

FILES IT READS AND WRITES
    Reads SKILL.md files. Writes nothing.

SEE ALSO
    skills_lint.py, skill_sizes.py, route_preview.py (use it).
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"

try:
    import yaml  # PyYAML, if installed
except ImportError:  # pragma: no cover - fallback is exercised only without PyYAML
    yaml = None


@dataclass
class Skill:
    dir: Path
    path: Path
    frontmatter: dict = field(default_factory=dict)
    body: str = ""
    parse_error: str | None = None

    @property
    def name(self) -> str:
        return str(self.frontmatter.get("name") or self.dir.name)

    @property
    def description(self) -> str:
        text = str(self.frontmatter.get("description") or "")
        extra = self.frontmatter.get("when_to_use")
        return f"{text} {extra}".strip() if extra else text

    @property
    def model_invocable(self) -> bool:
        return not _truthy(self.frontmatter.get("disable-model-invocation", False))


def _truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "yes", "on", "1")


def _minimal_yaml(text: str) -> dict:
    """Tiny fallback parser: `key: value` lines and `- item` lists. Enough for these skills."""
    data, current = {}, None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")) and line.strip().startswith("- ") and current:
            data.setdefault(current, [])
            if isinstance(data[current], list):
                data[current].append(line.strip()[2:].strip().strip("\"'"))
            continue
        key, _, value = line.partition(":")
        current = key.strip()
        data[current] = value.strip().strip("\"'") if value.strip() else []
    return data


def parse_skill_file(path: Path) -> Skill:
    text = path.read_text(encoding="utf-8")
    skill = Skill(dir=path.parent, path=path)
    if not text.startswith("---"):
        skill.parse_error = "Frontmatter must start with '---' on the very first line."
        skill.body = text
        return skill
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.DOTALL)
    if not match:
        skill.parse_error = "Frontmatter has no closing '---' line."
        skill.body = text
        return skill
    raw, skill.body = match.group(1), match.group(2)
    try:
        loaded = yaml.safe_load(raw) if yaml else _minimal_yaml(raw)
        skill.frontmatter = loaded if isinstance(loaded, dict) else {}
    except Exception as err:  # yaml.YAMLError, but keep the fallback path simple
        skill.parse_error = f"Invalid YAML: {err}"
    return skill


def load_skills(skills_dir: Path = DEFAULT_SKILLS_DIR) -> list[Skill]:
    return [parse_skill_file(p) for p in sorted(Path(skills_dir).glob("*/SKILL.md"))]


STOP_WORDS = set(
    """a an and are as at be by can do does for from has have how i if in into is it its me my of on
    or the this to use used user uses when with what which who you your asks about not than that these
    those there their them then than via per like such any all one two very""".split()
)


def _stem(word: str) -> str:
    if len(word) <= 4:
        return word
    if word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith(("ches", "shes", "xes", "sses")):
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    if word.endswith("ing") and len(word) > 5:
        return word[:-3]
    if word.endswith("ed") and len(word) > 5:
        return word[:-2]
    return word


def tokens(text: str) -> list[str]:
    """Lowercase content words with a light stemmer (good enough for a preview).

    Compound tokens such as "km/h" or "sales.csv" are kept whole AND split into
    their parts, so "tax/VAT" matches both "tax" and "vat".
    """
    out = []
    for raw in re.findall(r"[a-z0-9]+(?:[/.][a-z0-9]+)*", text.lower()):
        parts = [raw] + re.split(r"[/.]", raw) if re.search(r"[/.]", raw) else [raw]
        for w in parts:
            if w and w not in STOP_WORDS and len(w) >= 2:
                out.append(_stem(w))
    return out


# Convention in this repo: the "Not for X (use Y)" boundary is the LAST sentence of a description.
NEGATIVE_CLAUSE_RE = re.compile(r"\b(?:Not for|Do not use|Don't use)\b.*$", re.IGNORECASE | re.DOTALL)


def positive_description(text: str) -> str:
    """Drop the trailing 'Not for X (use Y)' clause. A word counter can't read negation; Claude can."""
    return NEGATIVE_CLAUSE_RE.sub("", text).strip()
