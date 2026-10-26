"""Sheets, summaries and pivot tables of an Excel workbook. The script of the analyzing-excel skill (Lesson 7).

WHAT
    Four commands:
        check                       which Python runs the script, and the pandas and openpyxl versions
        sheets FILE                 the sheet names, with their row counts and column names
        summary FILE [--sheet NAME] the columns of one sheet: type, missing values, min, max, mean,
                                    median, sum, first and last date, frequent values
        pivot FILE --index COL --values COL [--columns COL] [--agg sum|mean|count|min|max] [--sheet NAME]
                                    a pivot table with a Total row and column

WHY
    .xlsx files can't be read as text. pandas reads them, and computes exact totals and pivots, so
    Claude only explains the result.

HOW CLAUDE USES IT
    The analyzing-excel SKILL.md tells Claude to run sheets first, then summary or pivot. Claude runs
    plain `python`, so the packages must be in the Python that comes first on PATH: start claude from
    a cmd window where the venv is activated. Claude reads only the JSON that the script prints.

HOW TO RUN IT YOURSELF  (in cmd, from the project folder, with the venv activated)
    python .claude/skills/analyzing-excel/scripts/excel_tool.py check
        {"python": "C:/pyenvsmy/claudeclioct26/Scripts/python.exe", "pandas": "3.0.6", "openpyxl": "3.1.5"}
    python .claude/skills/analyzing-excel/scripts/excel_tool.py sheets data/sales.xlsx
    python .claude/skills/analyzing-excel/scripts/excel_tool.py summary data/sales.xlsx --sheet Sales
    python .claude/skills/analyzing-excel/scripts/excel_tool.py pivot data/sales.xlsx --index region --columns product --values amount

ERRORS
    - A wrong sheet or column name prints the error and the real names, with exit code 1.
    - Without the packages (the venv was not activated) it prints, with exit code 2:
        {"error": "Python package 'pandas' is not installed in C:/Python312/python.exe",
         "hint": "Claude Code was started without the skills' virtual environment. ..."}
      Claude reads the hint and tells you how to fix it, instead of failing with a long traceback.

NEEDS
    pandas and openpyxl, listed in requirements.txt next to this file. Install them once into the venv:
        python -m pip install -r .claude/skills/analyzing-excel/scripts/requirements.txt
    It never calls Claude.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k excel -k WrongInterpreter
       Expected (4 tests; the time differs):
           ....
           ----------------------------------------------------------------------
           Ran 4 tests in 8.575s

           OK
       What they check: sheet names and a sheet summary, a pivot with Total row and column, the real
       sheet names after a wrong one, and the helpful message when pandas is missing. Add -v to see the
       name of each test.
    2. By hand: free.
           python .claude/skills/analyzing-excel/scripts/excel_tool.py pivot data/sales.xlsx --index region --values amount
               {"index": "region", "columns": null, "values": "amount", "agg": "sum", "rows": [{"region": "East", "amount": 910},
                ..., {"region": "Total", "amount": 4630}]}
           python -S .claude/skills/analyzing-excel/scripts/excel_tool.py check
               {"error": "Python package 'pandas' is not installed in C:/pyenvsmy/claudeclioct26/Scripts/python.exe",
                "hint": "Claude Code was started without the skills' virtual environment. ..."}       (exit code 2)
               (-S tells Python to ignore installed packages, so this shows what happens without the venv.)
    3. With Claude: uses a little Pro allowance.
           claude -p "Which sheets are in data/sales.xlsx, and how many rows does each have?" --model haiku --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)"
               Expected: Sales with 12 rows, Targets with 4 rows (the real run showed them as a table).

IF SOMETHING GOES WRONG
    - Exit code 2 and "is not installed in C:/Python312/python.exe": claude was started without the venv.
      Activate the venv, then start claude again (Lesson 7, Step 7).
    - A wrong sheet name: the error lists the real names. Sheet names are case-sensitive ("Sales").
    - "Permission denied" while the workbook is open in Excel: close it in Excel and run again.

FILES IT READS AND WRITES
    Reads the .xlsx file you name. Writes nothing.

SEE ALSO
    requirements.txt next to this file; analyzing-excel/SKILL.md; tests PackageSkills and
    WrongInterpreter; Lesson 7, Steps 4, 7 and 9.
"""

import argparse
import json
import sys
from pathlib import Path

REQUIREMENTS = Path(__file__).with_name("requirements.txt")

try:
    import pandas as pd
    import openpyxl  # noqa: F401  (pandas needs it to read .xlsx)
except ImportError as missing:
    # Wrong interpreter (or packages not installed yet). Say exactly how to fix the call.
    print(json.dumps({
        "error": f"Python package '{missing.name}' is not installed in {sys.executable}",
        "hint": "Claude Code was started without the skills' virtual environment. Activate the venv, "
                f"then start claude again. Missing packages: python -m pip install -r \"{REQUIREMENTS}\"",
    }))
    sys.exit(2)

