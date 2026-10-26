"""Checks, totals and writes invoices from a JSON file. The script of the calculating-invoices skill (Lesson 3, Pattern C).

WHAT
    Three commands, in this order:
        validate FILE           lists every problem of the invoice; {"ok": true} if there is none
        total FILE              the amount of each line, the subtotal, discount, tax and total
        render FILE --out MD    writes the invoice as a Markdown document
    The JSON has: number, customer, currency, discount_pct, tax_pct, items (each with description,
    qty and unit_price), and notes. data/invoice.json is a correct example; data/invoice_broken.json
    has 5 mistakes.

WHY
    Money must be exact to the cent, and a broken invoice must never be totalled. That is the pattern
    "plan, check, then do": the script checks the data first, and refuses to calculate wrong data.

HOW CLAUDE USES IT
    The calculating-invoices SKILL.md tells Claude to write the items into a file such as
    invoice.json, run validate, fix every listed problem and validate again, and only then run total
    (and render, if you want a document). Claude reads only the JSON that the script prints.

HOW TO RUN IT YOURSELF  (in cmd, from the project folder)
    python .claude/skills/calculating-invoices/scripts/invoice.py validate data/invoice_broken.json
        {"ok": false, "problems": ["items[0].qty must be a number greater than 0, got 0.", ...]}
    python .claude/skills/calculating-invoices/scripts/invoice.py total data/invoice.json
        {"currency": "USD", "lines": [...], "subtotal": "1440.47", "discount": "144.05",
         "tax": "106.95", "total": "1403.37"}
    python .claude/skills/calculating-invoices/scripts/invoice.py render data/invoice.json --out invoice.md

ERRORS AND EXIT CODES
    validate ends with exit code 1 when it found problems. total and render refuse an invalid invoice:
    they print {"error": "Invoice is invalid; run validate first: ..."} with exit code 1.

HOW IT WORKS
    Decimal instead of float: 0.1 + 0.2 is exactly 0.3, and money() rounds to cents half up, the way
    invoices are rounded. The discount is taken from the subtotal, and the tax from the discounted
    amount.

NEEDS
    Only the standard library. It never calls Claude.

HOW TO TEST
    1. Unit tests: free, no Claude. In cmd, from the project folder, with the venv activated:
           python -m unittest discover -s tests -k CalculatingInvoices
       Expected (3 tests; the time differs):
           ...
           ----------------------------------------------------------------------
           Ran 3 tests in 0.202s

           OK
       What they check: cent rounding of totals, all 5 problems of data/invoice_broken.json, and the
       Markdown document. Add -v to see the name of each test.
    2. By hand: free.
           python .claude/skills/calculating-invoices/scripts/invoice.py total data/invoice.json
               {"currency": "USD", "lines": [...], "subtotal": "1440.47", "discount": "144.05", "tax": "106.95", "total": "1403.37"}
           python .claude/skills/calculating-invoices/scripts/invoice.py total data/invoice_broken.json
               {"error": "Invoice is invalid; run validate first: items[0].qty must be a number greater than 0, got 0. ..."}
               (exit code 1: a broken invoice is never totalled)
    3. With Claude: uses a little Pro allowance.
           claude -p "What is the grand total of the invoice in data/invoice.json?" --model haiku --allowedTools "Skill,Read,Bash(python *),PowerShell(python *)"
               Expected: 1403.37 USD, the script's answer. In the real run Haiku did not run the script: it did
               the math itself, and answered 1,403.36, one cent off. That is exactly why the script exists. If you
               see this, start the skill yourself (/calculating-invoices), or use a stronger model.

IF SOMETHING GOES WRONG
    - {"error": "Invalid JSON in ...: line 2, column 1: Expecting value"}: the file is not valid JSON; the
      line and column show where.
    - "Invoice is invalid; run validate first": run validate, and fix every problem it lists.

FILES IT READS AND WRITES
    Reads the invoice JSON file. render writes the --out file (invoice.md is ignored by git).

SEE ALSO
    calculating-invoices/SKILL.md; data/invoice.json and data/invoice_broken.json; Lesson 3, Pattern C.
"""

import argparse
import json
import sys
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def load(path: str) -> dict:
    file = Path(path)
    if not file.exists():
        raise ValueError(f"File not found: {path}")
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise ValueError(f"Invalid JSON in {path}: line {err.lineno}, column {err.colno}: {err.msg}") from None


