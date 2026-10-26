"""Bar and line charts as PNG pictures, from .csv or .xlsx data. The script of the plotting-charts skill (Lesson 7).

WHAT
    Three commands:
        check                                                  which Python runs the script, and the
                                                               pandas and matplotlib versions
        bar FILE --x COL --y COL [--agg sum|mean|count|min|max] [--sheet NAME] [--title T] [--out PNG]
                                                               one bar per value of --x
        line FILE --x COL --y COL [--agg ...] [--freq D|W|M] [--sheet NAME] [--title T] [--out PNG]
                                                               values over time; --freq groups the
                                                               dates by day, week or month
    Without --out the picture goes to charts/<kind>_<y>_by_<x>.png. --sheet is for .xlsx files.

WHY
    Claude can't draw a picture by itself. matplotlib can, and the script also prints the numbers of
    each bar or point, so Claude can describe the chart without seeing it.

HOW CLAUDE USES IT
    The plotting-charts SKILL.md tells Claude to run bar or line, and to tell you where the PNG file is.
    Claude runs plain `python`, so start claude from a cmd window where the venv is activated.

HOW TO RUN IT YOURSELF  (in cmd, from the project folder, with the venv activated)
    python .claude/skills/plotting-charts/scripts/chart.py check
    python .claude/skills/plotting-charts/scripts/chart.py bar data/sales.csv --x region --y amount
        {"written": "charts/bar_amount_by_region.png", "kind": "bar", "x": "region", "y": "amount",
         "agg": "sum", "points": [{"region": "North", "amount": 2150.0}, ...]}
    python .claude/skills/plotting-charts/scripts/chart.py line data/sales.xlsx --sheet Sales --x date --y amount --freq M
    start charts/bar_amount_by_region.png          (opens the picture)

ERRORS
    - A wrong file, sheet or column name prints {"error": ...} with exit code 1.
    - Without the packages (the venv was not activated) it prints an error and a hint with exit code 2,
      the same as excel_tool.py.

HOW IT WORKS
    pandas groups and aggregates the data; matplotlib draws it with the "Agg" backend, which writes
    files and never opens a window, so it works when Claude runs it.

NEEDS
    pandas, openpyxl and matplotlib, listed in requirements.txt next to this file. Install them once:
        python -m pip install -r .claude/skills/plotting-charts/scripts/requirements.txt
    It never calls Claude.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k chart -k WrongInterpreter
       Expected (3 tests; the time differs):
           ...
           ----------------------------------------------------------------------
           Ran 3 tests in 6.417s

           OK
       What they check: a bar chart that is a real PNG file, a line chart by month from the .xlsx file,
       and the helpful message when the packages are missing. Add -v to see the name of each test.
    2. By hand: free.
           python .claude/skills/plotting-charts/scripts/chart.py bar data/sales.csv --x region --y amount --out charts/test_bar.png
               {"written": "charts/test_bar.png", "kind": "bar", "x": "region", "y": "amount", "agg": "sum",
                "points": [{"region": "North", "amount": 2150.0}, {"region": "East", "amount": 910.0}, ...]}
           start charts/test_bar.png              (look at it; then delete charts/test_bar.png)
           python .claude/skills/plotting-charts/scripts/chart.py bar data/sales.csv --x Region --y amount
               {"error": "Unknown column 'Region'.", "columns": ["date", "region", "product", "units", "amount"]}     (exit code 1)
    3. With Claude: uses a little Pro allowance.
           claude -p "Make a bar chart of the total amount per region from data/sales.csv." --model haiku --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)"
               Expected: the file charts/bar_amount_by_region.png, and the totals North 2,150, East 910, West 900,
               South 670 in the answer.

IF SOMETHING GOES WRONG
    - Exit code 2 and "is not installed in ...": the venv is not active (same as excel_tool.py).
    - The picture is not in charts/: charts/ is relative to the current folder; the "written" field shows
      where the file went.

FILES IT READS AND WRITES
    Reads the .csv or .xlsx file. Writes the PNG file (charts/ is ignored by git).

SEE ALSO
    requirements.txt next to this file; plotting-charts/SKILL.md; Lesson 3, Step E3; Lesson 7, Step 5.
"""

import argparse
import json
import sys
from pathlib import Path

REQUIREMENTS = Path(__file__).with_name("requirements.txt")

try:
    import matplotlib

    matplotlib.use("Agg")  # draw to files only; no window (Claude runs this without a screen)
    import matplotlib.pyplot as plt
    import pandas as pd
except ImportError as missing:
    # Wrong interpreter (or packages not installed yet). Say exactly how to fix the call.
    print(json.dumps({
        "error": f"Python package '{missing.name}' is not installed in {sys.executable}",
        "hint": "Claude Code was started without the skills' virtual environment. Activate the venv, "
                f"then start claude again. Missing packages: python -m pip install -r \"{REQUIREMENTS}\"",
    }))
    sys.exit(2)

AGGREGATIONS = ("sum", "mean", "count", "min", "max")
# pandas resample codes: day, week (ending Sunday), month (end of month).
FREQUENCIES = {"D": "D", "W": "W", "M": "ME"}
# 8 x 4.5 inches at 120 dpi = 960 x 540 px: readable on screen, small file.
FIGSIZE, DPI = (8, 4.5), 120


