#!/usr/bin/env python3
"""Shared lens context, claim grouping, checker batches, and answer accounting.

  claims.py context  RUN_DIR --base REF [--staged]
                                         run in the repo; writes context.md for the lenses
  claims.py batch    RUN_DIR [--size N]   reads lens-*.json, groups claims, writes batch-*.md
  claims.py status   RUN_DIR              reads check-*.json, prints each group's answer
  claims.py findings RUN_DIR              prints kept groups, groups to settle, and kept groups
                                         that cite nearby lines

A group joins claims only when they share a verdict and their cited lines
overlap, so claims proposing different moves never collapse into one finding,
and overlapping lenses cost one check instead of several. Batches hold only
claim text, stated cost, case for leaving it, and evidence, so checkers never
see a verdict or proposed move, and the main agent never retypes a claim.
Checkers confirm the cost and the case for leaving it too, so a finding's
strength and its counterargument both rest on checked facts.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

LENSES = ["depth", "ownership", "locality", "domain", "modules", "parsing", "reruns", "enforcement", "testability", "layers"]
VERDICTS = {"move", "split", "merge", "delete", "backstop", "relocate", "defer", "ask"}
LABELS = {"Holds", "Narrowed", "Refuted", "Unresolved"}
MAX_DIFF_LINES = 2000


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def context(run_dir, base, staged):
    merge_base = git("merge-base", "HEAD", base).strip()
    against = ["--cached", merge_base] if staged else [merge_base]
    diff = git("diff", *against)
    untracked = [] if staged else git("ls-files", "--others", "--exclude-standard").split()
    parts = [
        f"# Scope\n\nBase `{base}`, merge base `{merge_base}`{', staged only' if staged else ''}.\n",
        "## Changed files\n\n```\n" + git("diff", "--stat", *against) + "```\n",
    ]
    if untracked:
        parts.append("## Untracked files\n\n" + "\n".join(f"- `{p}`" for p in untracked) + "\n")
    if len(diff.splitlines()) <= MAX_DIFF_LINES:
        parts.append("## Diff\n\n```diff\n" + diff + "```\n")
    else:
        parts.append(f"## Diff\n\nOver {MAX_DIFF_LINES} lines; read the changed files directly.\n")
    path = run_dir / "context.md"
    path.write_text("\n".join(parts))
    print(path)
    return 0


def load_claims(run_dir):
    claims, errors = [], []
    for lens in LENSES:
        path = run_dir / f"lens-{lens}.json"
        if not path.exists():
            errors.append(f"{path.name}: missing")
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{path.name}: invalid JSON ({e})")
            continue
        for i, finding in enumerate(data.get("findings", []), 1):
            claim_id = f"{lens}-{i}"
            evidence = finding.get("evidence") or []
            if not str(finding.get("claim", "")).strip():
                errors.append(f"{claim_id}: no claim text")
            if not evidence or not all(e.get("location") and e.get("quote") for e in evidence):
                errors.append(f"{claim_id}: every claim needs evidence with a location and a quote")
            if finding.get("verdict") not in VERDICTS:
                errors.append(f"{claim_id}: verdict must be one of {sorted(VERDICTS)}")
            claims.append({"id": claim_id, "lens": lens, **finding, "evidence": evidence})
    return claims, errors


def line_span(location):
    path, _, lines = location.rpartition(":")
    if not path or not lines.replace("-", "").isdigit():
        return location, 0, float("inf")
    start, _, end = lines.partition("-")
    return path, int(start), int(end or start)


def overlaps(a, b):
    for x in a["evidence"]:
        px, sx, ex = line_span(x["location"])
        for y in b["evidence"]:
            py, sy, ey = line_span(y["location"])
            if px == py and sx <= ey and sy <= ex:
                return True
    return False


def group_claims(claims):
    parent = {c["id"]: c["id"] for c in claims}

    def root(i):
        while parent[i] != i:
            i = parent[i]
        return i

    for i, a in enumerate(claims):
        for b in claims[i + 1:]:
            if a["verdict"] == b["verdict"] and overlaps(a, b):
                parent[root(b["id"])] = root(a["id"])
    grouped = {}
    for c in claims:
        grouped.setdefault(root(c["id"]), []).append(c)
    return {f"G{n}": members for n, members in enumerate(grouped.values(), 1)}


def load_groups(run_dir):
    claims, errors = load_claims(run_dir)
    if errors:
        return None, errors
    by_id = {c["id"]: c for c in claims}
    saved = json.loads((run_dir / "groups.json").read_text())
    return {gid: [by_id[i] for i in ids] for gid, ids in saved.items()}, []


def batch(run_dir, size):
    claims, errors = load_claims(run_dir)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    groups = group_claims(claims)
    (run_dir / "groups.json").write_text(json.dumps({gid: [c["id"] for c in m] for gid, m in groups.items()}, indent=2))
    for old in run_dir.glob("batch-*.md"):
        old.unlink()
    gids = list(groups)
    batches = [gids[i:i + size] for i in range(0, len(gids), size)]
    for n, chunk in enumerate(batches, 1):
        lines = []
        for gid in chunk:
            lines.append(f"## {gid}\n")
            seen = set()
            for c in groups[gid]:
                lines.append(f"- {c['claim']}")
            lines.append("\nStated costs:\n")
            for c in groups[gid]:
                lines.append(f"- {c.get('cost') or 'none found'}")
            lines.append("\nStated cases for leaving it:\n")
            for c in groups[gid]:
                lines.append(f"- {c.get('leave') or 'none given'}")
            lines.append("")
            for c in groups[gid]:
                for e in c["evidence"]:
                    key = (e["location"], e["quote"])
                    if key not in seen:
                        seen.add(key)
                        lines.append(f"`{e['location']}`\n\n```\n{e['quote']}\n```\n")
        (run_dir / f"batch-{n}.md").write_text("\n".join(lines))
    print(f"{len(claims)} claims in {len(groups)} groups, {len(batches)} batches")
    for n in range(1, len(batches) + 1):
        print(run_dir / f"batch-{n}.md")
    return 0


def load_answers(run_dir, groups):
    answers, problems = {}, []
    for path in sorted(run_dir.glob("check-*.json")):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            problems.append(f"{path.name}: invalid JSON ({e})")
            continue
        for a in data.get("answers", []):
            gid = a.get("id")
            if gid in answers:
                problems.append(f"{gid}: answered more than once")
            if a.get("label") not in LABELS:
                problems.append(f"{gid}: label must be one of {sorted(LABELS)}")
            if a.get("label") in {"Holds", "Narrowed", "Refuted"} and not a.get("evidence"):
                problems.append(f"{gid}: {a.get('label')} needs cited evidence")
            for field in ("confirmed_cost", "confirmed_leave"):
                if not str(a.get(field, "")).strip():
                    problems.append(f"{gid}: needs {field}, or none")
            answers[gid] = a
    for gid in groups:
        if gid not in answers:
            problems.append(f"{gid}: no checker answer")
    for gid in sorted(set(answers) - set(groups)):
        problems.append(f"{gid}: answer for an unknown group")
    return answers, problems


def checked(run_dir):
    groups, errors = load_groups(run_dir)
    if errors:
        return None, None, errors
    answers, problems = load_answers(run_dir, groups)
    return groups, answers, problems


def status(run_dir):
    groups, answers, problems = checked(run_dir)
    for gid, members in (groups or {}).items():
        if gid in answers:
            print(f"{gid}\t{answers[gid].get('label')}\t{', '.join(c['id'] for c in members)}")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    return 0


NEARBY_LINES = 40


def same_file(a, b):
    """Lenses cite paths from different roots, so match on a trailing path."""
    return a == b or a.endswith("/" + b) or b.endswith("/" + a)


def cited_spans(members):
    """A relocate cites the file it moves first, and moving it touches every line."""
    spans = []
    for c in members:
        for i, e in enumerate(c["evidence"]):
            path, start, end = line_span(e["location"])
            spans.append((path, 0, float("inf")) if c["verdict"] == "relocate" and i == 0 else (path, start, end))
    return spans


def nearby(x, y):
    return same_file(x[0], y[0]) and x[1] - NEARBY_LINES <= y[2] and y[1] - NEARBY_LINES <= x[2]


def overlapping_pairs(groups, kept):
    spans = {gid: cited_spans(groups[gid]) for gid in kept}
    pairs = []
    for i, a in enumerate(kept):
        for b in kept[i + 1:]:
            shared = sorted({x[0] for x in spans[a] for y in spans[b] if nearby(x, y)})
            if shared:
                pairs.append((a, b, shared))
    return pairs


def findings(run_dir):
    groups, answers, problems = checked(run_dir)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    unsettled, kept = [], []
    for gid, members in groups.items():
        a = answers[gid]
        if a["label"] not in {"Holds", "Narrowed"}:
            unsettled.append(gid)
            continue
        kept.append(gid)
        print(f"## {gid}: {members[0]['verdict']} ({a['label']}), claims {', '.join(c['id'] for c in members)}\n")
        if a.get("narrowed_claim"):
            print(f"Narrowed to: {a['narrowed_claim']}\n")
        print(f"Confirmed cost: {a['confirmed_cost']}\n")
        print(f"Confirmed case for leaving it: {a['confirmed_leave']}\n")
        for c in members:
            print(f"- {c['id']}: {c['claim']}")
            print(f"  locations: {', '.join(e['location'] for e in c['evidence'])}")
            print(f"  move: {c.get('move', '')}")
            print(f"  cost: {c.get('cost', '')}")
        print()
    if unsettled:
        print("## To settle\n")
        for gid in unsettled:
            a = answers[gid]
            cited = ", ".join(e["location"] for e in a.get("evidence") or []) or "none"
            claims = "; ".join(c["claim"] for c in groups[gid])
            print(f"- {gid} ({a['label']}, checker cites {cited}): {claims}")
    pairs = overlapping_pairs(groups, kept)
    if pairs:
        print(f"\n## Overlapping pairs (cited lines within {NEARBY_LINES} of each other)\n")
        for a, b, shared in pairs:
            print(f"- {a} + {b}: {', '.join(shared)}")
    return 0


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("context")
    c.add_argument("run_dir", type=Path)
    c.add_argument("--base", required=True)
    c.add_argument("--staged", action="store_true")
    b = sub.add_parser("batch")
    b.add_argument("run_dir", type=Path)
    b.add_argument("--size", type=int, default=5)
    for name in ("status", "findings"):
        sub.add_parser(name).add_argument("run_dir", type=Path)
    args = parser.parse_args()
    if args.command == "context":
        return context(args.run_dir, args.base, args.staged)
    if args.command == "batch":
        return batch(args.run_dir, args.size)
    if args.command == "findings":
        return findings(args.run_dir)
    return status(args.run_dir)


if __name__ == "__main__":
    sys.exit(main())
