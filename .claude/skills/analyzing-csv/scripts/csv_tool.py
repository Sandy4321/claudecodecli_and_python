"""Summaries, totals per group and top rows of a .csv file. The script of the analyzing-csv skill (Lesson 3, Pattern A).

WHAT
    Three commands:
        summary FILE                                            the columns: type, missing values,
                                                                min, max, mean, median, frequent values
        groupby FILE --by COL --value COL [--agg sum|mean|count|min|max]   a total (or other
                                                                aggregate) per group, largest first
        top FILE --column COL [--n 5] [--asc]                   the N rows with the largest (or, with
                                                                --asc, the smallest) values

WHY
    Adding up a column by "reading" it is where language models make mistakes. Python counts exactly,
    and the whole file never has to enter Claude's context: Claude sees only the short result.

HOW CLAUDE USES IT
    The analyzing-csv SKILL.md tells Claude to run summary first, to learn the exact column names, then
    groupby or top. Claude reads only the JSON that the script prints, never this file.

HOW TO RUN IT YOURSELF  (in cmd, from the project folder)
    python .claude/skills/analyzing-csv/scripts/csv_tool.py summary data/sales.csv
    python .claude/skills/analyzing-csv/scripts/csv_tool.py groupby data/sales.csv --by region --value amount
        {"by": "region", "value": "amount", "agg": "sum", "groups": [{"region": "North",
         "amount_sum": 2150.0}, {"region": "East", "amount_sum": 910.0}, ...]}
    python .claude/skills/analyzing-csv/scripts/csv_tool.py top data/sales.csv --column amount --n 2

ERRORS
    A wrong column name prints the error and the real column names, with exit code 1:
        {"error": "Unknown column 'Region'.", "columns": ["date", "region", "product", "units", "amount"]}
    so Claude can correct the name and try again.

HOW IT WORKS
    The csv module reads the rows as text; to_number() turns a cell into a number, or None when it is
    not one. A column counts as numeric when all its filled cells are numbers.

NEEDS
    Only the standard library (no pandas). It never calls Claude.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k AnalyzingCsv
       Expected (4 tests; the time differs):
           ....
           ----------------------------------------------------------------------
           Ran 4 tests in 0.215s

           OK
       What they check: column types and missing values, totals per group sorted largest first, top
       rows, and the list of real column names after a wrong one. Add -v to see the name of each test.
    2. By hand: free.
           python .claude/skills/analyzing-csv/scripts/csv_tool.py groupby data/sales.csv --by region --value amount --agg count
               {"by": "region", "value": "amount", "agg": "count", "groups": [{"region": "North", "amount_count": 4},
                {"region": "South", "amount_count": 3}, {"region": "East", "amount_count": 3}, {"region": "West", "amount_count": 2}]}
           python .claude/skills/analyzing-csv/scripts/csv_tool.py top data/sales.csv --column price
               {"error": "Unknown column 'price'.", "columns": ["date", "region", "product", "units", "amount"]}     (exit code 1)
    3. With Claude: uses a little Pro allowance.
           claude -p "What is the total amount per region in data/sales.csv?" --model haiku --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)"
               Expected: North 2,150, East 910, West 900, South 670. In the real run Claude said it used the
               groupby command of the analyzing-csv skill.

IF SOMETHING GOES WRONG
    - {"error": "File not found: data/missing.csv", ...}: paths are relative to the current folder, so run
      the command from the project folder.
    - "Column 'x' has non-numeric value ...": sum, mean, min and max need numbers; use --agg count for a
      text column.

FILES IT READS AND WRITES
    Reads the CSV file you name. Writes nothing.

SEE ALSO
    analyzing-csv/SKILL.md and analyzing-csv/reference.md; class AnalyzingCsv in
    tests/test_skill_scripts.py; Lesson 3, Pattern A.
"""

import argparse
import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

# How many [value, count] pairs to show for text columns. Five is enough to
# see the shape of a category column without flooding the context window.
TOP_VALUES_SHOWN = 5


class CsvError(Exception):
    def __init__(self, message: str, **extra):
        super().__init__(message)
        self.payload = {"error": message, **extra}


