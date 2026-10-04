#!/usr/bin/env python3
"""List the test and production files a branch changes, and flag test edits that can make a test easier to pass.

Usage: python3 test_diff.py --base <ref> [--staged]

Compares the working tree (committed, uncommitted, and untracked) against the merge base with <ref>.
Pass --base HEAD for uncommitted work only, and add --staged for staged changes only.
Flags are text-pattern leads, not verdicts: removed assertions, added skip or focus markers, and deleted tests.
"""

import argparse
import re
import subprocess
import sys

TEST_PATH = re.compile(
    r"(^|/)(tests?|__tests__|specs?)/"
    r"|(^|/)test_[^/]+\.py$"
    r"|_test\.\w+$"
    r"|_spec\.rb$"
    r"|\.(test|spec)\.\w+$"
    r"|Tests?\.(java|kt|cs|swift)$"
)

ASSERTION = re.compile(
    r"\bassert\w*"
    r"|\bexpect\s*\("
    r"|\.should\b"
    r"|\.to(Be|Equal|Have|Throw|Match|Contain|StrictEqual)\w*"
    r"|\bt\.(Error|Fatal|Fail)\w*"
    r"|\brequire\.\w+\("
    r"|\bXCTAssert\w*"
    r"|\bverify\s*\("
)

SKIP_MARKER = re.compile(
    r"\.(skip|skipIf|todo|fixme)\b"
    r"|\bskip\s*\("
    r"|@pytest\.mark\.(skip|xfail)"
    r"|@unittest\.(skip|expectedFailure)"
    r"|\.only\b"
    r"|\b(xit|xdescribe|xtest|fit|fdescribe)\s*\("
    r"|@Disabled|@Ignore"
    r"|\bt\.Skip"
    r"|#\[ignore\]"
)

TEST_DEFINITION = [
    re.compile(r"^\s*(?:async\s+)?def\s+(test\w*)"),
    re.compile(r"^\s*func\s+(Test\w+)"),
    re.compile(r"^\s*fn\s+(test\w*)"),
    re.compile(r"\b(?:it|test|scenario)\s*\(?\s*(['\"`])(.+?)\1"),
]


def git(*args):
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def test_name(line):
    for pattern in TEST_DEFINITION:
        match = pattern.search(line)
        if match:
            return match.group(match.lastindex)
    return None


def parse_hunks(diff):
    """Yield (sign, line_number, text) for removed (old numbering) and added (new numbering) lines."""
    old = new = 0
    for line in diff.splitlines():
        header = re.match(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if header:
            old, new = int(header.group(1)), int(header.group(2))
        elif line.startswith("-") and not line.startswith("---"):
            yield "-", old, line[1:]
            old += 1
        elif line.startswith("+") and not line.startswith("+++"):
            yield "+", new, line[1:]
            new += 1


def assertion_lines(old_lines):
    """Line numbers covered by each assertion, including continuation lines a formatter wrapped."""
    covered = set()
    for start, line in enumerate(old_lines):
        if not ASSERTION.search(line):
            continue
        depth = 0
        for number in range(start, min(start + 30, len(old_lines))):
            text = old_lines[number]
            depth += sum(text.count(c) for c in "([{") - sum(text.count(c) for c in ")]}")
            covered.add(number + 1)
            if depth <= 0:
                break
    return covered


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    base = git("merge-base", "HEAD", args.base).strip()
    against = ["--cached", base] if args.staged else [base]

    changed = {}
    for row in git("diff", "--name-status", "--no-renames", *against).splitlines():
        status, path = row.split("\t", 1)
        changed[path] = status[0]
    if not args.staged:
        for path in git("ls-files", "--others", "--exclude-standard").splitlines():
            changed[path] = "?"

    tests = {path: status for path, status in changed.items() if TEST_PATH.search(path)}
    production = sorted(path for path in changed if path not in tests)
    labels = {"A": "added", "?": "untracked", "M": "modified", "D": "deleted"}

    flags, unrecognized = [], []
    for path, status in sorted(tests.items()):
        if status == "D":
            flags.append(f"{path}: deleted test file")
            continue
        in_assertion = set()
        if status == "?":
            lines = [("+", number, text) for number, text in enumerate(read(path).splitlines(), 1)]
        else:
            lines = list(parse_hunks(git("diff", "-U0", *against, "--", path)))
            if status != "A":
                in_assertion = assertion_lines(git("show", f"{base}:{path}").splitlines())
        removed = {text.strip() for sign, _, text in lines if sign == "-"}
        added = {text.strip() for sign, _, text in lines if sign == "+"}
        current = read(path)

        for sign, number, text in lines:
            moved = text.strip() in (added if sign == "-" else removed)
            if moved:
                continue
            if sign == "-" and (ASSERTION.search(text) or number in in_assertion):
                flags.append(f"{path}:{number} (old line): removed or changed assertion: {text.strip()}")
            if sign == "-":
                name = test_name(text)
                if name and name not in current:
                    flags.append(f"{path}:{number} (old line): removed test, name gone from file: {name}")
            if sign == "+" and SKIP_MARKER.search(text):
                flags.append(f"{path}:{number}: added skip or focus marker: {text.strip()}")

        if not ASSERTION.search(current):
            unrecognized.append(path)

    print(f"Merge base: {base}")
    print(f"\nTest files ({len(tests)}):")
    for path, status in sorted(tests.items()):
        print(f"  {labels.get(status, status)}  {path}")
    tracked_tests = [path for path, status in sorted(tests.items()) if status not in "?D"]
    if tracked_tests:
        print(f"\nTest-only diff: git diff {' '.join(against)} -- {' '.join(tracked_tests)}")
    print(f"\nProduction files ({len(production)}):")
    for path in production:
        print(f"  {labels.get(changed[path], changed[path])}  {path}")

    print(f"\nFlags ({len(flags)}):")
    for flag in flags:
        print(f"  {flag}")
    if not flags:
        print(f"  No pattern matches in {len(tests)} test files. This is not proof the tests are untouched.")
    if unrecognized:
        print("\nNo assertion found in the current file. Either the style is unrecognized or the tests assert nothing; read by hand:")
        for path in unrecognized:
            print(f"  {path}")


if __name__ == "__main__":
    main()
