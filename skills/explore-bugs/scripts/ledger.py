#!/usr/bin/env python3
"""The exploration ledger: one JSON line per round of explore-bugs.

Each round starts in a fresh session, so the ledger is the loop's only memory:
what was tried, what behavior it reached, what it cost, and what is still open.
Settings come from the kit's exploration.json, which build-verification writes.

Usage:
    ledger.py --kit KIT_DIR summary          # where the loop stands, as JSON
    ledger.py --kit KIT_DIR add '<json>'     # append one round
    ledger.py --kit KIT_DIR cleaned ID ...   # record resources deleted

Exits 0 on success, 2 when it cannot run or a row is invalid.
"""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

VERDICTS = ("finding", "known", "no-break", "lead", "invalid", "planted-caught", "planted-missed")
REQUIRED = ("sweep", "hypothesis", "kind", "command", "signature", "verdict")
DEFAULT_KINDS = ["timing", "order", "identity", "input-shape", "lifecycle", "external-side", "code-reading"]


class LedgerError(ValueError):
    pass


def load_settings(kit):
    path = kit / "exploration.json"
    if not path.is_file():
        raise LedgerError(f"no exploration settings at {path}; set up exploration with build-verification")
    settings = json.loads(path.read_text())
    if "ledger" not in settings:
        raise LedgerError(f"{path} has no ledger")
    repo_root = kit
    while repo_root != repo_root.parent and not (repo_root / ".git").exists():
        repo_root = repo_root.parent
    settings["ledger_path"] = repo_root / settings["ledger"]
    settings.setdefault("kinds", DEFAULT_KINDS)
    settings.setdefault("stale_rounds", 3)
    return settings


def read(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def rounds(lines):
    return [line for line in lines if "cleaned" not in line]


def append(path, entry):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as ledger:
        ledger.write(json.dumps(entry) + "\n")
    return entry


def add(row, settings):
    missing = [key for key in REQUIRED if key not in row]
    if missing:
        raise LedgerError(f"missing {', '.join(missing)}")
    if row["kind"] not in settings["kinds"] and row["kind"] != "planted":
        raise LedgerError(f"kind must be one of {', '.join(settings['kinds'])}, or planted")
    if row["verdict"] not in VERDICTS:
        raise LedgerError(f"verdict must be one of {', '.join(VERDICTS)}")
    if not isinstance(row["signature"], list) or not all(isinstance(part, str) for part in row["signature"]):
        raise LedgerError("signature must be a list of strings")
    path = settings["ledger_path"]
    number = len(rounds(read(path))) + 1
    return append(path, {"round": number, "at": datetime.now().isoformat(timespec="seconds"), **row})


def summary(lines, settings):
    """A round is new when its signature, the set of behaviors it reached, was never reached before."""
    rows = rounds(lines)
    deleted = {item for line in lines for item in line.get("cleaned", [])}
    sweep = rows[-1]["sweep"] if rows else None
    # Planted rounds rediscover a known break on purpose, so they never count as new.
    seen, new_flags = set(), []
    for row in (row for row in rows if row["kind"] != "planted"):
        signature = frozenset(row["signature"])
        new_flags.append(signature not in seen)
        seen.add(signature)
    since_new = 0
    for is_new in reversed(new_flags):
        if is_new:
            break
        since_new += 1
    tried = Counter(row["kind"] for row in rows)
    planted = [row for row in rows if row["kind"] == "planted"]
    return {
        "sweep": sweep,
        "rounds": len(rows),
        "rounds_since_new_signature": since_new,
        "must_change_approach": since_new >= settings["stale_rounds"],
        "kinds_tried": {kind: tried.get(kind, 0) for kind in settings["kinds"]},
        "planted_caught": f"{sum(row['verdict'] == 'planted-caught' for row in planted)}/{len(planted)}",
        "open_findings": [
            {key: row.get(key) for key in ("round", "hypothesis", "verdict", "reproduced", "finding", "evidence")}
            for row in rows if row["verdict"] in ("finding", "lead") and not row.get("closed")
        ],
        "to_clean": sorted({item for row in rows for item in row.get("created_open", [])} - deleted),
        "recent": [
            {key: row.get(key) for key in ("round", "kind", "hypothesis", "verdict", "signature")}
            for row in rows[-5:]
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--kit", type=Path, required=True, help="the verification kit directory")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("summary")
    adding = commands.add_parser("add")
    adding.add_argument("row", help="one round as a JSON object")
    cleaning = commands.add_parser("cleaned")
    cleaning.add_argument("ids", nargs="+", help="IDs of resources this loop created and has now deleted")
    args = parser.parse_args()
    try:
        settings = load_settings(args.kit.resolve())
        if args.command == "summary":
            result = summary(read(settings["ledger_path"]), settings)
        elif args.command == "cleaned":
            entry = {"at": datetime.now().isoformat(timespec="seconds"), "cleaned": [str(i) for i in args.ids]}
            result = append(settings["ledger_path"], entry)
        else:
            result = add(json.loads(args.row), settings)
    except (LedgerError, json.JSONDecodeError) as error:
        print(f"STOPPED: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
