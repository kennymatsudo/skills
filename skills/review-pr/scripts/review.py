#!/usr/bin/env python3
"""Numbered diff, finding collection, checker batches, and answer accounting.

  review.py context  RUN_DIR --base REF --head REF
                                    run in the repo; writes context.md and changed.json
  review.py collect  RUN_DIR        reads review-*.json, drops findings whose cause is not a
                                    changed line, groups duplicates, writes batch-*.md
  review.py status   RUN_DIR        reads check-*.json, prints each group's answer
  review.py findings RUN_DIR        prints kept groups, then dropped and unresolved ones

The diff carries head line numbers because models anchor findings better on
numbered lines. Every finding must name a cause on a line the PR added or changed, so
pre-existing problems drop out mechanically instead of by judgment.
Batches hold only the claim, scenario, cause, and evidence, so a checker judges
the code and never sees which reviewer raised it or how severe it was called.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

LENSES = ["diff", "contracts", "intent", "security"]
SEVERITIES = {"high", "medium"}
LABELS = {"Proven", "Holds", "Refuted", "Unresolved", "Below the bar"}
KEPT = {"Proven", "Holds"}
MAX_DIFF_LINES = 3000
SAME_CAUSE_LINES = 3
HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def number_diff(diff):
    """Prefix each diff line with its head line number and collect changed head lines.

    A pure deletion has no head line, so the head line after it counts as changed:
    that is where a reviewer anchors "this removal breaks X".
    """
    out, changed, path, new, header = [], {}, None, 0, False
    for line in diff.splitlines():
        if line.startswith("diff --git"):
            path, header = None, True
            out.append(line)
        elif header and line.startswith("+++ "):
            path = None if line == "+++ /dev/null" else line[6:]
            out.append(line)
        elif m := HUNK.match(line):
            new, header = int(m.group(2)), False
            out.append(line)
        elif header or path is None or line.startswith("\\"):
            out.append(line)
        elif line.startswith("+"):
            changed.setdefault(path, set()).add(new)
            out.append(f"{new:>6} {line}")
            new += 1
        elif line.startswith("-"):
            changed.setdefault(path, set()).add(new)
            out.append(f"{'':>6} {line}")
        else:
            out.append(f"{new:>6} {line}")
            new += 1
    return "\n".join(out) + "\n", {p: sorted(s) for p, s in changed.items()}


def context(run_dir, base, head):
    merge_base = git("merge-base", base, head).strip()
    diff = git("diff", "-U5", "--no-color", merge_base, head)
    numbered, changed = number_diff(diff)
    lines = numbered.count("\n")
    parts = [
        f"# Scope\n\nMerge base `{merge_base}`, head `{git('rev-parse', head).strip()}`.\n",
        "## Changed files\n\n```\n" + git("diff", "--stat", merge_base, head) + "```\n",
    ]
    if lines <= MAX_DIFF_LINES:
        parts.append("## Diff\n\nEach line starts with its line number at head; removed lines have none.\n\n```diff\n" + numbered + "```\n")
    else:
        parts.append(f"## Diff\n\nOver {MAX_DIFF_LINES} lines. Read only the files in your scope, with `git diff {merge_base} {head} -- <path>`.\n")
    (run_dir / "context.md").write_text("\n".join(parts))
    (run_dir / "changed.json").write_text(json.dumps(changed, indent=1))
    print(f"{run_dir / 'context.md'}: {len(changed)} files, {lines} diff lines")
    return 0


def split_location(location):
    path, _, lines = str(location).rpartition(":")
    start, _, end = lines.partition("-")
    if not path or not start.isdigit() or (end and not end.isdigit()):
        return None
    return path, int(start), int(end or start)


def match_path(path, changed):
    """Reviewers cite paths from different roots, so match on a trailing path."""
    for p in changed:
        if p == path or p.endswith("/" + path) or path.endswith("/" + p):
            return p
    return None


def on_changed_line(cause, changed):
    span = split_location(cause)
    if not span:
        return False
    path = match_path(span[0], changed)
    return bool(path) and any(span[1] <= n <= span[2] for n in changed[path])


def load_findings(run_dir):
    findings, errors = [], []
    for lens in LENSES:
        path = run_dir / f"review-{lens}.json"
        if not path.exists():
            errors.append(f"{path.name}: missing")
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{path.name}: invalid JSON ({e})")
            continue
        for i, f in enumerate(data.get("findings", []), 1):
            fid = f"{lens}-{i}"
            for field in ("claim", "scenario", "cause", "proof"):
                if not str(f.get(field, "")).strip():
                    errors.append(f"{fid}: no {field}")
            if not split_location(f.get("cause")):
                errors.append(f"{fid}: cause must be path:line or path:start-end")
            evidence = f.get("evidence") or []
            if not evidence or not all(e.get("location") and e.get("quote") for e in evidence):
                errors.append(f"{fid}: needs evidence with a location and a quote")
            if f.get("severity") not in SEVERITIES:
                errors.append(f"{fid}: severity must be one of {sorted(SEVERITIES)}")
            findings.append({"id": fid, "lens": lens, **f, "evidence": evidence})
    return findings, errors


def group(findings):
    groups = []
    for f in findings:
        path, start, end = split_location(f["cause"])
        for g in groups:
            p, s, e = split_location(g[0]["cause"])
            if (p == path or p.endswith("/" + path) or path.endswith("/" + p)) and start - SAME_CAUSE_LINES <= e and s - SAME_CAUSE_LINES <= end:
                g.append(f)
                break
        else:
            groups.append([f])
    return {f"G{n}": g for n, g in enumerate(groups, 1)}


def missing_steps(run_dir):
    return [f"{name}: missing; write it before reviewing" for name in ("intent.md", "map.md") if not (run_dir / name).exists()]


def collect(run_dir):
    findings, errors = load_findings(run_dir)
    errors = missing_steps(run_dir) + errors
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    changed = json.loads((run_dir / "changed.json").read_text())
    inside = [f for f in findings if on_changed_line(f["cause"], changed)]
    outside = [f for f in findings if f not in inside]
    groups = group(inside)
    saved = {"groups": {gid: [f["id"] for f in g] for gid, g in groups.items()}, "outside": [f["id"] for f in outside]}
    (run_dir / "groups.json").write_text(json.dumps(saved, indent=2))
    for old in run_dir.glob("batch-*.md"):
        old.unlink()
    for gid, members in groups.items():
        lines = [f"# {gid}\n"]
        for f in members:
            lines += [f"- **Claim:** {f['claim']}", f"  **Scenario:** {f['scenario']}", f"  **Cause:** `{f['cause']}`", f"  **Suggested proof:** {f['proof']}"]
        lines.append("")
        seen = set()
        for f in members:
            for e in f["evidence"]:
                if (e["location"], e["quote"]) not in seen:
                    seen.add((e["location"], e["quote"]))
                    lines.append(f"`{e['location']}`\n\n```\n{e['quote']}\n```\n")
        (run_dir / f"batch-{gid}.md").write_text("\n".join(lines))
    print(f"{len(findings)} findings: {len(inside)} on changed lines in {len(groups)} groups, {len(outside)} dropped as outside the diff")
    for f in outside:
        print(f"  outside: {f['id']} cause {f['cause']}: {f['claim']}")
    for gid in groups:
        print(run_dir / f"batch-{gid}.md")
    return 0


def checked(run_dir):
    findings, errors = load_findings(run_dir)
    if errors:
        return None, None, None, errors
    by_id = {f["id"]: f for f in findings}
    saved = json.loads((run_dir / "groups.json").read_text())
    groups = {gid: [by_id[i] for i in ids] for gid, ids in saved["groups"].items()}
    answers, problems = {}, []
    for path in sorted(run_dir.glob("check-*.json")):
        try:
            a = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            problems.append(f"{path.name}: invalid JSON ({e})")
            continue
        gid = a.get("id")
        if gid not in groups:
            problems.append(f"{path.name}: answer for unknown group {gid}")
            continue
        if a.get("label") not in LABELS:
            problems.append(f"{gid}: label must be one of {sorted(LABELS)}")
        if a.get("label") != "Unresolved" and not a.get("evidence"):
            problems.append(f"{gid}: {a.get('label')} needs cited evidence")
        if a.get("label") == "Proven" and not (a.get("proof") or {}).get("command"):
            problems.append(f"{gid}: Proven needs the command that showed the failure")
        if a.get("label") in KEPT and a.get("severity") not in SEVERITIES:
            problems.append(f"{gid}: kept findings need a confirmed severity")
        answers[gid] = a
    for gid in groups:
        if gid not in answers:
            problems.append(f"{gid}: no checker answer")
    return groups, answers, saved["outside"], problems


def status(run_dir):
    groups, answers, _, problems = checked(run_dir)
    for gid in groups or {}:
        if gid in answers:
            print(f"{gid}\t{answers[gid].get('label')}\t{', '.join(f['id'] for f in groups[gid])}")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    return 0


def findings(run_dir):
    groups, answers, outside, problems = checked(run_dir)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    order = {"high": 0, "medium": 1}
    kept = sorted((g for g in groups if answers[g]["label"] in KEPT),
                  key=lambda g: (order[answers[g]["severity"]], answers[g]["label"] != "Proven"))
    for gid in kept:
        a = answers[gid]
        print(f"## {gid}: {a['severity']}, {a['label']}, from {', '.join(f['id'] for f in groups[gid])}\n")
        print(f"Confirmed claim: {a.get('claim') or groups[gid][0]['claim']}")
        print(f"Confirmed scenario: {a.get('scenario') or groups[gid][0]['scenario']}")
        print(f"Cause: {groups[gid][0]['cause']}")
        if a.get("proof"):
            print(f"Proof: {json.dumps(a['proof'])}")
        print(f"Evidence: {', '.join(e['location'] for e in a['evidence'])}")
        for f in groups[gid]:
            print(f"- {f['id']} fix: {f.get('fix', '')}")
        print()
    rest = [g for g in groups if g not in kept]
    if rest:
        print("## Not kept\n")
        for gid in rest:
            a = answers[gid]
            cited = ", ".join(e["location"] for e in a.get("evidence") or []) or "none"
            print(f"- {gid} ({a['label']}, checker cites {cited}): {groups[gid][0]['claim']} | {a.get('reasoning', '')}")
    print(f"\n{len(kept)} kept, {len(rest)} not kept, {len(outside)} outside the diff")
    return 0


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("context")
    c.add_argument("run_dir", type=Path)
    c.add_argument("--base", required=True)
    c.add_argument("--head", required=True)
    for name in ("collect", "status", "findings"):
        sub.add_parser(name).add_argument("run_dir", type=Path)
    args = parser.parse_args()
    if args.command == "context":
        return context(args.run_dir, args.base, args.head)
    return {"collect": collect, "status": status, "findings": findings}[args.command](args.run_dir)


if __name__ == "__main__":
    sys.exit(main())
