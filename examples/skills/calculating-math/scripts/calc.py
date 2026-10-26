"""A strict calculator: arithmetic, square roots, sine and cosine. The script of the calculating-math example skill (Lesson 8).

WHAT
    One command:  calc.py OPERATION NUMBER [NUMBER] [--unit degrees|radians]
        add, subtract, multiply, divide     two numbers (subtract and divide: the first by the second)
        sqrt                                one number
        sin, cos                            one number, and --unit is required
    Other common names work too: plus, minus, times, sum, root, sine, sinus, cosine, ...

WHY
    The script is strict on purpose: numbers as digits, a known operation, and an explicit unit for
    sin and cos. Users write messy text, such as "seven and five add" or "4 radnias sinus". Claude
    turns that text into this strict form; the script does the arithmetic exactly. Each part does
    what it does best (Lesson 8).

HOW CLAUDE USES IT
    The calculating-math SKILL.md has a table "The user writes / Command" with examples of messy text,
    and tells Claude to run
        python "${CLAUDE_SKILL_DIR}/scripts/calc.py" <operation> <number> [<number>] [--unit degrees|radians]
    The skill is in examples/skills/, so Claude doesn't load it until you copy the folder into
    .claude/skills/ (Lesson 8, Step 1).

HOW TO RUN IT YOURSELF  (in cmd, from the project folder)
    python examples/skills/calculating-math/scripts/calc.py add 7 5
        {"operation": "add", "numbers": [7.0, 5.0], "unit": null, "result": 12.0}
    python examples/skills/calculating-math/scripts/calc.py divide 7 5
    python examples/skills/calculating-math/scripts/calc.py sqrt 45
    python examples/skills/calculating-math/scripts/calc.py sinus 30 --unit degrees
        {"operation": "sin", "numbers": [30.0], "unit": "degrees", "result": 0.5}

ERRORS
    A problem prints {"error": ..., "hint": ...} with exit code 1. The hint tells Claude what to do:
        calc.py sin 3     ->  {"error": "'sin' needs --unit degrees or --unit radians.",
                               "hint": "If the user gave no unit, use degrees and say so in the answer."}
        calc.py divide 7 0  ->  {"error": "Division by zero.", "hint": "Ask the user for a divisor other than 0."}

HOW IT WORKS
    calculate(operation, numbers, unit) does the work, so the tests can call it directly
    (CalculatingMath in tests/test_skill_scripts.py). OPERATIONS maps each operation to its function and
    number of inputs; ALIASES maps the other names to the operations.

NEEDS
    Only the standard library. It never calls Claude.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k CalculatingMath
       Expected (5 tests; the time differs):
           .....
           ----------------------------------------------------------------------
           Ran 5 tests in 0.195s

           OK
       What they check: the order of subtract and divide, sqrt, sin and cos with units, the other
       operation names, and the error hints for Claude. Add -v to see the name of each test.
    2. By hand: free.
           python examples/skills/calculating-math/scripts/calc.py times 6 7
               {"operation": "multiply", "numbers": [6.0, 7.0], "unit": null, "result": 42.0}
           python examples/skills/calculating-math/scripts/calc.py divide 7 0
               {"error": "Division by zero.", "hint": "Ask the user for a divisor other than 0."}       (exit code 1)
    3. With Claude: uses a little Pro allowance.
           The skill is in examples/skills/, so Claude doesn't see it until you copy it into .claude/skills/.
           Lesson 8 does that (Step 1), and shows nine real claude -p runs with messy input (Step 4).

IF SOMETHING GOES WRONG
    - {"error": "Unknown operation 'power'.", "hint": "Use one of: add, subtract, ..."}: add the new name to
      OPERATIONS (a new operation) or to ALIASES (another name for an existing one).
    - {"error": "Not a number: ['seven', '5'].", ...}: the script wants digits; turning words into digits is
      Claude's job.

FILES IT READS AND WRITES
    None.

SEE ALSO
    examples/skills/calculating-math/SKILL.md; Lesson 8.
"""

import argparse
import json
import math
import sys

# Every operation: how many numbers it takes, and the function that computes it.
OPERATIONS = {
    "add": (2, lambda a, b: a + b),
    "subtract": (2, lambda a, b: a - b),
    "multiply": (2, lambda a, b: a * b),
    "divide": (2, lambda a, b: a / b),
    "sqrt": (1, math.sqrt),
    "sin": (1, math.sin),
    "cos": (1, math.cos),
}
ALIASES = {
    "plus": "add", "sum": "add",
    "minus": "subtract", "sub": "subtract",
    "times": "multiply", "mul": "multiply", "product": "multiply",
    "div": "divide", "over": "divide",
    "root": "sqrt", "square-root": "sqrt", "squareroot": "sqrt",
    "sine": "sin", "sinus": "sin",
    "cosine": "cos", "cosinus": "cos",
}
UNITS = ("degrees", "radians")


def calculate(operation: str, numbers: list[str], unit: str | None = None) -> dict:
    """Return {"operation", "numbers", "unit", "result"}, or {"error", "hint"} for a call to fix."""
    name = ALIASES.get(operation.lower(), operation.lower())
    if name not in OPERATIONS:
        return {"error": f"Unknown operation '{operation}'.", "hint": f"Use one of: {', '.join(OPERATIONS)}."}
    count, function = OPERATIONS[name]
    if len(numbers) != count:
        return {"error": f"'{name}' takes {count} number(s), got {len(numbers)}.",
                "hint": "Pass exactly the numbers of the request, in the order the operation needs."}
    try:
        values = [float(n) for n in numbers]
    except ValueError:
        return {"error": f"Not a number: {numbers}.", "hint": "Write numbers as digits: 'seven' -> 7, 'twenty-three' -> 23."}

    if name in ("sin", "cos"):
        if unit not in UNITS:
            return {"error": f"'{name}' needs --unit degrees or --unit radians.",
                    "hint": "If the user gave no unit, use degrees and say so in the answer."}
        angle = math.radians(values[0]) if unit == "degrees" else values[0]
        result = function(angle)
    elif name == "divide" and values[1] == 0:
        return {"error": "Division by zero.", "hint": "Ask the user for a divisor other than 0."}
    elif name == "sqrt" and values[0] < 0:
        return {"error": f"No real square root of {values[0]:g}.", "hint": "Tell the user; only numbers >= 0 have one."}
    else:
        result = function(*values)

    # round() hides float noise such as cos(90 degrees) = 6.123e-17.
    return {"operation": name, "numbers": values, "unit": unit if name in ("sin", "cos") else None,
            "result": round(result, 10)}


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    parser = argparse.ArgumentParser(description="Basic arithmetic and trigonometry.")
    parser.add_argument("operation", help="add, subtract, multiply, divide, sqrt, sin, cos (or plus, times, sinus, ...)")
    parser.add_argument("numbers", nargs="+", help="one or two numbers, as digits")
    parser.add_argument("--unit", choices=UNITS, help="for sin and cos")
    args = parser.parse_args(argv)
    result = calculate(args.operation, args.numbers, args.unit)
    print(json.dumps(result))
    return 1 if "error" in result else 0


if __name__ == "__main__":
    sys.exit(main())
