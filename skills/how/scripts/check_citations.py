#!/usr/bin/env python3
"""Check that every path:line citation in a draft points at a real file and line range.

Usage: check_citations.py <repo-root> <draft-file | ->
Exits 1 if any citation is broken or the draft has none.
"""

import re
import subprocess
import sys
from pathlib import Path

CITATION = re.compile(r"(?<![\w/.-])([\w./-]+\.\w+):(\d+)(?:-(\d+))?")
URL = re.compile(r"\w+://\S+")


def find_citations(draft: str) -> list[tuple[str, str, str]]:
    return CITATION.findall(URL.sub("", draft))


def tracked_files(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files"], capture_output=True, text=True
    )
    return result.stdout.splitlines() if result.returncode == 0 else []


def resolve(repo_root: Path, path_text: str, tracked: list[str]) -> Path | str:
    if (repo_root / path_text).is_file():
        return repo_root / path_text
    matches = [f for f in tracked if f.endswith("/" + path_text)]
    if len(matches) == 1:
        return repo_root / matches[0]
    if matches:
        return f"ambiguous, matches {len(matches)} files"
    return "file not found"


def check(repo_root: Path, draft: str) -> list[str]:
    citations = find_citations(draft)
    if not citations:
        return ["no path:line citations found"]

    tracked = tracked_files(repo_root)
    failures = []
    line_counts: dict[Path, int] = {}
    for path_text, start_text, end_text in citations:
        citation = f"{path_text}:{start_text}" + (f"-{end_text}" if end_text else "")
        path = resolve(repo_root, path_text, tracked)
        if isinstance(path, str):
            failures.append(f"{citation}: {path}")
            continue
        if path not in line_counts:
            line_counts[path] = len(path.read_text(errors="replace").splitlines())
        start = int(start_text)
        end = int(end_text) if end_text else start
        if start < 1 or end < start or end > line_counts[path]:
            failures.append(f"{citation}: out of range, file has {line_counts[path]} lines")
    return failures


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    repo_root = Path(sys.argv[1])
    draft = sys.stdin.read() if sys.argv[2] == "-" else Path(sys.argv[2]).read_text()

    failures = check(repo_root, draft)
    for failure in failures:
        print(failure)
    if failures:
        return 1
    print(f"OK: {len(find_citations(draft))} citations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
