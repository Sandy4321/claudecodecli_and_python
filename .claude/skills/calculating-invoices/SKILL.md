---
name: calculating-invoices
description: Builds and checks invoices and quotes from line items - validates the JSON, computes subtotal, discount, sales tax/VAT, and grand total with correct cent rounding, and renders a Markdown invoice. Use when the user asks to total a bill, price a quote, apply a discount or tax to items, or produce an invoice document.
allowed-tools:
  - Bash(python *)
  - PowerShell(python *)
effort: high
---

# Calculating invoices

Money math must be exact (no float rounding errors), so the script uses `Decimal`.
Follow the workflow in order. Copy this checklist into your reply and tick it off:

```
- [ ] 1. Invoice JSON exists
- [ ] 2. Validation passes
- [ ] 3. Totals computed
- [ ] 4. Rendered (only if the user wants a document)
```

## 1. Create or locate the invoice JSON

If the user gave items in chat, write them to a file such as `invoice.json`:

```json
{
  "number": "INV-001",
  "customer": "Acme Ltd",
  "currency": "USD",
  "discount_pct": 10,
  "tax_pct": 8.25,
  "items": [
    {"description": "Consulting hours", "qty": 12, "unit_price": 95.00},
    {"description": "Travel", "qty": 1, "unit_price": 240.50}
  ]
}
```

`discount_pct` and `tax_pct` are optional (default 0). Discount applies before tax.
A sample is in `data/invoice.json`.

## 2. Validate - repeat until it passes

```bash
python "${CLAUDE_SKILL_DIR}/scripts/invoice.py" validate invoice.json
```

If it prints `"ok": false`, fix every listed problem in the JSON and validate again.
Do not compute totals from an invalid file.

## 3. Compute totals

```bash
python "${CLAUDE_SKILL_DIR}/scripts/invoice.py" total invoice.json
```

Report `subtotal`, `discount`, `tax`, and `total` exactly as printed.

## 4. Render (optional)

```bash
python "${CLAUDE_SKILL_DIR}/scripts/invoice.py" render invoice.json --out invoice.md
```
