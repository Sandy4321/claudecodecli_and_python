---
name: plotting-charts
description: Draws bar and line charts as PNG images from .csv or .xlsx data with matplotlib - totals or averages per category, and values over time grouped by day, week or month. Use when the user asks for a chart, graph, plot, or picture of data in a CSV or Excel file. Not for numeric answers without a picture (use analyzing-csv or analyzing-excel).
allowed-tools:
  - Bash(python *)
  - PowerShell(python *)
effort: medium
---

# Plotting charts

The script uses pandas and matplotlib from the activated virtual environment.

## Bar chart: one value per category

```bash
python "${CLAUDE_SKILL_DIR}/scripts/chart.py" bar data/sales.csv --x region --y amount --agg sum
```

## Line chart: values over time

```bash
python "${CLAUDE_SKILL_DIR}/scripts/chart.py" line data/sales.csv --x date --y amount --agg sum --freq M
```

`--freq` groups dates by `D` (day), `W` (week) or `M` (month). Leave it out to plot each x value as is.

Common options: `--agg` (sum, mean, count, min, max), `--sheet NAME` for .xlsx files, `--title "..."`,
`--out charts/name.png`. The default output is `charts/<kind>_<y>_by_<x>.png`.

## After the chart is written

1. The JSON output has `written` (the PNG path) and `points` (the plotted numbers).
2. Open the PNG with the Read tool and check that it shows what the user asked for.
3. Tell the user the file path and the two or three most important numbers from `points`.

## If it fails

- `"Python package ... is not installed"`: Claude Code was started without the virtual environment.
  Do not install anything. Tell the user to exit, activate `C:\pyenvsmy\claudeclioct26`, and start
  `claude` again.
- An unknown column or sheet returns an error that lists the valid names. Fix the argument and rerun.
