---
name: calculating-dates
description: Calculates with calendar dates - days or weeks between two dates, adding days, adding or counting business days (skipping weekends and holidays), day of the week, ISO week number, and age from a birthdate. Use when the user asks about deadlines, due dates, "how many days until", working days, or what weekday a date falls on.
allowed-tools:
  - Bash(python *)
  - PowerShell(python *)
effort: high
---

# Calculating dates

Date math is easy to get wrong by one day. Always run the script.

Each Python function in `scripts/dates.py` is a subcommand; each parameter is a `--flag`.
Dates are ISO format `YYYY-MM-DD`. If the user gives "today" or a relative date, resolve it
to an ISO date first.

| Question | Command |
|---|---|
| Days between two dates | `python "${CLAUDE_SKILL_DIR}/scripts/dates.py" days_between --start 2026-01-01 --end 2026-12-25` |
| Date + N days | `python "${CLAUDE_SKILL_DIR}/scripts/dates.py" add_days --date 2026-10-15 --days 30` |
| Date + N working days | `python "${CLAUDE_SKILL_DIR}/scripts/dates.py" add_business_days --date 2026-10-15 --days 10 --holidays 2026-11-26` |
| Working days in a range | `python "${CLAUDE_SKILL_DIR}/scripts/dates.py" business_days_between --start 2026-10-01 --end 2026-10-31` |
| Weekday / ISO week | `python "${CLAUDE_SKILL_DIR}/scripts/dates.py" weekday --date 2026-12-25` |
| Age | `python "${CLAUDE_SKILL_DIR}/scripts/dates.py" age --birthdate 1990-05-17` |

`--holidays` takes comma-separated ISO dates and is optional.

If you need a function that is not in the table, list them all with their docstrings:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/dates.py" --list
```

Output is JSON. An `{"error": ...}` result explains which argument was wrong - fix it and rerun.