def _decimal(value) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def validate(invoice: dict) -> dict:
    """Return {"ok": bool, "problems": [...]}. Messages say exactly what to fix."""
    problems = []
    items = invoice.get("items")
    if not isinstance(items, list) or not items:
        problems.append("'items' must be a non-empty list of {description, qty, unit_price}.")
        items = []

    for index, item in enumerate(items):
        where = f"items[{index}]"
        if not isinstance(item, dict):
            problems.append(f"{where} must be an object, got {type(item).__name__}.")
            continue
        if not str(item.get("description", "")).strip():
            problems.append(f"{where}.description is missing or empty.")
        qty = _decimal(item.get("qty"))
        if qty is None or qty <= 0:
            problems.append(f"{where}.qty must be a number greater than 0, got {item.get('qty')!r}.")
        price = _decimal(item.get("unit_price"))
        if price is None or price < 0:
            problems.append(f"{where}.unit_price must be a number >= 0, got {item.get('unit_price')!r}.")

    for field in ("discount_pct", "tax_pct"):
        if field in invoice:
            pct = _decimal(invoice[field])
            if pct is None or not (0 <= pct <= 100):
                problems.append(f"'{field}' must be between 0 and 100, got {invoice[field]!r}.")

    unknown = set(invoice) - {"number", "customer", "currency", "discount_pct", "tax_pct", "items", "notes"}
    if unknown:
        problems.append(f"Unknown top-level fields {sorted(unknown)}; allowed: number, customer, currency, discount_pct, tax_pct, items, notes.")

    return {"ok": not problems, "problems": problems}


def totals(invoice: dict) -> dict:
    check = validate(invoice)
    if not check["ok"]:
        raise ValueError("Invoice is invalid; run validate first: " + " ".join(check["problems"]))

    lines = []
    subtotal = Decimal("0")
    for item in invoice["items"]:
        amount = money(Decimal(str(item["qty"])) * Decimal(str(item["unit_price"])))
        subtotal += amount
        lines.append({"description": item["description"], "qty": str(item["qty"]),
                      "unit_price": str(money(Decimal(str(item["unit_price"])))), "amount": str(amount)})

    discount = money(subtotal * Decimal(str(invoice.get("discount_pct", 0))) / 100)
    taxable = subtotal - discount
    tax = money(taxable * Decimal(str(invoice.get("tax_pct", 0))) / 100)
    return {
        "currency": invoice.get("currency", "USD"),
        "lines": lines,
        "subtotal": str(subtotal),
        "discount": str(discount),
        "tax": str(tax),
        "total": str(taxable + tax),
    }


def render(invoice: dict) -> str:
    t = totals(invoice)
    cur = t["currency"]
    out = [f"# Invoice {invoice.get('number', '')}".rstrip(), ""]
    if invoice.get("customer"):
        out += [f"**Bill to:** {invoice['customer']}", ""]
    out += ["| Description | Qty | Unit price | Amount |", "|---|---:|---:|---:|"]
    out += [f"| {l['description']} | {l['qty']} | {l['unit_price']} | {l['amount']} |" for l in t["lines"]]
    out += ["", f"Subtotal: {t['subtotal']} {cur}  "]
    if Decimal(t["discount"]):
        out.append(f"Discount ({invoice['discount_pct']}%): -{t['discount']} {cur}  ")
    if Decimal(t["tax"]):
        out.append(f"Tax ({invoice['tax_pct']}%): {t['tax']} {cur}  ")
    out += [f"**Total: {t['total']} {cur}**", ""]
    if invoice.get("notes"):
        out += [invoice["notes"], ""]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description="Validate, total and render invoices.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "total"):
        sub.add_parser(name).add_argument("file")
    p_render = sub.add_parser("render")
    p_render.add_argument("file")
    p_render.add_argument("--out", required=True)

    args = parser.parse_args(argv)
    try:
        invoice = load(args.file)
        if args.command == "validate":
            result = validate(invoice)
            print(json.dumps(result, ensure_ascii=False))
            return 0 if result["ok"] else 1
        if args.command == "total":
            print(json.dumps(totals(invoice), ensure_ascii=False))
            return 0
        Path(args.out).write_text(render(invoice), encoding="utf-8")
        print(json.dumps({"written": args.out}))
        return 0
    except ValueError as err:
        print(json.dumps({"error": str(err)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
