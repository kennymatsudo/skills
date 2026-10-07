#!/usr/bin/env python3
"""List every way the harness's tests and checks got weaker since a commit.

Compares the working tree with --since (by default the last commit titled "Audit harness
checks", else the last commit before 30 days ago) and prints:

  deleted-test   a test function that no longer exists
  fewer-asserts  a file that lost more assertion lines than it gained
  removed-assert each assertion line removed, with its old text
  new-skip       a skip or xfail that was added
  check-changed  a check function (a top-level def matching --match) whose body changed

Each line is a lead. A weakening is fine only when the behavior it guarded changed on purpose;
a bug never changes the expectation. Python files only. Run from the project root.
Exits 1 when there are leads.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

DEFAULT_MATCH = r"(_problems$|_violations$|^check_)"
AUDIT_TITLE = "^Audit harness checks"
TEST_DEF = re.compile(r"^\s*(?:async\s+)?def (test_\w+)")
TOP_DEF = re.compile(r"^(?:async\s+)?def (\w+)\(")
ASSERT = re.compile(r"(\bself\.assert\w+|\bself\.fail\(|^\s*assert\s|\bpytest\.(raises|fail)\()")
SKIP = re.compile(r"(@\S*skip|\.skipTest\(|expectedFailure|mark\.xfail|pytest\.(skip|xfail)\()")
HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def default_since() -> tuple[str, str]:
    audit = git("log", "-1", "--format=%H", f"--grep={AUDIT_TITLE}", "--", ".").strip()
    if audit:
        return audit, "last Audit harness checks commit"
    return git("rev-list", "-1", "--before=30 days ago", "HEAD").strip(), "30 days ago (no earlier audit)"


def enclosing_checks(path: str, rev: str | None, match: re.Pattern[str]) -> list[tuple[int, str | None]]:
    """Start line and name of each top-level def in a file at rev (None = working tree).

    Non-check defs are kept with name None so a check's span ends where the next def starts.
    """
    try:
        text = git("show", f"{rev}:./{path}") if rev else open(path).read()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    starts = []
    for n, line in enumerate(text.splitlines(), 1):
        if m := TOP_DEF.match(line):
            starts.append((n, m.group(1) if match.search(m.group(1)) else None))
        elif line and not line[0].isspace() and not line.startswith(("#", "@", ")")):
            starts.append((n, None))
    return starts


def owner(starts: list[tuple[int, str | None]], line: int) -> str | None:
    name = None
    for start, candidate in starts:
        if start <= line:
            name = candidate
    return name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--since")
    parser.add_argument("--path", action="append", help="path to compare; repeatable (default harness)")
    parser.add_argument("--match", default=DEFAULT_MATCH, help=f"regex on check function names (default {DEFAULT_MATCH})")
    args = parser.parse_args()
    paths = args.path or ["harness"]
    match = re.compile(args.match)
    since, why = (args.since, "--since") if args.since else default_since()
    print(f"Since {since[:12]} ({why})")

    leads: list[str] = []
    removed_tests: dict[str, str] = {}
    added_tests: set[str] = set()
    for rel in git("diff", "--relative", "--name-only", since, "--", *paths).split():
        if not rel.endswith(".py"):
            continue
        diff = git("diff", "-U0", since, "--", rel)
        old_checks, new_checks = enclosing_checks(rel, since, match), enclosing_checks(rel, None, match)
        changed: set[str] = set()
        removed_asserts = added_asserts = 0
        old_line = new_line = 0
        for line in diff.splitlines():
            if hunk := HUNK.match(line):
                old_line, new_line = int(hunk.group(1)), int(hunk.group(2))
                continue
            if line.startswith(("---", "+++")):
                continue
            if line.startswith("-"):
                text = line[1:]
                if m := TEST_DEF.match(text):
                    removed_tests[m.group(1)] = rel
                if ASSERT.search(text):
                    removed_asserts += 1
                    leads.append(f"removed-assert {rel}:{old_line} {text.strip()[:140]}")
                if name := owner(old_checks, old_line):
                    changed.add(name)
                old_line += 1
            elif line.startswith("+"):
                text = line[1:]
                if m := TEST_DEF.match(text):
                    added_tests.add(m.group(1))
                if ASSERT.search(text):
                    added_asserts += 1
                if SKIP.search(text):
                    leads.append(f"new-skip {rel}:{new_line} {text.strip()[:140]}")
                if name := owner(new_checks, new_line):
                    changed.add(name)
                new_line += 1
        if removed_asserts > added_asserts:
            leads.append(f"fewer-asserts {rel}: -{removed_asserts} +{added_asserts}")
        leads += [f"check-changed {rel} {name}" for name in sorted(changed)]

    leads += [f"deleted-test {path} {name}" for name, path in sorted(removed_tests.items()) if name not in added_tests]
    order = ["deleted-test", "fewer-asserts", "new-skip", "check-changed", "removed-assert"]
    leads.sort(key=lambda lead: order.index(lead.split()[0]))
    print("\n".join(leads) if leads else "No weakening found.")
    return 1 if leads else 0


if __name__ == "__main__":
    sys.exit(main())