# Text columns: how many of the most frequent values to show.
TOP_VALUES_SHOWN = 3
AGGREGATIONS = ("sum", "mean", "count", "min", "max")


class ExcelError(Exception):
    def __init__(self, message: str, **extra):
        super().__init__(message)
        self.payload = {"error": message, **extra}


def _workbook(path: str) -> "pd.ExcelFile":
    if not Path(path).exists():
        raise ExcelError(f"File not found: {path}", hint="Check the path relative to the current directory.")
    return pd.ExcelFile(path, engine="openpyxl")


def _frame(path: str, sheet: str | None) -> "pd.DataFrame":
    book = _workbook(path)
    if sheet is not None and sheet not in book.sheet_names:
        raise ExcelError(f"Unknown sheet '{sheet}'.", sheets=book.sheet_names)
    return book.parse(sheet if sheet is not None else book.sheet_names[0])


def _require(df: "pd.DataFrame", *columns: str | None) -> None:
    for column in columns:
        if column is not None and column not in df.columns:
            raise ExcelError(f"Unknown column '{column}'.", columns=[str(c) for c in df.columns])


def _plain(value):
    """numpy / pandas scalars -> JSON-friendly Python values."""
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat() if value == value.normalize() else value.isoformat()
    return value.item() if hasattr(value, "item") else value


def check() -> dict:
    return {"python": sys.executable, "pandas": pd.__version__, "openpyxl": openpyxl.__version__}


def sheets(path: str) -> dict:
    book = _workbook(path)
    out = []
    for name in book.sheet_names:
        df = book.parse(name)
        out.append({"sheet": name, "rows": len(df), "columns": [str(c) for c in df.columns]})
    return {"file": path, "sheets": out}


def summary(path: str, sheet: str | None = None) -> dict:
    df = _frame(path, sheet)
    columns = []
    for name in df.columns:
        series = df[name]
        info = {"name": str(name), "count": int(series.count()), "missing": int(series.isna().sum())}
        if pd.api.types.is_bool_dtype(series):
            info.update(type="boolean", true=int(series.sum()))
        elif pd.api.types.is_numeric_dtype(series):
            info.update(type="numeric", min=_plain(series.min()), max=_plain(series.max()),
                        mean=round(float(series.mean()), 4), median=_plain(series.median()), sum=_plain(series.sum()))
        elif pd.api.types.is_datetime64_any_dtype(series):
            info.update(type="date", min=_plain(series.min()), max=_plain(series.max()))
        else:
            top = series.value_counts().head(TOP_VALUES_SHOWN)
            info.update(type="text", unique=int(series.nunique()), top_values=[[str(k), int(v)] for k, v in top.items()])
        columns.append(info)
    return {"file": path, "sheet": sheet or _workbook(path).sheet_names[0], "rows": len(df), "columns": columns}


def pivot(path: str, index: str, values: str, columns: str | None = None, agg: str = "sum",
          sheet: str | None = None) -> dict:
    if agg not in AGGREGATIONS:
        raise ExcelError(f"Unknown aggregation '{agg}'.", valid=list(AGGREGATIONS))
    df = _frame(path, sheet)
    _require(df, index, values, columns)
    table = pd.pivot_table(df, index=index, columns=columns, values=values, aggfunc=agg,
                           fill_value=0, margins=True, margins_name="Total")
    if isinstance(table, pd.Series):
        table = table.to_frame()
    table.columns = [str(c) for c in table.columns]
    rows = [{index: str(label), **{c: _plain(round(v, 4) if isinstance(v, float) else v) for c, v in row.items()}}
            for label, row in table.iterrows()]
    return {"index": index, "columns": columns, "values": values, "agg": agg, "rows": rows}


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="Analyze an Excel workbook.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="show the interpreter and package versions")
    p_sheets = sub.add_parser("sheets", help="sheet names, row counts, column names")
    p_sheets.add_argument("file")
    p_summary = sub.add_parser("summary", help="column types and statistics for one sheet")
    p_summary.add_argument("file")
    p_summary.add_argument("--sheet")
    p_pivot = sub.add_parser("pivot", help="pivot table with totals")
    p_pivot.add_argument("file")
    p_pivot.add_argument("--index", required=True)
    p_pivot.add_argument("--values", required=True)
    p_pivot.add_argument("--columns")
    p_pivot.add_argument("--agg", default="sum", choices=AGGREGATIONS)
    p_pivot.add_argument("--sheet")

    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            result = check()
        elif args.command == "sheets":
            result = sheets(args.file)
        elif args.command == "summary":
            result = summary(args.file, args.sheet)
        else:
            result = pivot(args.file, args.index, args.values, args.columns, args.agg, args.sheet)
    except ExcelError as err:
        print(json.dumps(err.payload, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
