"""Unit tests for every skill script and tutorial tool. No Claude calls, no cost (Lesson 5, Test 1).

WHAT
    74 tests in 13 groups. Each group is a class, and its name is the word to use with -k:
        ConvertingUnits, AnalyzingCsv, CalculatingDates, AnalyzingText, CalculatingInvoices,
        TrackingTodos     the scripts of the standard-library skills;
        PackageSkills     excel_tool.py, chart.py and tools/make_sample_xlsx.py (need pandas,
                          openpyxl and matplotlib);
        WrongInterpreter  the helpful message when the venv is not active;
        TutorialTools     the tools in tools/: linter, preview, skill sizes, skilllib, the hook of
                          Lesson 9, show_sdk_command.py;
        CalculatingMath   examples/skills/calculating-math/scripts/calc.py (Lesson 8);
        AgentGuard        the rules of agent/guard.py (Lesson 6, Part 4);
        AskClaudeCommand  the claude -p command of agent/ask_claude.py, and tools/run_cost.py;
        BothWays          the other way of each agent program and tool (--cli or --sdk), and a test
                          that proves the --cli ways work with every SDK import blocked.
    Each test's name starts with the file it tests where a group covers several files, so -k with a
    file name picks that file's tests: -k guard_hook, -k run_agent. Every .py file's HOW TO TEST
    section names its own -k words.

WHY
    Claude trusts what a script prints. If the script computes wrong, Claude answers wrong, with
    confidence. These tests check the Python part of each skill, fast and for free, after every change.
    Whether Claude chooses the right skill is tested by tools/routing_eval.py instead.

HOW IT WORKS
    Two ways to test a script:
      - load() imports the script as a module, and a test calls its functions directly;
      - cli() runs the script as a separate program, exactly as Claude does, and reads the JSON it
        prints, with its exit code.
    Tests that write files use a temporary folder, never your data/todos.json. The PackageSkills tests
    are skipped (not failed) when pandas, openpyxl or matplotlib is missing.

HOW TO RUN  (in cmd, from the project folder)
    python -m unittest discover -s tests                            (all tests, with the venv: OK)
    python -m unittest discover -s tests -v                         (one line per test)
    python -m unittest discover -s tests -k ConvertingUnits -v      (one group)
    C:/Python312/python.exe -m unittest discover -s tests           (the system Python: OK (skipped=6))

WHICH WAY TO REACH CLAUDE
    None: the tests never call Claude. The tests of ask_claude.py check the command it would run.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests
       Expected (74 tests; the time differs):
           ..........................................................................
           ----------------------------------------------------------------------
           Ran 74 tests in 31.351s

           OK
    2. By hand: free.
           See a test fail on purpose: change one number in a script, run the tests, read the failure, and
           change it back (Lesson 5, Step 2 does this with the mile factor in convert.py).
           Run with the system Python too: C:/Python312/python.exe -m unittest discover -s tests
               The package tests are skipped there, not failed (Lesson 7, Step 9).

IF SOMETHING GOES WRONG
    - "OK (skipped=N)": tests that need the venv's packages (pandas, ...) or the Agent SDK were skipped.
      -v shows each skip with its reason.
    - ModuleNotFoundError or "Ran 0 tests": run from the project folder, with -s tests.

FILES IT READS AND WRITES
    Only temporary folders (deleted after each test). It never touches data/todos.json.

SEE ALSO
    Lesson 5, Test 1; Lesson 7, Step 9; each file's own HOW TO TEST section.
"""

import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))


def load(skill: str, filename: str):
    scripts = SKILLS / skill / "scripts"
    sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location(f"{skill}_{filename[:-3]}", scripts / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cli(skill: str, filename: str, *args: str, stdin: str | None = None, env: dict | None = None,
        python: list[str] | None = None) -> tuple[int, dict]:
    """Run a script exactly the way Claude does: as a subprocess, JSON on stdout."""
    proc = subprocess.run(
        [*(python or [sys.executable]), str(SKILLS / skill / "scripts" / filename), *args],
        cwd=ROOT, input=stdin, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, **(env or {})},
    )
    return proc.returncode, json.loads(proc.stdout)


def has_packages(*modules: str) -> bool:
    """True when the Python running the tests can import these (i.e. the skills' venv is activated)."""
    return subprocess.run([sys.executable, "-c", "import " + ", ".join(modules)], capture_output=True).returncode == 0


class ConvertingUnits(unittest.TestCase):
    convert = load("converting-units", "convert.py")

    def test_length(self):
        self.assertAlmostEqual(self.convert.convert(100, "km", "mi")["result"], 62.137119, places=5)

    def test_aliases_and_temperature(self):
        self.assertAlmostEqual(self.convert.convert(212, "Fahrenheit", "°C")["result"], 100.0)
        self.assertAlmostEqual(self.convert.convert(0, "c", "k")["result"], 273.15)

    def test_binary_data_units(self):
        self.assertEqual(self.convert.convert(3, "GiB", "bytes")["result"], 3 * 1024**3)

    def test_errors_explain_the_fix(self):
        mismatch = self.convert.convert(5, "kg", "mi")
        self.assertIn("Cannot convert mass", mismatch["error"])
        self.assertIn("lb", mismatch["hint"])
        self.assertIn("Unknown unit", self.convert.convert(1, "parsec", "m")["error"])

    def test_cli(self):
        code, out = cli("converting-units", "convert.py", "convert", "1", "mi", "km")
        self.assertEqual((code, out["result"]), (0, 1.609344))
        code, out = cli("converting-units", "convert.py", "convert", "1", "kg", "km")
        self.assertEqual(code, 1)


