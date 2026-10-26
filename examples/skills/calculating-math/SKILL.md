---
name: calculating-math
description: Calculates basic math on one or two numbers - add, subtract, multiply, divide, square root, sine and cosine in degrees or radians - from requests in any word order, with numbers written as words ("seven") or with typos ("sinus", "squere root"). Use when the user asks for a simple arithmetic or trigonometry result. Not for unit conversion (use converting-units), dates (use calculating-dates) or invoices (use calculating-invoices).
allowed-tools:
  - Bash(python *)
  - PowerShell(python *)
effort: low
---

# Calculating math

The user's request can be messy: any word order, numbers as words, typos. Your job is to turn it
into one clean command. The script does the math: never compute the result yourself.

What the user typed after /calculating-math (empty if you chose this skill yourself): $ARGUMENTS

## 1. Find the three parts of the request

- **Operation:** add, subtract, multiply, divide, sqrt, sin or cos. Read other words and typos by
  meaning: "plus" = add, "times" = multiply, "sinus" = sin, "squere root" or "squera root" = sqrt.
- **Numbers:** write them as digits: "seven" = 7, "twenty-three" = 23.
- **Unit,** only for sin and cos: degrees or radians, also misspelled ("radnias" = radians). If the
  request has no unit, use degrees, and say so in the answer.

For subtract and divide the order matters: "subtract 5 from 7" is 7 - 5, and "divide 10 by 2" is
10 / 2. If the order is unclear, use the order in which the numbers appear, and say so.

## 2. Run one command

```bash
python "${CLAUDE_SKILL_DIR}/scripts/calc.py" <operation> <number> [<number>] [--unit degrees|radians]
```

| The user writes | Command after `calc.py` |
|---|---|
| seven and five add | `add 7 5` |
| add seven and five | `add 7 5` |
| 23 cosine | `cos 23 --unit degrees` (no unit given: degrees) |
| cosine of 45 degrees | `cos 45 --unit degrees` |
| sinus 3 radians | `sin 3 --unit radians` |
| 4 radnias sinus | `sin 4 --unit radians` |
| 45 squere root | `sqrt 45` |
| squera root 67 | `sqrt 67` |

## 3. Answer

Report `result` from the JSON, and say how you read the request, for example "cos 23° = 0.9205".
If the JSON has `error`, read its `hint`, fix the command, and run it again.
