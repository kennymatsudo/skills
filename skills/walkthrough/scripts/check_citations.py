#!/usr/bin/env python3
"""Check that every citation in a draft points at a real file and line range.

Usage: check_citations.py <repo-root> <base-ref> <head-ref> <draft-file | ->

A citation is `path:LINE` or `path:START-END`, checked against the head ref.
Prefix it with `before:` to check it against the base ref instead, for code the
change removed or rewrote. Exits 1 if any citation is broken or the draft has none.
On success, also prints the draft's word count with citations left out.
"""

import re
import subprocess
import sys
from pathlib import Path

CITATION = re.compile(r"(?<![\w/.-])(before:)?([\w./-]+\.\w+):(\d+)(?:-(\d+))?")
URL = re.compile(r"\w+://\S+")


def git(repo: str, *args: str) -> str | None:
    result = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def find_citations(draft: str) -> list[tuple[str, str, str, str]]:
    return CITATION.findall(URL.sub("", draft))


def prose_words(draft: str) -> int:
    # Citations leave wrappers like "(``)" behind; count only tokens with a letter or digit.
    return sum(1 for token in CITATION.sub("", URL.sub("", draft)).split() if re.search(r"\w", token))


def resolve(path_text: str, files: list[str]) -> str | None:
    if path_text in files:
        return path_text
    matches = [f for f in files if f.endswith("/" + path_text)]
    return matches[0] if len(matches) == 1 else None


def check(repo: str, base: str, head: str, draft: str) -> list[str]:
    citations = find_citations(draft)
    if not citations:
        return ["no path:line citations found"]

    files: dict[str, list[str]] = {}
    line_counts: dict[tuple[str, str], int] = {}
    failures = []
    for before, path_text, start_text, end_text in citations:
        ref = base if before else head
        citation = f"{before}{path_text}:{start_text}" + (f"-{end_text}" if end_text else "")
        if ref not in files:
            listing = git(repo, "ls-tree", "-r", "--name-only", ref)
            if listing is None:
                return [f"cannot read ref {ref}"]
            files[ref] = listing.splitlines()
        path = resolve(path_text, files[ref])
        if path is None:
            side = "before" if before else "after"
            failures.append(f"{citation}: no single matching file in the {side} version")
            continue
        if (ref, path) not in line_counts:
            line_counts[(ref, path)] = len((git(repo, "show", f"{ref}:{path}") or "").splitlines())
        start = int(start_text)
        end = int(end_text) if end_text else start
        if start < 1 or end < start or end > line_counts[(ref, path)]:
            failures.append(f"{citation}: out of range, file has {line_counts[(ref, path)]} lines")
    return failures


def main() -> int:
    if len(sys.argv) != 5:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    repo, base, head, draft_arg = sys.argv[1:]
    draft = sys.stdin.read() if draft_arg == "-" else Path(draft_arg).read_text()

    failures = check(repo, base, head, draft)
    for failure in failures:
        print(failure)
    if failures:
        return 1
    print(f"OK: {len(find_citations(draft))} citations, {prose_words(draft)} words without citations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
