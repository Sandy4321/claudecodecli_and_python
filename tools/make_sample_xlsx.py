"""Makes the sample workbook data/sales.xlsx from data/sales.csv (used in Lessons 3 and 7).

WHAT
    Writes data/sales.xlsx with two sheets: "Sales" (the 12 rows of data/sales.csv) and "Targets"
    (a sales target per region). The analyzing-excel and plotting-charts skills read this file.

WHY
    The project already contains data/sales.xlsx. Run this only if you deleted or changed it, or
    changed data/sales.csv and want the workbook to match.

HOW IT WORKS
    pandas reads the CSV (the "date" column as dates), builds the Targets table, and writes both
    sheets with the openpyxl engine.

HOW TO RUN  (in cmd, from the project folder, with the venv activated)
    python tools/make_sample_xlsx.py
    It prints: Wrote .../data/sales.xlsx
    python tools/make_sample_xlsx.py practice.xlsx       (another file; data/sales.xlsx stays as it is)

NEEDS
    pandas and openpyxl, so the activated venv (Lesson 7). With the system Python it stops with
    ModuleNotFoundError.

WHICH WAY TO REACH CLAUDE
    None: it never calls Claude, and costs nothing.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k make_sample_xlsx
       Expected (1 test; the time differs):
           .
           ----------------------------------------------------------------------
           Ran 1 test in 3.936s

           OK
       What it checks: that the workbook gets the sheets Sales (12 rows) and Targets (4 rows); it
       writes a temporary file, never data/sales.xlsx. Add -v to see the name of each test.
    2. By hand: free.
           python tools/make_sample_xlsx.py %TEMP%/check.xlsx
               Wrote C:/Users/<you>/AppData/Local/Temp/check.xlsx
           python .claude/skills/analyzing-excel/scripts/excel_tool.py sheets %TEMP%/check.xlsx
               {"file": ".../check.xlsx", "sheets": [{"sheet": "Sales", "rows": 12, ...}, {"sheet": "Targets", "rows": 4, ...}]}

IF SOMETHING GOES WRONG
    - ModuleNotFoundError: No module named 'pandas': activate the venv.
    - PermissionError: data/sales.xlsx is open in Excel; close it there first.

FILES IT READS AND WRITES
    Reads data/sales.csv. Writes data/sales.xlsx, or the file you name.

SEE ALSO
    excel_tool.py and chart.py (read the workbook); Lesson 7.
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

sales = pd.read_csv(ROOT / "data" / "sales.csv", parse_dates=["date"])
targets = pd.DataFrame({"region": ["North", "South", "East", "West"], "target": [2000, 800, 1000, 1000]})

out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "sales.xlsx"   # the tests write a temporary file
with pd.ExcelWriter(out, engine="openpyxl") as writer:
    sales.to_excel(writer, sheet_name="Sales", index=False)
    targets.to_excel(writer, sheet_name="Targets", index=False)
print(f"Wrote {out}")
