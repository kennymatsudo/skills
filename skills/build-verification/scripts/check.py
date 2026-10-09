#!/usr/bin/env python3
"""Check a verification kit's feature map against its format and the repo.

Usage: check.py [KIT_DIR] [--evidence-dir DIR]

KIT_DIR defaults to the directory above this script. Exits 0 when the map is
valid, 1 when it has errors, 2 when it cannot run. Evidence age is reported as
warnings only, because evidence directories are usually local and git-ignored.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SUB_FEATURE = re.compile(r"^- ([a-z0-9][a-z0-9._-]*): \S")
PROOF = re.compile(r"^- ([a-z0-9][a-z0-9._-]*): (.+)$")
INDEX_LINK = re.compile(r"\]\(([^)#]+\.md)\)")
BACKTICK = re.compile(r"`([^`]+)`")
REQUIRED = ["Sub-features", "How a user reaches it", "How to prove it", "Gotchas"]
OPTIONAL = ["Request flow"]
REQUIREMENTS = "requirements.md"
CLAUSE = re.compile(r"^- (.+?) \| (.+?) \| (.+)$")
OUTCOME = re.compile(r"^(ids: .+|No check yet|not in source|blocked on decision: .+|out of scope: .+)$")


def sections(text):
    found, current = {}, None
    order = []
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            order.append(current)
            found[current] = []
        elif current:
            found[current].append(line)
    return order, found


def proof_kind(body):
    if body.startswith("No check yet"):
        return "none"
    if body.startswith("Unreachable:"):
        return "unreachable" if "Tried" in body else "bad-unreachable"
    if body.startswith("`"):
        return "command"
    return "bad"


def command_path_exists(command, repo_root):
    first = command.split()[0]
    if "/" not in first:
        return True
    return (repo_root / first).exists()


def check_feature(path, repo_root, seen_ids, errors):
    order, body = sections(path.read_text())
    name = path.name
    headings = [h for h in order if h not in OPTIONAL]
    if headings != REQUIRED:
        errors.append(f"{name}: sections are {order}, expected {REQUIRED} in order")
        return {}

    ids = []
    for line in body["Sub-features"]:
        if line.startswith("- "):
            match = SUB_FEATURE.match(line)
            if not match:
                errors.append(f"{name}: sub-feature line is not '- <id>: <behavior>': {line}")
                continue
            sub_id = match.group(1)
            if sub_id in seen_ids:
                errors.append(f"{name}: {sub_id} is also defined in {seen_ids[sub_id]}")
            seen_ids[sub_id] = name
            ids.append(sub_id)

    proofs = {}
    for line in body["How to prove it"]:
        if not line.startswith("- "):
            continue
        match = PROOF.match(line)
        if not match:
            errors.append(f"{name}: proof line is not '- <id>: <proof>': {line}")
            continue
        sub_id, proof = match.groups()
        if sub_id in proofs:
            errors.append(f"{name}: {sub_id} has more than one proof line")
        proofs[sub_id] = proof

    commands = {}
    for sub_id in ids:
        if sub_id not in proofs:
            errors.append(f"{name}: {sub_id} has no line under 'How to prove it'")
            continue
        proof = proofs[sub_id]
        kind = proof_kind(proof)
        if kind == "bad":
            errors.append(f"{name}: {sub_id} proof must be a `command`, 'No check yet.', or 'Unreachable: ... Tried ...'")
        elif kind == "bad-unreachable":
            errors.append(f"{name}: {sub_id} is Unreachable but does not say what was tried")
        elif kind == "command":
            if "Break-tested" not in proof and "Not break-tested" not in proof:
                errors.append(f"{name}: {sub_id} check does not say 'Break-tested <date>: ...' or 'Not break-tested: ...'")
            for command in BACKTICK.findall(proof):
                if not command_path_exists(command, repo_root):
                    errors.append(f"{name}: {sub_id} names `{command}`, but {command.split()[0]} does not exist")
            commands[sub_id] = proof
    for sub_id in proofs:
        if sub_id not in ids:
            errors.append(f"{name}: proof line for {sub_id}, which is not a sub-feature here")
    return commands


def check_requirements(path, seen_ids, errors):
    order, body = sections(path.read_text())
    if "Clauses" not in body:
        errors.append(f"{REQUIREMENTS}: no '## Clauses' section")
        return
    for line in body["Clauses"]:
        if not line.startswith("- "):
            continue
        match = CLAUSE.match(line)
        if not match:
            errors.append(f"{REQUIREMENTS}: clause line is not '- <clause> | <source> | <outcome>': {line}")
            continue
        outcome = match.group(3).strip()
        if not OUTCOME.match(outcome):
            errors.append(f"{REQUIREMENTS}: unknown outcome '{outcome}' for: {match.group(1)}")
            continue
        if outcome.startswith("ids: "):
            for sub_id in (part.strip() for part in outcome[5:].split(",")):
                if sub_id not in seen_ids:
                    errors.append(f"{REQUIREMENTS}: {sub_id} is not a sub-feature in the map")


def git(repo_root, *args):
    result = subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def evidence_warnings(evidence_dir, commands, repo_root):
    latest = {}
    for path in sorted(evidence_dir.glob("*.json")):
        try:
            record = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if record.get("passed") is not True:
            continue
        for sub_id in record.get("sub_features", []):
            if sub_id not in latest or record.get("finished_at", "") > latest[sub_id].get("finished_at", ""):
                latest[sub_id] = record

    warnings = []
    for sub_id in sorted(commands):
        record = latest.get(sub_id)
        if not record:
            warnings.append(f"{sub_id}: no passing evidence in {evidence_dir}")
            continue
        commit = (record.get("code") or {}).get("commit")
        behind = git(repo_root, "rev-list", "--count", f"{commit}..HEAD") if commit else None
        if behind is None:
            warnings.append(f"{sub_id}: last pass ran on {commit or 'an unknown commit'}, which this checkout cannot find")
        elif behind != "0":
            warnings.append(f"{sub_id}: last pass is {behind} commit{'' if behind == '1' else 's'} behind HEAD")
    return warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("kit_dir", nargs="?", default=Path(__file__).resolve().parent.parent, type=Path)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()

    features_dir = args.kit_dir / "features"
    index = features_dir / "README.md"
    if not index.is_file():
        print(f"STOPPED: no feature index at {index}", file=sys.stderr)
        return 2
    repo_root = Path(git(args.kit_dir, "rev-parse", "--show-toplevel") or args.kit_dir)

    errors = []
    index_text = index.read_text()
    _, index_sections = sections(index_text)
    linked = {link.lstrip("./") for link in INDEX_LINK.findall("\n".join(index_sections.get("Features", [])))}
    for link in set(INDEX_LINK.findall(index_text)):
        if "://" not in link and not (features_dir / link).is_file():
            errors.append(f"README.md links {link}, which does not exist")
    files = {p.name for p in features_dir.glob("*.md") if p.name not in ("README.md", REQUIREMENTS)}
    for unlisted in sorted(files - linked):
        errors.append(f"{unlisted} is not listed in README.md")

    seen_ids, commands = {}, {}
    for name in sorted(files):
        commands.update(check_feature(features_dir / name, repo_root, seen_ids, errors))
    if (features_dir / REQUIREMENTS).is_file():
        check_requirements(features_dir / REQUIREMENTS, seen_ids, errors)

    for error in errors:
        print(f"ERROR {error}")
    if args.evidence_dir:
        if args.evidence_dir.is_dir():
            for warning in evidence_warnings(args.evidence_dir, commands, repo_root):
                print(f"WARN {warning}")
        else:
            print(f"WARN no evidence directory at {args.evidence_dir}")

    total = len(seen_ids)
    print(f"{len(files)} features, {total} sub-features, {len(commands)} with checks, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
