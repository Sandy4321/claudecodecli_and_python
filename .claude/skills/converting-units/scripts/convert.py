"""Converts values between units with exact factors. The script of the converting-units skill (Lessons 1 and 3).

WHAT
    Two commands:
        convert VALUE FROM TO   one conversion: length, mass, volume, speed, temperature or data size
        units                   the supported units, by category
    Common other names are accepted too: miles, kilometres, lbs, celsius, fahrenheit, kph, ...

WHY
    A language model can get a conversion slightly wrong; this script uses exact factors (one mile is
    1609.344 metres) and Python's arithmetic. The skill tells Claude to run it for every conversion.

HOW CLAUDE USES IT
    The converting-units SKILL.md tells Claude to run
        python "${CLAUDE_SKILL_DIR}/scripts/convert.py" convert 100 km mi
    Claude reads only the one line of JSON that the script prints, never this file.

HOW TO RUN IT YOURSELF  (in cmd, from the project folder)
    python .claude/skills/converting-units/scripts/convert.py convert 100 km mi
        {"value": 100.0, "from": "km", "to": "mi", "result": 62.137119, "category": "length"}
    python .claude/skills/converting-units/scripts/convert.py units
        {"length": ["mm", "cm", "m", "km", "in", "ft", "yd", "mi", "nmi"], "mass": [...], ...}
    python .claude/skills/converting-units/scripts/convert.py --help

ERRORS
    A wrong unit or category prints {"error": ..., "hint": ...} and ends with exit code 1, for example
        {"error": "Cannot convert length (km) to mass (kg).", "hint": "Valid length units: mm, cm, ..."}
    The hint tells Claude how to correct its command and try again.

HOW IT WORKS
    Each unit of a category has a factor to one base unit (metres, kilograms, litres, ...): the value is
    multiplied by the first factor and divided by the second. Temperatures go through kelvin, because
    they also have an offset. ALIASES maps the other names to the short ones.

ALSO USED BY
    tests/test_skill_scripts.py, which imports convert() directly (Lesson 5), and
    agent/custom_tools_agent.py, which offers convert() to Claude as a tool (Lesson 6, Part 2).

NEEDS
    Only the standard library. It never calls Claude.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k ConvertingUnits
       Expected (5 tests; the time differs):
           .....
           ----------------------------------------------------------------------
           Ran 5 tests in 0.328s

           OK
       What they check: exact factors for lengths, temperatures through kelvin, binary data units (GiB),
       error hints, and the command itself. Add -v to see the name of each test.
    2. By hand: free.
           python .claude/skills/converting-units/scripts/convert.py convert 1 mi km
               {"value": 1.0, "from": "mi", "to": "km", "result": 1.609344, "category": "length"}
           python .claude/skills/converting-units/scripts/convert.py convert 5 km kg
               {"error": "Cannot convert length (km) to mass (kg).", "hint": "Valid length units: mm, cm, m, km, in, ft, yd, mi, nmi"}
           echo %errorlevel%
               1          (0 after a good conversion, 1 after an error)
    3. With Claude: uses a little Pro allowance.
           claude -p "Convert 1 mile to km." --model haiku --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)"
               Expected: an answer with 1.609344 km. A real run: "1 mile = **1.609 km** (exactly 1.609344 km)."

IF SOMETHING GOES WRONG
    - {"error": "Unknown unit 'parsec'.", "hint": "Run the 'units' command to see valid units."}: the unit
      is not in LINEAR_UNITS or ALIASES. To accept a new name, add it to ALIASES.
    - "python" is not recognized, or the Microsoft Store opens: activate the venv first (Lesson 0).
    - A test fails after you changed a factor: Lesson 5, Step 2 shows how to read the failure.

FILES IT READS AND WRITES
    None: it reads only its arguments, and writes only to the screen (stdout).

SEE ALSO
    converting-units/SKILL.md (how Claude is told to run this script); tests/test_skill_scripts.py,
    class ConvertingUnits; agent/custom_tools_agent.py and agent/tutor_mcp_server.py (convert() as a
    tool); Lesson 1, Step 4; Lesson 3, Part 1; Lesson 5, Step 2.
"""

import argparse
import json
import sys

