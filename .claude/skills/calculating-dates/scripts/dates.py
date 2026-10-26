"""Days between dates, working days, weekdays and ages. The script of the calculating-dates skill (Lesson 3, Pattern B).

WHAT
    Six functions, each one a command (Python names with underscores, parameters as --options):
        days_between --start DATE --end DATE                       calendar days from start to end
        add_days --date DATE --days N                              a date plus (or minus) N days
        add_business_days --date DATE --days N [--holidays LIST]   plus N working days (Monday to
                                                                   Friday, without the holidays)
        business_days_between --start DATE --end DATE [--holidays LIST]   working days in a range
        weekday --date DATE                                        the day of the week and ISO week
        age --birthdate DATE [--on DATE]                           age in years, today or on a date
    Dates are YYYY-MM-DD; LIST is comma-separated dates, for example 2026-11-26,2026-12-25.

WHY
    "What date is 10 working days after October 15?" is easy to get wrong in your head, and for a
    language model too. Python's datetime module gets it right.

HOW CLAUDE USES IT
    The calculating-dates SKILL.md has a table with one command per function, and tells Claude to run
    --list when it needs something else. Claude reads only the JSON that the script prints.

HOW TO RUN IT YOURSELF  (in cmd, from the project folder)
    python .claude/skills/calculating-dates/scripts/dates.py --list
    python .claude/skills/calculating-dates/scripts/dates.py add_business_days --date 2026-10-15 --days 10
        {"date": "2026-10-15", "business_days": 10, "result": "2026-10-29", "weekday": "Thursday"}
    python .claude/skills/calculating-dates/scripts/dates.py weekday --date 2026-12-25
        {"date": "2026-12-25", "weekday": "Friday", "iso_week": 52}
    python .claude/skills/calculating-dates/scripts/dates.py add_business_days --help

ERRORS
    A wrong date prints {"error": ..., "function": ..., "signature": ...} with exit code 1:
        {"error": "date must be an ISO date like 2026-10-15, got '2026-02-30'", "function": "add_days", ...}

HOW IT WORKS
    The functions are plain Python with type hints and docstrings. The last lines hand them to
    fncli.run() (fncli.py, in this folder), which builds the command line from them: no argparse code
    here. To add a command, write a function and add it to the PUBLIC list (Lesson 3, Step B4).
    The same functions are offered to Claude as tools in agent/custom_tools_agent.py (Lesson 6, Part 2).

NEEDS
    Only the standard library and fncli.py. It never calls Claude.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k CalculatingDates
       Expected (5 tests; the time differs):
           .....
           ----------------------------------------------------------------------
           Ran 5 tests in 0.608s

           OK
       What they check: working days that skip weekends and holidays, working days in a range, ages
       before and after a birthday, and calling functions by name through fncli. Add -v to see the name
       of each test.
    2. By hand: free.
           python .claude/skills/calculating-dates/scripts/dates.py days_between --start 2026-01-01 --end 2026-12-25
               {"start": "2026-01-01", "end": "2026-12-25", "days": 358, "weeks": 51.14}
           python .claude/skills/calculating-dates/scripts/dates.py add_days --date 2026-10-15
               usage: dates.py add_days [-h] --date DATE --days DAYS
               dates.py add_days: error: the following arguments are required: --days       (exit code 2)
    3. With Claude: uses a little Pro allowance.
           claude -p "How many days are there from 2026-01-01 to 2026-12-25?" --model haiku --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)"
               Expected: 358 days.

IF SOMETHING GOES WRONG
    - {"error": "date must be an ISO date like 2026-10-15, got ...", ...}: dates are YYYY-MM-DD.
    - The option names are the parameter names, with underscores: --birthdate, --start, --end.
    - Your new function is not a command: add it to the PUBLIC list at the end of the file.

FILES IT READS AND WRITES
    None.

SEE ALSO
    fncli.py (builds the command line); calculating-dates/SKILL.md; Lesson 3, Pattern B (Steps B1 to
    B4).
"""

import datetime as dt
from datetime import timedelta

import fncli

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _parse(text: str, field: str) -> dt.date:
    try:
        return dt.date.fromisoformat(text.strip())
    except ValueError:
        raise ValueError(f"{field} must be an ISO date like 2026-10-15, got '{text}'") from None


def _holidays(text: str) -> set[dt.date]:
    return {_parse(item, "holidays") for item in text.split(",") if item.strip()}


def _is_business_day(day: dt.date, holidays: set[dt.date]) -> bool:
    return day.weekday() < 5 and day not in holidays


def days_between(start: str, end: str) -> dict:
    """Calendar days from start to end (negative if end is earlier). Dates are YYYY-MM-DD."""
    d1, d2 = _parse(start, "start"), _parse(end, "end")
    delta = (d2 - d1).days
    return {"start": d1, "end": d2, "days": delta, "weeks": round(delta / 7, 2)}


def add_days(date: str, days: int) -> dict:
    """Add (or subtract, if negative) calendar days to a date."""
    base = _parse(date, "date")
    result = base + timedelta(days=days)
    return {"date": base, "days": days, "result": result, "weekday": WEEKDAY_NAMES[result.weekday()]}


def add_business_days(date: str, days: int, holidays: str = "") -> dict:
    """Add business days (Mon-Fri), skipping comma-separated holiday dates. Days must be >= 0."""
    if days < 0:
        raise ValueError("days must be zero or positive for add_business_days")
    base, skip = _parse(date, "date"), _holidays(holidays)
    current, remaining = base, days
    while remaining > 0:
        current += timedelta(days=1)
        if _is_business_day(current, skip):
            remaining -= 1
    return {"date": base, "business_days": days, "result": current, "weekday": WEEKDAY_NAMES[current.weekday()]}


def business_days_between(start: str, end: str, holidays: str = "") -> dict:
    """Count business days after start up to and including end, skipping weekends and holidays."""
    d1, d2, skip = _parse(start, "start"), _parse(end, "end"), _holidays(holidays)
    if d2 < d1:
        raise ValueError("end must be on or after start")
    count = sum(1 for offset in range(1, (d2 - d1).days + 1) if _is_business_day(d1 + timedelta(days=offset), skip))
    return {"start": d1, "end": d2, "business_days": count}


def weekday(date: str) -> dict:
    """Day of the week and ISO week number for a date."""
    day = _parse(date, "date")
    return {"date": day, "weekday": WEEKDAY_NAMES[day.weekday()], "iso_week": day.isocalendar().week}


def age(birthdate: str, on: str = "") -> dict:
    """Age in whole years on a given date (default: today)."""
    born = _parse(birthdate, "birthdate")
    today = _parse(on, "on") if on else dt.date.today()
    if today < born:
        raise ValueError("'on' date is before the birthdate")
    years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return {"birthdate": born, "on": today, "years": years}


PUBLIC = [days_between, add_days, add_business_days, business_days_between, weekday, age]

if __name__ == "__main__":
    fncli.run(PUBLIC)
