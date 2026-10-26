"""fncli: turns plain Python functions into a command line, so a SKILL.md can call them by name (Lesson 3, Pattern B).

WHAT
    run([func_a, func_b]) makes one command per function, and one --option per parameter. It prints
    each function's return value as JSON. --list prints the names, signatures and docstrings of all
    functions as JSON.

WHY
    Writing argparse code for every function is repetitive, and easy to get out of step with the
    functions. With fncli you write normal typed functions, and the command line follows them. --list
    lets Claude find a function the SKILL.md doesn't mention, without reading the code.

HOW TO USE IT  (in your own script, next to fncli.py)
    import fncli

    def add_days(date: str, days: int) -> dict:
        "Add (or subtract, if negative) calendar days to a date."
        ...

    if __name__ == "__main__":
        fncli.run([add_days])

    Then:  python dates.py add_days --date 2026-10-15 --days 30
           python dates.py --list
           python dates.py add_days --help         (the help comes from the docstring)

HOW IT WORKS
    inspect.signature() lists the parameters of each function. Each one becomes --name (underscores
    stay), converted with its type hint: int, float, str, or bool (true/false, yes/no, 1/0). A
    parameter without a default is required. A ValueError raised by your function becomes
    {"error": ..., "function": ..., "signature": ...} with exit code 1, so Claude can read what went
    wrong and try again.

NEEDS
    Only the standard library. It never calls Claude. Used by dates.py.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k fncli
       Expected (2 tests; the time differs):
           ..
           ----------------------------------------------------------------------
           Ran 2 tests in 0.635s

           OK
       What they check: calling a function by its name with typed options, and the JSON error with the
       function's signature after bad input. Add -v to see the name of each test.
    2. By hand: free.
           python .claude/skills/calculating-dates/scripts/dates.py add_days --help
               usage: dates.py add_days [-h] --date DATE --days DAYS

               Add (or subtract, if negative) calendar days to a date.

               options:
                 -h, --help   show this help message and exit
                 --date DATE
                 --days DAYS
               (fncli made this help from the function's parameters and its docstring.)
    3. With Claude: uses a little Pro allowance.
           See dates.py: every Claude run of that skill goes through fncli.

IF SOMETHING GOES WRONG
    - A parameter without a type hint, or with a type other than int, float, str or bool, arrives as text.
    - Only ValueError becomes a JSON error. Any other exception stops with a traceback, so check the input
      and raise ValueError with a clear message.

FILES IT READS AND WRITES
    None.

SEE ALSO
    dates.py (uses it); Lesson 3, Steps B2 and B4.
"""

import argparse
import inspect
import json
import sys
from typing import Callable

_PARSERS = {int: int, float: float, str: str}


def _parse_bool(text: str) -> bool:
    if text.lower() in ("1", "true", "yes", "y", "on"):
        return True
    if text.lower() in ("0", "false", "no", "n", "off"):
        return False
    raise argparse.ArgumentTypeError(f"expected true/false, got '{text}'")


def describe(functions: list[Callable]) -> list[dict]:
    return [
        {"name": fn.__name__, "signature": f"{fn.__name__}{inspect.signature(fn)}", "doc": inspect.getdoc(fn) or ""}
        for fn in functions
    ]


def run(functions: list[Callable], argv: list[str] | None = None) -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description=inspect.getdoc(sys.modules["__main__"]) or None)
    parser.add_argument("--list", action="store_true", help="list functions as JSON and exit")
    sub = parser.add_subparsers(dest="function")

    by_name = {fn.__name__: fn for fn in functions}
    for fn in functions:
        doc = inspect.getdoc(fn) or ""
        cmd = sub.add_parser(fn.__name__, help=doc.splitlines()[0] if doc else None, description=doc)
        for param in inspect.signature(fn).parameters.values():
            annotation = param.annotation if param.annotation is not inspect.Parameter.empty else str
            convert = _parse_bool if annotation is bool else _PARSERS.get(annotation, str)
            flag = "--" + param.name
            if param.default is inspect.Parameter.empty:
                cmd.add_argument(flag, dest=param.name, type=convert, required=True)
            else:
                cmd.add_argument(flag, dest=param.name, type=convert, default=param.default)

    args = parser.parse_args(argv)
    if args.list or not args.function:
        print(json.dumps(describe(functions), indent=2, ensure_ascii=False))
        return

    fn = by_name[args.function]
    kwargs = {name: value for name, value in vars(args).items() if name not in ("list", "function")}
    try:
        result = fn(**kwargs)
    except ValueError as err:
        print(json.dumps({"error": str(err), "function": fn.__name__, "signature": describe([fn])[0]["signature"]}))
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, default=str))
