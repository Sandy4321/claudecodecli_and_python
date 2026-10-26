---
name: analyzing-csv
description: Summarizes and aggregates tabular data in .csv files - column types, missing values, min/max/mean/median, group-by totals and averages, top-N rows by a column. Use when the user asks about the contents, statistics, totals, or rankings in a CSV file. Not for .xlsx workbooks (use analyzing-excel), charts (use plotting-charts), or prose .txt documents (use analyzing-text).
allowed-tools:
  - Bash(python *)
  - PowerShell(python *)
effort: low
---

# Analyzing CSV files

Use the bundled script instead of reading the whole CSV into context.
It uses only the Python standard library, so nothing needs installing.

## Workflow

1. **Always start with a summary** so you know the real column names and types:
   ```bash
   python "${CLAUDE_SKILL_DIR}/scripts/csv_tool.py" summary data/sales.csv
   ```
2. Then answer the question with one of:
   - Totals or averages per category:
     ```bash
     python "${CLAUDE_SKILL_DIR}/scripts/csv_tool.py" groupby data/sales.csv --by region --value amount --agg sum
     ```
     `--agg` is one of `sum`, `mean`, `count`, `min`, `max`.
   - Largest or smallest rows:
     ```bash
     python "${CLAUDE_SKILL_DIR}/scripts/csv_tool.py" top data/sales.csv --column amount --n 5
     ```
     Add `--asc` for the smallest.
3. Report numbers from the JSON output. Do not recompute them by hand.

Column names are case-sensitive. If you get `"error": "Unknown column"`, the error lists
the valid columns - pick the right one and run again.

For the exact JSON shape of each command, see [reference.md](reference.md).
