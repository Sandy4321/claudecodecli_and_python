# csv_tool.py output reference

This file is loaded only when Claude needs the details (progressive disclosure, level 3).

## summary

```json
{
  "file": "data/sales.csv",
  "rows": 12,
  "columns": [
    {"name": "region", "type": "text", "count": 12, "missing": 0,
     "unique": 4, "top_values": [["North", 4], ["South", 3], ["East", 3], ["West", 2]]},
    {"name": "units", "type": "numeric", "count": 11, "missing": 1,
     "min": 1.0, "max": 20.0, "mean": 6.4545, "median": 5.0},
    {"name": "amount", "type": "numeric", "count": 12, "missing": 0,
     "min": 150.0, "max": 1200.0, "mean": 385.8333, "median": 285.0}
  ]
}
```

- A column is `numeric` when every non-empty value parses as a number.
- `missing` counts empty cells.
- `top_values` shows at most 5 `[value, count]` pairs, most frequent first.

## groupby

```json
{"by": "region", "value": "amount", "agg": "sum",
 "groups": [{"region": "North", "amount_sum": 2150.0}, {"region": "East", "amount_sum": 910.0},
            {"region": "West", "amount_sum": 900.0}, {"region": "South", "amount_sum": 670.0}]}
```

Groups are sorted by the aggregated value, largest first.
`count` works on any column; the other aggregations need a numeric `--value` column.

## top

```json
{"column": "amount", "order": "desc",
 "rows": [{"date": "2026-03-02", "region": "North", "product": "Gizmo", "units": "8", "amount": "1200"}]}
```

Rows are returned exactly as they appear in the file (strings).

## Errors

Every command returns `{"error": "...", ...}` with a non-zero exit code on bad input.
The extra fields (`columns`, `hint`) say how to fix the call.