class ChartError(Exception):
    def __init__(self, message: str, **extra):
        super().__init__(message)
        self.payload = {"error": message, **extra}


def load(path: str, sheet: str | None = None) -> "pd.DataFrame":
    file = Path(path)
    if not file.exists():
        raise ChartError(f"File not found: {path}", hint="Check the path relative to the current directory.")
    if file.suffix.lower() in (".xlsx", ".xlsm"):
        book = pd.ExcelFile(file, engine="openpyxl")
        if sheet is not None and sheet not in book.sheet_names:
            raise ChartError(f"Unknown sheet '{sheet}'.", sheets=book.sheet_names)
        return book.parse(sheet if sheet is not None else book.sheet_names[0])
    return pd.read_csv(file, encoding="utf-8-sig")


def _require(df: "pd.DataFrame", *columns: str) -> None:
    for column in columns:
        if column not in df.columns:
            raise ChartError(f"Unknown column '{column}'.", columns=[str(c) for c in df.columns])


LABEL_FORMATS = {"M": "%Y-%m", "W": "week to %Y-%m-%d", "D": "%Y-%m-%d"}


def _label(value, freq: str | None = None) -> str:
    if isinstance(value, pd.Timestamp):
        return value.strftime(LABEL_FORMATS.get(freq, "%Y-%m-%d"))
    return str(value)


def _points(series: "pd.Series", x: str, y: str, freq: str | None = None) -> list[dict]:
    return [{x: _label(k, freq), y: round(float(v), 4)} for k, v in series.items()]


def _save(fig, out: Path) -> str:
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    return out.as_posix()


def bar(path: str, x: str, y: str, agg: str = "sum", sheet: str | None = None,
        title: str | None = None, out: str | None = None) -> dict:
    df = load(path, sheet)
    _require(df, x, y)
    series = df.groupby(x)[y].agg(agg).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.bar([str(k) for k in series.index], series.values, color="#4C72B0")
    for i, v in enumerate(series.values):
        ax.annotate(f"{v:,.0f}", (i, v), ha="center", va="bottom", fontsize=9)
    ax.set_title(title or f"{agg} of {y} by {x}")
    ax.set_xlabel(x)
    ax.set_ylabel(f"{y} ({agg})")
    ax.spines[["top", "right"]].set_visible(False)
    written = _save(fig, Path(out or f"charts/bar_{y}_by_{x}.png"))
    return {"written": written, "kind": "bar", "x": x, "y": y, "agg": agg, "points": _points(series, x, y)}


def line(path: str, x: str, y: str, agg: str = "sum", freq: str | None = None, sheet: str | None = None,
         title: str | None = None, out: str | None = None) -> dict:
    df = load(path, sheet)
    _require(df, x, y)
    if freq:
        if freq not in FREQUENCIES:
            raise ChartError(f"Unknown --freq '{freq}'.", valid=list(FREQUENCIES))
        dates = pd.to_datetime(df[x], errors="coerce")
        if dates.isna().all():
            raise ChartError(f"Column '{x}' does not contain dates, so --freq cannot be used.")
        series = df.assign(**{x: dates}).set_index(x)[y].resample(FREQUENCIES[freq]).agg(agg)
    else:
        series = df.groupby(x)[y].agg(agg).sort_index()
    labels = [_label(k, freq) for k in series.index]
    fig, ax = plt.subplots(figsize=FIGSIZE)
    # Plot against positions with text labels, so each point sits exactly on its period's label.
    ax.plot(range(len(series)), series.values, marker="o", color="#4C72B0")
    ax.set_xticks(range(len(series)), labels)
    for i, v in enumerate(series.values):
        ax.annotate(f"{v:,.0f}", (i, v), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=9)
    period = {"D": "day", "W": "week", "M": "month"}.get(freq)
    ax.set_title(title or f"{agg} of {y} per {period}" if period else title or f"{agg} of {y} by {x}")
    ax.set_xlabel(x)
    ax.set_ylabel(f"{y} ({agg})")
    ax.grid(alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.autofmt_xdate()
    written = _save(fig, Path(out or f"charts/line_{y}_by_{x}.png"))
    return {"written": written, "kind": "line", "x": x, "y": y, "agg": agg, "freq": freq,
            "points": _points(series, x, y, freq)}


def check() -> dict:
    return {"python": sys.executable, "pandas": pd.__version__, "matplotlib": matplotlib.__version__}


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="Draw a chart from a .csv or .xlsx file.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="show the interpreter and package versions")
    for kind in ("bar", "line"):
        p = sub.add_parser(kind)
        p.add_argument("file")
        p.add_argument("--x", required=True)
        p.add_argument("--y", required=True)
        p.add_argument("--agg", default="sum", choices=AGGREGATIONS)
        p.add_argument("--sheet")
        p.add_argument("--title")
        p.add_argument("--out", help="PNG path (default: charts/<kind>_<y>_by_<x>.png)")
        if kind == "line":
            p.add_argument("--freq", choices=list(FREQUENCIES), help="group dates by day, week or month")

    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            result = check()
        elif args.command == "bar":
            result = bar(args.file, args.x, args.y, args.agg, args.sheet, args.title, args.out)
        else:
            result = line(args.file, args.x, args.y, args.agg, args.freq, args.sheet, args.title, args.out)
    except ChartError as err:
        print(json.dumps(err.payload, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
