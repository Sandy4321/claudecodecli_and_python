---
name: converting-units
description: Converts physical quantities between units of length, mass, volume, speed, temperature, and digital data size (km to miles, kg to lb, °F to °C, liters to gallons, mph to km/h, MB to GiB) with exact factors. Use for every unit conversion request, even simple ones like miles to kilometers, and whenever the user asks "how many X in Y".
allowed-tools:
  - Bash(python *)
  - PowerShell(python *)
effort: low
---

# Converting units

Never do unit math in your head. Run the script; it is exact and handles aliases.

## Convert one value

```bash
python "${CLAUDE_SKILL_DIR}/scripts/convert.py" convert 100 km mi
```

Output is JSON:

```json
{"value": 100.0, "from": "km", "to": "mi", "result": 62.137119, "category": "length"}
```

Report `result` to the user, rounded sensibly (usually 2-4 significant decimals).

## List supported units

```bash
python "${CLAUDE_SKILL_DIR}/scripts/convert.py" units
```

Run this when the user names a unit you are not sure about, then pick the closest match.

## Errors

If the script prints `{"error": ...}`, read the message. It lists valid units for the category,
so fix the unit name and run again. Do not guess a conversion factor yourself.
