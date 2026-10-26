---
name: analyzing-excel
description: Reads Excel workbooks (.xlsx) with pandas - lists sheets and columns, summarizes a sheet (types, missing values, min/max/mean/sum, date ranges), and builds pivot tables with totals (for example amount by region and product). Use when the user asks about the contents, sheets, statistics, or a pivot of an .xlsx or Excel file. Not for .csv files (use analyzing-csv) or charts (use plotting-charts).
allowed-tools:
  - Bash(python *)
  - PowerShell(python *)
effort: low
---

# Analyzing Excel workbooks

The script uses pandas and openpyxl from the activated virtual environment.

## Workflow

1. List the sheets and their columns first:
   ```bash
   python "${CLAUDE_SKILL_DIR}/scripts/excel_tool.py" sheets data/sales.xlsx
   ```
2. Then, depending on the question:
   - Statistics for one sheet:
     ```bash
     python "${CLAUDE_SKILL_DIR}/scripts/excel_tool.py" summary data/sales.xlsx --sheet Sales
     ```
   - Pivot table with a Total row and column (`--columns` is optional, `--agg` is sum, mean, count, min or max):
     ```bash
     python "${CLAUDE_SKILL_DIR}/scripts/excel_tool.py" pivot data/sales.xlsx --sheet Sales --index region --columns product --values amount --agg sum
     ```
3. Report the numbers from the JSON output. Do not recompute them by hand.

Sheet and column names are case-sensitive. An `{"error": ...}` result lists the valid sheets or
columns - pick the right one and run again.

## If it fails

- `"Python package ... is not installed"`: Claude Code was started without the virtual environment.
  Do not install anything. Tell the user to exit, activate `C:\pyenvsmy\claudeclioct26`, and start
  `claude` again.