class AnalyzingCsv(unittest.TestCase):
    csv_tool = load("analyzing-csv", "csv_tool.py")
    sales = str(DATA / "sales.csv")

    def test_summary_types_and_missing(self):
        columns = {c["name"]: c for c in self.csv_tool.summary(self.sales)["columns"]}
        self.assertEqual(columns["amount"]["type"], "numeric")
        self.assertEqual(columns["amount"]["max"], 1200.0)
        self.assertEqual(columns["units"]["missing"], 1)
        self.assertEqual(columns["region"]["unique"], 4)

    def test_groupby_sorted_desc(self):
        groups = self.csv_tool.groupby(self.sales, "region", "amount", "sum")["groups"]
        self.assertEqual(groups[0], {"region": "North", "amount_sum": 2150.0})
        self.assertEqual([g["region"] for g in groups], ["North", "East", "West", "South"])

    def test_top(self):
        rows = self.csv_tool.top(self.sales, "amount", n=1)["rows"]
        self.assertEqual(rows[0]["amount"], "1200")
        self.assertEqual(self.csv_tool.top(self.sales, "amount", n=1, ascending=True)["rows"][0]["amount"], "150")

    def test_unknown_column_lists_valid_ones(self):
        code, out = cli("analyzing-csv", "csv_tool.py", "top", "data/sales.csv", "--column", "Amount")
        self.assertEqual(code, 1)
        self.assertIn("amount", out["columns"])


class CalculatingDates(unittest.TestCase):
    dates = load("calculating-dates", "dates.py")

    def test_business_days_skip_weekend_and_holiday(self):
        result = self.dates.add_business_days("2026-10-15", 10, "2026-10-26")
        self.assertEqual(result["result"], date(2026, 10, 30))

    def test_business_days_between(self):
        self.assertEqual(self.dates.business_days_between("2026-10-01", "2026-10-31")["business_days"], 21)

    def test_age_before_and_after_birthday(self):
        self.assertEqual(self.dates.age("1990-10-16", on="2026-10-15")["years"], 35)
        self.assertEqual(self.dates.age("1990-10-15", on="2026-10-15")["years"], 36)

    def test_fncli_calls_functions_by_name(self):
        code, out = cli("calculating-dates", "dates.py", "weekday", "--date", "2026-12-25")
        self.assertEqual((code, out["weekday"]), (0, "Friday"))
        code, listing = cli("calculating-dates", "dates.py", "--list")
        self.assertIn("add_business_days", [f["name"] for f in listing])

    def test_fncli_reports_bad_input(self):
        code, out = cli("calculating-dates", "dates.py", "add_days", "--date", "15/10/2026", "--days", "3")
        self.assertEqual(code, 1)
        self.assertIn("ISO date", out["error"])


class AnalyzingText(unittest.TestCase):
    text_stats = load("analyzing-text", "text_stats.py")

    def test_counts(self):
        result = self.text_stats.stats("One two three. Four five!\n\nSix seven eight nine?")
        self.assertEqual((result["words"], result["sentences"], result["paragraphs"]), (9, 3, 2))

    def test_heading_is_its_own_sentence(self):
        result = self.text_stats.stats("A Title\n\nFirst sentence here. Second one.")
        self.assertEqual(result["sentences"], 3)

    def test_top_words_skip_stop_words(self):
        words = dict(self.text_stats.top_words("the model and the model and the skill")["top_words"])
        self.assertEqual(words, {"model": 2, "skill": 1})

    def test_stdin(self):
        code, out = cli("analyzing-text", "text_stats.py", "stats", "-", stdin="Hello there. General Kenobi.")
        self.assertEqual((code, out["sentences"]), (0, 2))


class CalculatingInvoices(unittest.TestCase):
    invoice = load("calculating-invoices", "invoice.py")

    def test_totals_round_to_cents(self):
        data = json.loads((DATA / "invoice.json").read_text(encoding="utf-8"))
        result = self.invoice.totals(data)
        self.assertEqual(
            (result["subtotal"], result["discount"], result["tax"], result["total"]),
            ("1440.47", "144.05", "106.95", "1403.37"),
        )

    def test_validate_lists_every_problem(self):
        data = json.loads((DATA / "invoice_broken.json").read_text(encoding="utf-8"))
        problems = self.invoice.validate(data)["problems"]
        self.assertEqual(len(problems), 5)
        with self.assertRaises(ValueError):
            self.invoice.totals(data)

    def test_render_writes_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "inv.md"
            code, _ = cli("calculating-invoices", "invoice.py", "render", "data/invoice.json", "--out", str(out))
            self.assertEqual(code, 0)
            self.assertIn("**Total: 1403.37 USD**", out.read_text(encoding="utf-8"))


class TrackingTodos(unittest.TestCase):
    def test_add_list_done_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"TODO_FILE": str(Path(tmp) / "todos.json")}
            cli("tracking-todos", "todo.py", "add", "Low task", "--priority", "low", env=env)
            cli("tracking-todos", "todo.py", "add", "Late task", "--due", "2020-01-01", "--priority", "high", env=env)
            _, listing = cli("tracking-todos", "todo.py", "list", env=env)
            self.assertEqual([t["text"] for t in listing["tasks"]], ["Late task", "Low task"])
            self.assertTrue(listing["tasks"][0]["overdue"])

            cli("tracking-todos", "todo.py", "done", "2", env=env)
            _, cleared = cli("tracking-todos", "todo.py", "clear", "--done-only", env=env)
            self.assertEqual(cleared, {"removed": 1, "remaining": 1})

    def test_bad_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = cli("tracking-todos", "todo.py", "add", "x", "--priority", "urgent",
                            env={"TODO_FILE": str(Path(tmp) / "t.json")})
            self.assertEqual(code, 1)
            self.assertIn("priority must be one of", out["error"])


@unittest.skipUnless(has_packages("pandas", "openpyxl", "matplotlib"),
                     "activate the skills' venv (pandas, openpyxl, matplotlib) to run these tests")
