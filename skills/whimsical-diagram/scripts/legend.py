#!/usr/bin/env python3
"""Build a one-row legend strip for a Whimsical board.

Board table cells refuse hex colors and take the board's palette keys
(custom-...) instead, and a table added through `edit` ignores its position and
its hidden header. This turns a short legend spec into the ops that handle both.

Spec (JSON):
  {"x": 0, "y": 180, "width": 1600,
   "keys": [{"text": "Our service", "color": "#1F6F5C", "deco": "outline"},
            {"text": "Solid line"}],
   "meanings": ["Code we run", "Caller waits for the answer"]}

Prints {"step2": [...], "step3": [...]}:
  step2: the table, its key cells in the board's own color keys
  step3: fixes that need the table's id (replace <TABLE_ID> after a fetch)

Usage: python3 legend.py legend.json --palette palette.txt > legend_ops.json
palette.txt holds the "Palette:" line from a board fetch with detail "detailed",
taken after every hex color the legend uses is on the board.
"""
import json
import re
import sys


def legend_ops(legend, palette_text):
    by_hex = {h.upper(): k for k, h in re.findall(r"(custom-[A-Za-z0-9]+)=(#[0-9A-Fa-f]{6})", palette_text)}
    keys = []
    for cell in legend["keys"]:
        cell = {"bold": True, **cell}
        color = cell.get("color", "")
        if color.startswith("#"):
            if color.upper() not in by_hex:
                sys.exit(f"palette has no key for {color}: put a shape in that color on the board "
                         "first, then copy the Palette line from a fetch with detail 'detailed'")
            cell["color"] = by_hex[color.upper()]
        keys.append(cell)
    if len(keys) != len(legend["meanings"]):
        sys.exit("keys and meanings need the same length")
    n = len(keys)
    width = legend.get("width", 180 * n)
    widths = [int(width // n)] * n
    widths[-1] += int(width) - sum(widths)
    x, y = legend.get("x", 0), legend["y"]
    step2 = [{"op": "add", "type": "table", "x": x, "y": y, "head_style": "hide",
              "columns": [{"header": "-", "width": 200} for _ in range(n)],
              "rows": [keys, legend["meanings"]]}]
    step3 = [
        {"op": "update", "id": "<TABLE_ID>", "type": "table", "widths": widths},
        {"op": "update", "id": "<TABLE_ID>", "x": x, "y": y},
        {"op": "remove_rows", "id": "<TABLE_ID>", "indices": [0]},
    ]
    return {"step2": step2, "step3": step3}


def main():
    if "--palette" not in sys.argv or len(sys.argv) < 4:
        sys.exit(__doc__)
    with open(sys.argv[1]) as f:
        legend = json.load(f)
    with open(sys.argv[sys.argv.index("--palette") + 1]) as f:
        palette = f.read()
    json.dump(legend_ops(legend, palette), sys.stdout, indent=1)


if __name__ == "__main__":
    main()