def load_rows(path: str) -> tuple[list[str], list[dict]]:
    file = Path(path)
    if not file.exists():
        raise CsvError(f"File not found: {path}", hint="Check the path relative to the current directory.")
    # utf-8-sig strips the BOM that Excel adds to exported CSVs.
    with file.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = reader.fieldnames or []
    if not columns:
        raise CsvError(f"No header row found in {path}.")
    return columns, rows


def to_number(text: str) -> float | None:
    try:
        return float(text.replace(",", "")) if text.strip() else None
    except ValueError:
        return None


def require_column(name: str, columns: list[str]) -> None:
    if name not in columns:
        raise CsvError(f"Unknown column '{name}'.", columns=columns)


def summary(path: str) -> dict:
    columns, rows = load_rows(path)
    described = []
    for name in columns:
        values = [(row.get(name) or "").strip() for row in rows]
        present = [v for v in values if v]
        numbers = [to_number(v) for v in present]
        info = {"name": name, "count": len(present), "missing": len(values) - len(present)}
        if present and all(n is not None for n in numbers):
            info.update(
                type="numeric",
                min=min(numbers),
                max=max(numbers),
                mean=round(statistics.fmean(numbers), 4),
                median=statistics.median(numbers),
            )
        else:
            counts = Counter(present)
            info.update(type="text", unique=len(counts), top_values=counts.most_common(TOP_VALUES_SHOWN))
        described.append(info)
    return {"file": path, "rows": len(rows), "columns": described}


AGGREGATIONS = {
    "sum": sum,
    "mean": lambda xs: round(statistics.fmean(xs), 4),
    "min": min,
    "max": max,
    "count": len,
}


def groupby(path: str, by: str, value: str, agg: str = "sum") -> dict:
    columns, rows = load_rows(path)
    require_column(by, columns)
    require_column(value, columns)
    if agg not in AGGREGATIONS:
        raise CsvError(f"Unknown aggregation '{agg}'.", valid=list(AGGREGATIONS))

    buckets: dict[str, list] = defaultdict(list)
    for row in rows:
        raw = (row.get(value) or "").strip()
        if agg == "count":
            buckets[row.get(by, "")].append(raw)
            continue
        number = to_number(raw)
        if raw and number is None:
            raise CsvError(f"Column '{value}' has non-numeric value '{raw}'.", hint="Use --agg count for text columns.")
        if number is not None:
            buckets[row.get(by, "")].append(number)

    key = f"{value}_{agg}"
    groups = [{by: group, key: AGGREGATIONS[agg](items)} for group, items in buckets.items() if items]
    groups.sort(key=lambda g: g[key], reverse=True)
    return {"by": by, "value": value, "agg": agg, "groups": groups}


def top(path: str, column: str, n: int = 5, ascending: bool = False) -> dict:
    columns, rows = load_rows(path)
    require_column(column, columns)
    scored = [(to_number(row.get(column) or ""), row) for row in rows]
    scored = [(score, row) for score, row in scored if score is not None]
    scored.sort(key=lambda pair: pair[0], reverse=not ascending)
    return {"column": column, "order": "asc" if ascending else "desc", "rows": [row for _, row in scored[:n]]}


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="Analyze a CSV file.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_summary = sub.add_parser("summary", help="column types and statistics")
    p_summary.add_argument("file")

    p_group = sub.add_parser("groupby", help="aggregate a column per group")
    p_group.add_argument("file")
    p_group.add_argument("--by", required=True)
    p_group.add_argument("--value", required=True)
    p_group.add_argument("--agg", default="sum", choices=list(AGGREGATIONS))

    p_top = sub.add_parser("top", help="top-N rows by a numeric column")
    p_top.add_argument("file")
    p_top.add_argument("--column", required=True)
    p_top.add_argument("--n", type=int, default=5)
    p_top.add_argument("--asc", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command == "summary":
            result = summary(args.file)
        elif args.command == "groupby":
            result = groupby(args.file, args.by, args.value, args.agg)
        else:
            result = top(args.file, args.column, args.n, args.asc)
    except CsvError as err:
        print(json.dumps(err.payload, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