class PackageSkills(unittest.TestCase):
    """Skills whose scripts need pip packages. Run the tests from the activated venv, like Claude Code."""

    def venv(self, skill, filename, *args):
        return cli(skill, filename, *args)

    def test_excel_sheets_and_summary(self):
        _, out = self.venv("analyzing-excel", "excel_tool.py", "sheets", "data/sales.xlsx")
        self.assertEqual([s["sheet"] for s in out["sheets"]], ["Sales", "Targets"])
        _, out = self.venv("analyzing-excel", "excel_tool.py", "summary", "data/sales.xlsx", "--sheet", "Sales")
        columns = {c["name"]: c for c in out["columns"]}
        self.assertEqual((columns["date"]["type"], columns["date"]["min"]), ("date", "2026-01-05"))
        self.assertEqual(columns["amount"]["sum"], 4630)

    def test_excel_pivot_has_totals(self):
        _, out = self.venv("analyzing-excel", "excel_tool.py", "pivot", "data/sales.xlsx", "--sheet", "Sales",
                           "--index", "region", "--columns", "product", "--values", "amount")
        rows = {r["region"]: r for r in out["rows"]}
        self.assertEqual(rows["North"]["Total"], 2150)
        self.assertEqual(rows["Total"]["Total"], 4630)

    def test_excel_unknown_sheet_lists_sheets(self):
        code, out = self.venv("analyzing-excel", "excel_tool.py", "summary", "data/sales.xlsx", "--sheet", "sales")
        self.assertEqual((code, out["sheets"]), (1, ["Sales", "Targets"]))

    def test_chart_bar_writes_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "bar.png"
            code, out = self.venv("plotting-charts", "chart.py", "bar", "data/sales.csv",
                                  "--x", "region", "--y", "amount", "--out", str(png))
            self.assertEqual(code, 0)
            self.assertEqual(png.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(out["points"][0], {"region": "North", "amount": 2150.0})

    def test_chart_line_by_month_from_xlsx(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, out = self.venv("plotting-charts", "chart.py", "line", "data/sales.xlsx", "--sheet", "Sales",
                               "--x", "date", "--y", "amount", "--freq", "M", "--out", str(Path(tmp) / "line.png"))
        self.assertEqual([p["date"] for p in out["points"]], ["2026-01", "2026-02", "2026-03", "2026-04"])
        self.assertEqual(out["points"][2]["amount"], 2260.0)


    def test_make_sample_xlsx_writes_both_sheets(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sales.xlsx"
            proc = subprocess.run([sys.executable, str(ROOT / "tools" / "make_sample_xlsx.py"), str(out)],
                                  capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            _, sheets = self.venv("analyzing-excel", "excel_tool.py", "sheets", str(out))
        self.assertEqual([(s["sheet"], s["rows"]) for s in sheets["sheets"]], [("Sales", 12), ("Targets", 4)])

class WrongInterpreter(unittest.TestCase):
    """Run with a Python that cannot see any installed packages (-S): the scripts must explain the fix."""

    def test_scripts_explain_how_to_fix_the_call(self):
        for skill, script in [("analyzing-excel", "excel_tool.py"), ("plotting-charts", "chart.py")]:
            code, out = cli(skill, script, "check", python=[sys.executable, "-S"])
            self.assertEqual(code, 2, skill)
            self.assertIn("is not installed in", out["error"])
            self.assertIn("virtual environment", out["hint"])
            self.assertIn("requirements.txt", out["hint"])


# The 9 skills of the course. The preview and "only you" tests below use only these, so the skills you add in
# Lesson 8 or keep from Lesson 9 (Exercise 4) don't change their results: an extra skill shifts the preview's
# word weights, and another manual-only skill changes the set of "only you" skills.
COURSE_SKILLS = {"converting-units", "analyzing-csv", "analyzing-text", "calculating-dates", "calculating-invoices",
                 "tracking-todos", "clear-todos", "analyzing-excel", "plotting-charts"}


def course_skills():
    from skilllib import load_skills
    return [s for s in load_skills(SKILLS) if s.name in COURSE_SKILLS]


class TutorialTools(unittest.TestCase):
    def test_lint_passes(self):
        import skills_lint

        report = io.StringIO()
        with contextlib.redirect_stdout(report):      # keep the linter's report out of the test output
            result = skills_lint.main([str(SKILLS)])
        self.assertEqual(result, 0, report.getvalue())

    def test_lint_catches_common_mistakes(self):
        import skills_lint
        from skilllib import parse_skill_file

        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "Bad_Skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\nname: Bad_Skill\ndescription: I can help with stuff\n---\n"
                "Run python ${CLAUDE_SKILL_DIR}/scripts/missing.py and charge $5.\n"
                "Or C:/no/such/venv/Scripts/python.exe \"${CLAUDE_SKILL_DIR}/x.py\".\n",
                encoding="utf-8",
            )
            messages = " ".join(m for _, m in skills_lint.check_skill(parse_skill_file(skill_dir / "SKILL.md")))
        for expected in ("lowercase", "third person", "trigger clause", "quote the path", "word 6 typed", "does not exist",
                         "Pinned interpreter not found"):
            self.assertIn(expected, messages)

    def test_route_preview_ranks_the_right_skill_first(self):
        import route_preview

        skills = course_skills()
        self.assertEqual({s.name for s in skills}, COURSE_SKILLS)          # all 9 found, and nothing else
        for prompt, expected in [
            ("convert 26.2 miles to km", "converting-units"),
            ("Which region sold the most in data/sales.csv?", "analyzing-csv"),
            ("How readable is data/article.txt?", "analyzing-text"),
            ("How many working days until Christmas?", "calculating-dates"),
        ]:
            self.assertEqual(route_preview.rank(prompt, skills)[0][1], expected, prompt)

    def test_skill_sizes_reports_levels(self):
        proc = subprocess.run([sys.executable, str(ROOT / "tools" / "skill_sizes.py")], capture_output=True,
                              text=True, encoding="utf-8", cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)   # on failure, show the script's error text
        self.assertIn("converting-units", proc.stdout)
        self.assertIn("Level 1 total (in EVERY request)", proc.stdout)

    def test_skill_sizes_ignores_compiled_python_files(self):
        # Python writes __pycache__/*.pyc files next to imported scripts. They are binary, not text.
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "demo-skill"
            (skill / "scripts" / "__pycache__").mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: demo-skill\ndescription: Demo. Use when testing.\n---\nBody\n",
                                            encoding="utf-8")
            (skill / "scripts" / "tool.py").write_text("print('hi')\n", encoding="utf-8")
            (skill / "scripts" / "__pycache__" / "tool.cpython-312.pyc").write_bytes(b"\xcb\x0d\x0d\x0a\x00\xff")
            proc = subprocess.run([sys.executable, str(ROOT / "tools" / "skill_sizes.py"), tmp],
                                  capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("scripts/tool.py (1 lines)", proc.stdout)
        self.assertNotIn(".pyc", proc.stdout)

    def test_demo_bad_skills_show_the_lesson_mistakes(self):
        proc = subprocess.run([sys.executable, str(ROOT / "tools" / "skills_lint.py"), "tools/demo_bad_skills"],
                              capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("4 skills, 3 error(s).", proc.stdout)
        self.assertIn("csv-stats <-> csv-totals", proc.stdout)

    def test_manual_skill_is_not_model_invocable(self):
        manual = {s.name for s in course_skills() if not s.model_invocable}
        self.assertEqual(manual, {"clear-todos"})


    def test_skilllib_cuts_the_not_for_sentence_and_splits_words(self):
        from skilllib import positive_description, tokens

        text = "Converts units. Use when asked. Not for dates (use calculating-dates)."
        self.assertEqual(positive_description(text), "Converts units. Use when asked.")
        self.assertEqual(tokens("Totals tax/VAT for the dates"), ["total", "tax/vat", "tax", "vat", "date"])

    def test_only_data_folder_hook_blocks_writes_outside_data(self):
        hook = [sys.executable, str(ROOT / "tools" / "hooks" / "only_data_folder.py")]
        for path, code in [("data/notes.txt", 0), ("notes.txt", 2), ("data/../notes.txt", 2)]:
            event = json.dumps({"tool_name": "Write", "tool_input": {"file_path": path}, "cwd": str(ROOT)})
            proc = subprocess.run(hook, input=event, capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
            self.assertEqual(proc.returncode, code, path)
        self.assertIn("Blocked by hook: files may only be written inside", proc.stderr)

    @unittest.skipUnless(has_packages("claude_agent_sdk"), "install claude-agent-sdk to run this test")
    def test_show_sdk_command_prints_the_sdk_flags(self):
        proc = subprocess.run([sys.executable, str(ROOT / "tools" / "show_sdk_command.py"), "--model", "haiku"],
                              capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for expected in ("claude.exe", "Skill,Read,Bash(python *),PowerShell(python *)", "--setting-sources=project"):
            self.assertIn(expected, proc.stdout)

class CalculatingMath(unittest.TestCase):
    """examples/skills/calculating-math/scripts/calc.py: the strict calculator behind the messy-input skill (Lesson 8)."""

    spec = importlib.util.spec_from_file_location(
        "example_calc", ROOT / "examples" / "skills" / "calculating-math" / "scripts" / "calc.py")
    calc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(calc)

    def test_four_basic_operations_keep_the_order(self):
        self.assertEqual(self.calc.calculate("add", ["7", "5"])["result"], 12)
        self.assertEqual(self.calc.calculate("subtract", ["7", "5"])["result"], 2)
        self.assertEqual(self.calc.calculate("multiply", ["7", "5"])["result"], 35)
        self.assertEqual(self.calc.calculate("divide", ["10", "4"])["result"], 2.5)

    def test_sqrt_sin_cos_with_units(self):
        self.assertAlmostEqual(self.calc.calculate("sqrt", ["45"])["result"], 6.7082039325)
        self.assertEqual(self.calc.calculate("cos", ["60"], "degrees")["result"], 0.5)
        self.assertEqual(self.calc.calculate("cos", ["90"], "degrees")["result"], 0.0)     # no 6e-17 float noise
        self.assertAlmostEqual(self.calc.calculate("sin", ["3"], "radians")["result"], 0.1411200081)

    def test_other_operation_names_are_accepted(self):
        for alias, name in [("sinus", "sin"), ("plus", "add"), ("times", "multiply"), ("SquareRoot", "sqrt")]:
            numbers = ["2", "3"] if name in ("add", "multiply") else ["1"]
            unit = "radians" if name == "sin" else None
            self.assertEqual(self.calc.calculate(alias, numbers, unit)["operation"], name)

    def test_errors_tell_claude_how_to_fix_the_call(self):
        cases = [("cos", ["23"], None, "use degrees"), ("add", ["seven", "5"], None, "'seven' -> 7"),
                 ("divide", ["1", "0"], None, "divisor"), ("sqrt", ["-4"], None, ">= 0"),
                 ("power", ["2", "3"], None, "Use one of"), ("add", ["7"], None, "exactly the numbers")]
        for operation, numbers, unit, hint in cases:
            result = self.calc.calculate(operation, numbers, unit)
            self.assertIn("error", result, operation)
            self.assertIn(hint, result["hint"])

    def test_cli(self):
        script = ROOT / "examples" / "skills" / "calculating-math" / "scripts" / "calc.py"
        proc = subprocess.run([sys.executable, str(script), "cos", "45", "--unit", "degrees"],
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual((proc.returncode, json.loads(proc.stdout)["result"]), (0, 0.7071067812))


class AgentGuard(unittest.TestCase):
    """agent/guard.py: the rules that guarded_agent.py applies to every tool call (no SDK, no Claude)."""

    spec = importlib.util.spec_from_file_location("agent_guard", ROOT / "agent" / "guard.py")
    guard_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard_module)

    def setUp(self):
        self.guard = self.guard_module.Guard(max_commands=2)

    def test_skill_scripts_are_allowed(self):
        script = (SKILLS / "analyzing-csv" / "scripts" / "csv_tool.py").as_posix()
        self.assertTrue(self.guard.check("PowerShell", {"command": f'python "{script}" summary data/sales.csv'})[0])
        self.assertTrue(self.guard.check("Bash", {"command": "python .claude/skills/converting-units/scripts/convert.py units"})[0])

    def test_other_commands_are_denied(self):
        for command in ["Get-Content CLAUDE.md", 'python -c "print(1)"', "python tools/skills_lint.py",
                        "python .claude/skills/converting-units/scripts/convert.py units ; del data\\sales.csv"]:
            allowed, reason = self.guard.check("Bash", {"command": command})
            self.assertFalse(allowed, command)
            self.assertTrue(reason)                       # Claude is always told why

    def test_writes_only_inside_data(self):
        self.assertTrue(self.guard.check("Write", {"file_path": str(DATA / "report.txt")})[0])
        self.assertTrue(self.guard.check("Edit", {"file_path": "data/report.txt"})[0])
        self.assertFalse(self.guard.check("Write", {"file_path": str(ROOT / "report.txt")})[0])
        self.assertFalse(self.guard.check("Write", {"file_path": "data/../report.txt"})[0])

    def test_command_limit_per_run(self):
        command = {"command": "python .claude/skills/converting-units/scripts/convert.py units"}
        self.assertTrue(self.guard.check("Bash", command)[0])
        self.assertTrue(self.guard.check("Bash", command)[0])
        allowed, reason = self.guard.check("Bash", command)
        self.assertFalse(allowed)
        self.assertIn("limit of 2", reason)

    def test_reading_is_allowed_other_tools_are_not(self):
        self.assertTrue(self.guard.check("Read", {"file_path": "CLAUDE.md"})[0])
        self.assertFalse(self.guard.check("WebFetch", {"url": "https://example.com"})[0])


class AskClaudeCommand(unittest.TestCase):
    """agent/ask_claude.py: the claude -p command it builds (no Claude call)."""

    spec = importlib.util.spec_from_file_location("agent_ask_claude", ROOT / "agent" / "ask_claude.py")
    ask = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ask)

    def test_effort_is_passed_only_when_set(self):
        cmd = self.ask.build_cli_command("claude", "Hi", effort="low")
        self.assertEqual(cmd[cmd.index("--effort") + 1], "low")
        self.assertNotIn("--effort", self.ask.build_cli_command("claude", "Hi"))

    def test_plain_question_has_no_tools_and_no_session(self):
        cmd = self.ask.build_cli_command("claude", "Hi", model="sonnet")
        self.assertEqual(cmd[:3], ["claude", "-p", "Hi"])
        self.assertEqual(cmd[cmd.index("--tools") + 1], "")
        self.assertIn("--no-session-persistence", cmd)
        self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")

    def test_run_cost_lists_each_step_with_its_model(self):
        import run_cost
        events = [
            {"type": "assistant", "message": {"model": "claude-sonnet-5-5", "content": [
                {"type": "thinking"}, {"type": "tool_use", "name": "Skill", "input": {"skill": "converting-units"}}]}},
            {"type": "assistant", "message": {"model": "claude-haiku-5-5", "content": [
                {"type": "tool_use", "name": "Bash", "input": {"command": "python convert.py convert 1 mi km"}}]}},
            {"type": "result", "result": "1.61 km", "modelUsage": {}},
        ]
        run = run_cost.summarize(events)
        self.assertEqual(run["steps"], [("claude-sonnet-5-5", "thinks"), ("claude-sonnet-5-5", "Skill converting-units"),
                                        ("claude-haiku-5-5", "Bash: python convert.py convert 1 mi km")])
        self.assertEqual(run["result"]["result"], "1.61 km")
        cmd = run_cost.build_command("claude", "Hi", "sonnet", "low")
        self.assertEqual(cmd[cmd.index("--model") + 1], "sonnet")
        self.assertEqual(cmd[cmd.index("--effort") + 1], "low")

    def test_strict_adds_the_isolation_flags(self):
        plain = self.ask.build_cli_command("claude", "Hi")
        strict = self.ask.build_cli_command("claude", "Hi", strict=True)
        self.assertNotIn("--strict-mcp-config", plain)
        for flag in ("--strict-mcp-config", "--safe-mode"):
            self.assertIn(flag, strict)
        self.assertEqual(strict[strict.index("--setting-sources") + 1], "")
        self.assertEqual(strict[strict.index("--permission-mode") + 1], "dontAsk")

    def test_thinking_tokens_are_summed_over_models(self):
        usage = {"claude-haiku-5-5": {"thinkingTokens": 281}, "claude-sonnet-5-5": {"thinkingTokens": 19}}
        self.assertEqual(self.ask.thinking_tokens(usage), 300)
        self.assertEqual(self.ask.thinking_tokens(None), 0)


def load_agent(filename: str):
    """Import a program from agent/ (none of them needs the SDK to be imported)."""
    sys.path.insert(0, str(ROOT / "agent"))
    spec = importlib.util.spec_from_file_location(f"agent_{filename[:-3]}", ROOT / "agent" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_agent_script(filename: str, *lines: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run a hook script or the tool server as Claude Code does: JSON lines on stdin."""
    return subprocess.run([sys.executable, str(ROOT / "agent" / filename)], input="\n".join(lines) + "\n",
                          capture_output=True, text=True, encoding="utf-8", cwd=ROOT, env={**os.environ, **(env or {})})


class BothWays(unittest.TestCase):
    """The claude -p way (--cli) of the agent programs, and the rules both ways share (no Claude call)."""

    run_agent = load_agent("run_agent.py")

    def test_model_mode_compare_modes_differ_only_in_prompt_and_isolation(self):
        import model_mode_compare as mmc
        cmd = {m: mmc.build_command("claude", "Q", "haiku", m) for m in mmc.MODES}
        self.assertNotIn("--tools", cmd["harness"][0])                        # Claude Code exactly as it starts
        for mode in ("cc_prompt", "own_prompt", "strict"):
            self.assertEqual(cmd[mode][0][cmd[mode][0].index("--tools") + 1], "")
            self.assertIn("--strict-mcp-config", cmd[mode][0])
        self.assertIn("--append-system-prompt", cmd["cc_prompt"][0])         # keeps Claude Code's prompt
        self.assertIn("--system-prompt", cmd["own_prompt"][0])               # replaces it
        self.assertIn("--safe-mode", cmd["strict"][0])
        self.assertEqual(cmd["strict"][1]["CLAUDE_CODE_DISABLE_CLAUDE_MDS"], "1")
        self.assertEqual(cmd["own_prompt"][1], {})

    def test_model_mode_compare_adds_up_each_mode(self):
        import model_mode_compare as mmc
        rows = [{"mode": "strict", "right": True, "input_tokens": 800, "seconds": 4.0},
                {"mode": "strict", "right": False, "input_tokens": 900, "seconds": 6.0},
                {"mode": "harness", "right": True, "input_tokens": 39000, "seconds": 5.0}]
        summary = {s["mode"]: s for s in mmc.summarize(rows, ["harness", "strict"])}
        self.assertEqual((summary["strict"]["right"], summary["strict"]["runs"]), (1, 2))
        self.assertEqual((summary["strict"]["input_tokens"], summary["strict"]["seconds"]), (850, 5.0))
        self.assertEqual(summary["harness"]["input_tokens"], 39000)
        for q in mmc.QUESTIONS:                                                 # every built-in question is valid
            self.assertTrue(q["prompt"] and q["expect"])

    def test_harness_profile_compare_profiles_and_questions(self):
        import harness_profile_compare as hpc
        task = next(t for t in hpc.tasks() if t["name"] == "average amount")
        model_q, lean_q = hpc.question_for(task, "model"), hpc.question_for(task, "lean")
        self.assertIn("2026-01-05,North,Widget,10,250", model_q)          # the model profile gets the file's text
        self.assertEqual(lean_q, task["question"])                         # the others read the file themselves
        model_cmd, model_env, model_dir = hpc.build_command("claude", "Q", "haiku", "model")
        self.assertEqual((model_cmd[model_cmd.index("--tools") + 1], model_cmd[model_cmd.index("--max-turns") + 1]), ("", "1"))
        self.assertEqual((model_dir, model_env["CLAUDE_CODE_DISABLE_CLAUDE_MDS"]), (Path.home(), "1"))
        lean_cmd = hpc.build_command("claude", "Q", "haiku", "lean")[0]
        self.assertIn("--safe-mode", lean_cmd)
        self.assertNotIn("--system-prompt", lean_cmd)                      # keeps Claude Code's own prompt
        lean_py_cmd = hpc.build_command("claude", "Q", "haiku", "lean_py")[0]
        self.assertEqual(lean_py_cmd[lean_py_cmd.index("--append-system-prompt") + 1], hpc.PY_RULE)
        self.assertNotIn("--append-system-prompt", lean_cmd)
        skills_cmd = hpc.build_command("claude", "Q", "haiku", "skills")[0]
        self.assertTrue(skills_cmd[skills_cmd.index("--allowedTools") + 1].startswith("Skill,"))
        self.assertNotIn("--strict-mcp-config", hpc.build_command("claude", "Q", "haiku", "full")[0])
        answers = {"region totals": "North=2150, East=910, West=900, South=670", "average amount": "385.83",
                   "most units": "Widget", "invoice total": "1403.37", "word count": "180", "working days": "11",
                   "logic (control)": "Carl"}
        from decimal import Decimal
        totals = {}                                                        # the 300-row table, added up again
        for _, region, amount in hpc.orders_rows():
            totals[region] = totals.get(region, Decimal(0)) + Decimal(f"{amount:.2f}")
        answers["big table totals"] = ", ".join(f"{r}={t:,}" for r, t in totals.items())  # 12,345.67 style
        answers["big table count"] = str(sum(a > 500 for _, _, a in hpc.orders_rows()))
        self.assertEqual((len(hpc.orders_rows()), hpc.number_pattern(1234567)), (300, r"12,?345\.67"))
        self.assertEqual([len(hpc.choose_tasks(s)) for s in ("small", "big", "", "word count,big")], [7, 2, 9, 3])
        self.assertEqual(hpc.orders_rows(1000)[:300], hpc.orders_rows())   # a longer table starts with the same rows
        self.assertNotEqual(hpc.tasks(1000)[-1]["expect"], hpc.tasks()[-1]["expect"])
        long_q = "x" * (hpc.STDIN_FROM + 1)                                # too long for the command line
        cmd, stdin_text = hpc.split_long_prompt(hpc.build_command("claude", long_q, "haiku", "model")[0], long_q)
        self.assertEqual((cmd[:2], long_q in cmd, stdin_text), (["claude", "-p"], False, long_q))
        self.assertEqual(hpc.split_long_prompt(["claude", "-p", "Q"], "Q"), (["claude", "-p", "Q"], None))
        for t in hpc.tasks():                                              # the true answers pass every check
            self.assertRegex(answers[t["name"]], t["expect"], t["name"])
        self.assertNotRegex("1403.36", next(t for t in hpc.tasks() if t["name"] == "invoice total")["expect"])

    def test_harness_profile_compare_cost_per_right_answer(self):
        import harness_profile_compare as hpc
        rows = [{"profile": "lean", "right": True, "cost": 0.004, "seconds": 6, "turns": 2, "input_tokens": 20000,
                 "tools": ["Read", "Bash"]},
                {"profile": "lean", "right": False, "cost": 0.002, "seconds": 4, "turns": 2, "input_tokens": 18000,
                 "tools": ["Read"]},
                {"profile": "model", "right": False, "cost": 0.001, "seconds": 5, "turns": 1, "input_tokens": 1000}]
        summary = {s["profile"]: s for s in hpc.summarize(rows, ["model", "lean"])}
        self.assertAlmostEqual(summary["lean"]["cost_per_right"], 0.006)    # all the cost / the right answers
        self.assertIsNone(summary["model"]["cost_per_right"])               # no right answer: no cost per right
        self.assertEqual((summary["lean"]["right"], summary["lean"]["turns"]), (1, 2))
        self.assertEqual((summary["lean"]["code"], summary["model"]["code"]), (1, 0))  # runs that called Bash
        stream = "\n".join(json.dumps(e) for e in [                         # what claude -p --verbose prints
            {"type": "system", "subtype": "init"},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill",
                                                           "input": {"skill": "analyzing-text"}}]}},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {}},
                                                          {"type": "text", "text": "180"}]}},
            {"type": "result", "result": "180", "num_turns": 3}])
        result, tools = hpc.read_stream(stream + "\nnot json")
        self.assertEqual((result["result"], tools), ("180", ["Skill:analyzing-text", "Bash"]))

    def test_cli_ways_need_no_sdk(self):
        code = "\n".join([
            "import sys",
            "sys.modules['claude_agent_sdk'] = None    # from now on, every import of the SDK fails",
            "sys.path[:0] = ['agent', 'tools']",
            "import run_agent, chat_agent, guarded_agent, effort_probe, custom_tools_agent, tutor_mcp_server",
            "import run_cost, routing_eval",
            "run_agent.build_cli_command('claude', 'Hi')",
            "custom_tools_agent.build_cli_command('claude', 'Hi')",
            "print('ok')",
        ])
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
        self.assertEqual(proc.stdout.strip(), "ok", proc.stderr)

    def test_run_agent_cli_command_has_the_flags_the_sdk_passes(self):
        cmd = self.run_agent.build_cli_command("claude", "Hi", "all", "haiku", "low")
        self.assertEqual(cmd[:3], ["claude", "-p", "Hi"])
        self.assertEqual(cmd[cmd.index("--system-prompt") + 1], "")
        self.assertEqual(cmd[cmd.index("--allowedTools") + 1], "Skill,Read,Bash(python *),PowerShell(python *)")
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "project")
        self.assertEqual((cmd[cmd.index("--max-turns") + 1], cmd[cmd.index("--model") + 1],
                          cmd[cmd.index("--effort") + 1]), ("15", "haiku", "low"))

    def test_run_agent_cli_skill_list_resume_and_hooks(self):
        cmd = self.run_agent.build_cli_command("claude", "Hi", ["converting-units"], resume="abc",
                                               settings=self.run_agent.hook_settings(Path("agent/guard_hook.py"), "Bash"))
        self.assertTrue(cmd[cmd.index("--allowedTools") + 1].startswith("Skill(converting-units),Read"))
        self.assertEqual(cmd[cmd.index("--resume") + 1], "abc")
        self.assertIn("--include-hook-events", cmd)
        hook = json.loads(cmd[cmd.index("--settings") + 1])["hooks"]["PreToolUse"][0]
        self.assertEqual(hook["matcher"], "Bash")
        self.assertTrue(hook["hooks"][0]["command"].endswith('agent/guard_hook.py"'))
        no_matcher = json.loads(self.run_agent.hook_settings(Path("agent/effort_hook.py")))["hooks"]["PreToolUse"][0]
        self.assertNotIn("matcher", no_matcher)

    def test_guard_hook_keeps_the_count_in_a_file(self):
        command = json.dumps({"tool_name": "Bash", "tool_input": {
            "command": "python .claude/skills/converting-units/scripts/convert.py units"}})
        with tempfile.TemporaryDirectory() as tmp:
            env = {"GUARD_STATE": str(Path(tmp) / "count.txt")}
            decisions = [json.loads(run_agent_script("guard_hook.py", command, env=env).stdout)
                         ["hookSpecificOutput"]["permissionDecision"] for _ in range(7)]
        self.assertEqual(decisions, ["allow"] * 6 + ["deny"])
        proc = run_agent_script("guard_hook.py", json.dumps({"tool_name": "Write", "tool_input": {"file_path": "x.txt"}}))
        self.assertTrue(proc.stderr.startswith("[guard] DENY  Write: x.txt"))

    def test_effort_hook_writes_its_line_to_stderr_only(self):
        proc = run_agent_script("effort_hook.py", json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "python x.py"}, "effort": {"level": "low"}}))
        self.assertEqual((proc.stdout, proc.stderr.strip()), ("", "[effort] low    before Bash: python x.py"))
        effort_hook = load_agent("effort_hook.py")
        line = effort_hook.effort_line({"tool_name": "Read", "tool_input": {"file_path": "a.txt"}, "agent_type": "Explore"})
        self.assertEqual(line, "[effort] (not reported) before Read (in subagent Explore): a.txt")

    def test_tutor_mcp_server_answers_json_rpc(self):
        proc = run_agent_script(
            "tutor_mcp_server.py",
            json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}}),
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                        "params": {"name": "weekday", "arguments": {"date": "2026-12-25"}}}),
            json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                        "params": {"name": "weekday", "arguments": {"date": "2026-02-30"}}}),
        )
        replies = [json.loads(line) for line in proc.stdout.splitlines()]
        self.assertEqual([r["id"] for r in replies], [0, 1, 2, 3])      # no reply to the notification
        self.assertEqual(replies[0]["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual([t["name"] for t in replies[1]["result"]["tools"]],
                         ["convert_units", "weekday", "add_business_days"])
        self.assertEqual(json.loads(replies[2]["result"]["content"][0]["text"])["weekday"], "Friday")
        self.assertTrue(replies[3]["result"]["isError"])

    def test_custom_tools_agent_cli_command_starts_the_tool_server(self):
        tools_agent = load_agent("custom_tools_agent.py")
        cmd = tools_agent.build_cli_command("claude", "Hi")
        server = json.loads(cmd[cmd.index("--mcp-config") + 1])["mcpServers"]["tutor"]
        self.assertTrue(server["args"][0].endswith("tutor_mcp_server.py"))
        self.assertEqual((cmd[cmd.index("--tools") + 1], cmd[cmd.index("--allowedTools") + 1]), ("", "mcp__tutor__*"))
        self.assertIn("--strict-mcp-config", cmd)

    def test_routing_eval_rules_are_shared_by_both_ways(self):
        import routing_eval
        outcome = routing_eval.new_outcome()
        self.assertFalse(routing_eval.read_event(outcome, {"type": "system", "subtype": "init", "skills": ["a"]}))
        skill = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill",
                                                               "input": {"skill": "converting-units"}}]}}
        self.assertTrue(routing_eval.read_event(outcome, skill))
        self.assertEqual((outcome["skill"], outcome["skills_loaded"]), ("converting-units", ["a"]))
        outcome = routing_eval.new_outcome()
        read = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {}}]}}
        self.assertEqual([routing_eval.read_event(outcome, read) for _ in range(3)], [False, False, True])


    def test_run_agent_run_cli_prints_the_steps_of_a_fake_claude(self):
        lines = [
            {"type": "system", "subtype": "init", "apiKeySource": "none", "model": "claude-haiku-5-5", "skills": ["a"]},
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": "a"}}]}},
            {"type": "system", "subtype": "hook_response", "stderr": "[guard] ALLOW Bash: python x.py  (ok)"},
            {"type": "user", "message": {"content": [{"type": "tool_result", "is_error": True, "content": "denied"}]}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "Done."}]}},
            {"type": "result", "subtype": "success", "num_turns": 3, "total_cost_usd": 0.001, "session_id": "s1"},
        ]
        fake_claude = [sys.executable, "-c", "import sys; sys.stdout.write(sys.argv[1])",
                       "".join(json.dumps(line) + "\n" for line in lines)]     # prints what claude -p would print
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = self.run_agent.run_cli(fake_claude)
        self.assertEqual(result["session_id"], "s1")
        for expected in ("[init] auth: claude.ai subscription", "[skill] Claude picked: a", "[guard] ALLOW Bash",
                         "[refused] denied", "[claude] Done.", "[done] success, turns=3, cost≈$0.0010"):
            self.assertIn(expected, output.getvalue())

    def test_chat_agent_cli_way_passes_the_session_id(self):
        chat_agent = load_agent("chat_agent.py")
        calls = []
        fake_run_cli = lambda cmd, show_init=True, env=None: calls.append(cmd) or {"session_id": "abc"}
        with mock.patch.object(chat_agent, "run_cli", fake_run_cli), \
                mock.patch.object(chat_agent, "find_claude", lambda: "claude"), contextlib.redirect_stdout(io.StringIO()):
            chat_agent.chat_cli("haiku", interactive=False)
        self.assertEqual([cmd[2] for cmd in calls], chat_agent.DEMO_QUESTIONS)
        self.assertNotIn("--resume", calls[0])
        self.assertEqual(calls[1][calls[1].index("--resume") + 1], "abc")

    def test_guarded_agent_cli_way_switches_on_guard_hook(self):
        guarded_agent = load_agent("guarded_agent.py")
        seen = {}
        fake_run_cli = lambda cmd, show_init=True, env=None: seen.update(cmd=cmd, env=env) or {}
        with mock.patch.object(guarded_agent, "run_cli", fake_run_cli), \
                mock.patch.object(guarded_agent, "find_claude", lambda: "claude"):
            guarded_agent.run_cli_way("Hi", "haiku")
        hook = json.loads(seen["cmd"][seen["cmd"].index("--settings") + 1])["hooks"]["PreToolUse"][0]
        self.assertEqual(hook["matcher"], "Bash|PowerShell|Write|Edit")
        self.assertIn("guard_hook.py", hook["hooks"][0]["command"])
        self.assertTrue(seen["env"]["GUARD_STATE"].endswith("guard_state.txt"))

    def test_effort_probe_cli_way_resumes_and_prints_usage(self):
        effort_probe = load_agent("effort_probe.py")
        calls = []
        usage = {"claude-sonnet-5-5": {"outputTokens": 229, "thinkingTokens": 27}}
        fake_run_cli = lambda cmd, show_init=True, env=None: calls.append(cmd) or {"session_id": "s1", "modelUsage": usage}
        output = io.StringIO()
        with mock.patch.object(effort_probe, "run_cli", fake_run_cli), \
                mock.patch.object(effort_probe, "find_claude", lambda: "claude"), contextlib.redirect_stdout(output):
            effort_probe.run_cli_way(["first", "second"], "sonnet", None)
        hook = json.loads(calls[0][calls[0].index("--settings") + 1])["hooks"]["PreToolUse"][0]
        self.assertNotIn("matcher", hook)                      # no matcher: before every tool
        self.assertIn("effort_hook.py", hook["hooks"][0]["command"])
        self.assertEqual(calls[1][calls[1].index("--resume") + 1], "s1")
        self.assertIn("[usage] claude-sonnet-5-5: output 229 tokens, of which thinking 27", output.getvalue())

    def test_api_equivalent_prints_tokens_like_the_api(self):
        api_equivalent = load_agent("api_equivalent.py")
        reply = {"text": "Answer.", "model_usage": {"claude-sonnet-5-5": {"thinkingTokens": 73}},
                 "usage": {"input_tokens": 2, "cache_creation_input_tokens": 4307, "cache_read_input_tokens": 0,
                           "output_tokens": 77}}
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            api_equivalent.print_like_api(reply)
        self.assertIn("Input tokens: 4309 (new 2, written to cache 4307, read from cache 0)", output.getvalue())
        self.assertIn("Output tokens: 77 (of which thinking 73)", output.getvalue())

    def test_routing_eval_dry_run_prints_one_command_per_question(self):
        proc = subprocess.run([sys.executable, str(ROOT / "tools" / "routing_eval.py"), "--dry-run", "--limit", "2"],
                              capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
        lines = proc.stdout.splitlines()
        self.assertEqual((proc.returncode, len(lines)), (0, 2))
        self.assertTrue(all(" -p " in line and "--setting-sources project" in line for line in lines))

    @unittest.skipUnless(has_packages("claude_agent_sdk"), "install claude-agent-sdk to run this test")
    def test_run_cost_sdk_options_make_the_same_run_as_claude_p(self):
        import run_cost
        options = run_cost.sdk_options("sonnet", "low")
        self.assertEqual(options.system_prompt, {"type": "preset", "preset": "claude_code"})
        self.assertEqual(options.setting_sources, ["user", "project", "local"])
        self.assertEqual(",".join(options.allowed_tools), run_cost.ALLOWED_TOOLS)
        self.assertEqual((options.model, options.effort), ("sonnet", "low"))

if __name__ == "__main__":
    unittest.main()