# Every linear unit is stored as "how many base units is 1 of this unit".
# Base units: meter, kilogram, liter, meter/second, byte.
LINEAR_UNITS = {
    "length": {
        "mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0,
        "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mi": 1609.344, "nmi": 1852.0,
    },
    "mass": {
        "mg": 1e-6, "g": 0.001, "kg": 1.0, "t": 1000.0,
        "oz": 0.028349523125, "lb": 0.45359237, "st": 6.35029318,
    },
    "volume": {
        "ml": 0.001, "l": 1.0, "m3": 1000.0,
        "tsp": 0.00492892159375, "tbsp": 0.01478676478125, "cup": 0.2365882365,
        "pt": 0.473176473, "qt": 0.946352946, "gal": 3.785411784, "floz": 0.0295735295625,
    },
    "speed": {
        "m/s": 1.0, "km/h": 1000.0 / 3600.0, "mph": 1609.344 / 3600.0, "kn": 1852.0 / 3600.0,
    },
    "data": {
        "b": 1.0, "kb": 1e3, "mb": 1e6, "gb": 1e9, "tb": 1e12,
        "kib": 1024.0, "mib": 1024.0**2, "gib": 1024.0**3, "tib": 1024.0**4,
    },
}

TEMPERATURE_UNITS = ("c", "f", "k")

# Words people actually type -> canonical unit key.
ALIASES = {
    "meter": "m", "meters": "m", "metre": "m", "metres": "m",
    "kilometer": "km", "kilometers": "km", "kilometre": "km", "kilometres": "km",
    "centimeter": "cm", "centimeters": "cm", "millimeter": "mm", "millimeters": "mm",
    "inch": "in", "inches": "in", "foot": "ft", "feet": "ft", "yard": "yd", "yards": "yd",
    "mile": "mi", "miles": "mi",
    "gram": "g", "grams": "g", "kilogram": "kg", "kilograms": "kg", "kgs": "kg",
    "tonne": "t", "tonnes": "t", "ounce": "oz", "ounces": "oz",
    "pound": "lb", "pounds": "lb", "lbs": "lb", "stone": "st",
    "liter": "l", "liters": "l", "litre": "l", "litres": "l",
    "milliliter": "ml", "milliliters": "ml", "gallon": "gal", "gallons": "gal",
    "cups": "cup", "pint": "pt", "pints": "pt", "quart": "qt", "quarts": "qt",
    "kph": "km/h", "kmh": "km/h", "knot": "kn", "knots": "kn", "mps": "m/s",
    "celsius": "c", "°c": "c", "fahrenheit": "f", "°f": "f", "kelvin": "k",
    "byte": "b", "bytes": "b",
}


def normalize(unit: str) -> str:
    u = unit.strip().lower()
    return ALIASES.get(u, u)


def category_of(unit: str) -> str | None:
    if unit in TEMPERATURE_UNITS:
        return "temperature"
    for category, table in LINEAR_UNITS.items():
        if unit in table:
            return category
    return None


def _to_kelvin(value: float, unit: str) -> float:
    if unit == "c":
        return value + 273.15
    if unit == "f":
        return (value - 32.0) * 5.0 / 9.0 + 273.15
    return value


def _from_kelvin(value: float, unit: str) -> float:
    if unit == "c":
        return value - 273.15
    if unit == "f":
        return (value - 273.15) * 9.0 / 5.0 + 32.0
    return value


def convert(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert `value` from `from_unit` to `to_unit`. Returns a JSON-ready dict.

    Errors are returned as {"error": "..."} with a hint, never raised, so the
    agent can read the message and retry ("solve, don't punt").
    """
    src, dst = normalize(from_unit), normalize(to_unit)
    src_cat, dst_cat = category_of(src), category_of(dst)

    if src_cat is None or dst_cat is None:
        bad = from_unit if src_cat is None else to_unit
        return {"error": f"Unknown unit '{bad}'.", "hint": "Run the 'units' command to see valid units."}
    if src_cat != dst_cat:
        return {
            "error": f"Cannot convert {src_cat} ({from_unit}) to {dst_cat} ({to_unit}).",
            "hint": f"Valid {src_cat} units: {', '.join(list_units()[src_cat])}",
        }

    if src_cat == "temperature":
        result = _from_kelvin(_to_kelvin(value, src), dst)
    else:
        table = LINEAR_UNITS[src_cat]
        result = value * table[src] / table[dst]

    return {"value": value, "from": src, "to": dst, "result": round(result, 6), "category": src_cat}


def list_units() -> dict:
    units = {category: list(table) for category, table in LINEAR_UNITS.items()}
    units["temperature"] = list(TEMPERATURE_UNITS)
    return units


def _print_json(data) -> None:
    print(json.dumps(data, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="Convert between units.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_convert = sub.add_parser("convert", help="convert VALUE FROM TO")
    p_convert.add_argument("value", type=float)
    p_convert.add_argument("from_unit")
    p_convert.add_argument("to_unit")

    sub.add_parser("units", help="list supported units by category")

    args = parser.parse_args(argv)
    if args.command == "convert":
        result = convert(args.value, args.from_unit, args.to_unit)
        _print_json(result)
        return 1 if "error" in result else 0
    _print_json(list_units())
    return 0


if __name__ == "__main__":
    sys.exit(main())
