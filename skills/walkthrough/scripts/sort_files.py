#!/usr/bin/env python3
"""Tag each file a change set touches, so mechanical changes can be set aside.

Usage: sort_files.py <repo-root> <base-ref> <head-ref>

Prints one line per file: tag, lines added and removed, path, and a note.
Tags, first match wins:
  renamed      pure rename, content unchanged
  whitespace   only whitespace changed
  moved        most added lines were removed elsewhere in the same change, or
               most removed lines were added elsewhere
  generated    lock files, snapshots, minified or vendored files
  test         test files
  docs         markdown and other prose
  core         everything else
"""

import re
import subprocess
import sys
from collections import defaultdict

GENERATED = re.compile(
    r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Pipfile\.lock|"
    r"Cargo\.lock|go\.sum|Gemfile\.lock|composer\.lock|uv\.lock)$"
    r"|\.min\.(js|css)$|\.snap$|(^|/)(vendor|dist|build|__generated__|generated)/"
)
TEST = re.compile(
    r"(^|/)(tests?|__tests__|spec|specs)/|(^|/)test_[^/]+$|_test\.\w+$|\.(test|spec)\.\w+$|Tests?\.\w+$"
)
DOCS = re.compile(r"\.(md|mdx|rst|txt|adoc)$", re.IGNORECASE)
MOVED_SHARE = 0.8
MIN_LINE = 8  # shorter lines like "}" or "return" match by chance


def git(repo: str, *args: str) -> str:
    result = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def numstat(repo: str, base: str, head: str, *flags: str) -> dict[str, tuple[int, int]]:
    stats = {}
    for line in git(repo, "diff", "-M", "--numstat", *flags, base, head).splitlines():
        added, removed, path = line.split("\t", 2)
        # Renames print as "old => new" or "dir/{old => new}/file"; keep the new path.
        path = re.sub(r"\{[^}]* => ([^}]*)\}", r"\1", path).replace("//", "/")
        path = path.split(" => ")[-1]
        stats[path] = (int(added) if added != "-" else 0, int(removed) if removed != "-" else 0)
    return stats


def renames(repo: str, base: str, head: str) -> dict[str, tuple[str, int]]:
    found = {}
    for line in git(repo, "diff", "-M", "--name-status", base, head).splitlines():
        parts = line.split("\t")
        if parts[0].startswith("R"):
            found[parts[2]] = (parts[1], int(parts[0][1:]))
    return found


def moved_shares(repo: str, base: str, head: str) -> dict[str, float]:
    """Per file, the larger share of its added lines removed elsewhere or its removed lines added elsewhere."""
    lines: dict[str, dict[str, list[str]]] = defaultdict(lambda: {"+": [], "-": []})
    old_path = new_path = None
    for line in git(repo, "diff", "-M", "-U0", base, head).splitlines():
        if line.startswith("--- "):
            old_path = line[6:] if line.startswith("--- a/") else None
        elif line.startswith("+++ "):
            new_path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("@@"):
            continue
        elif line[:1] in "+-" and len(line[1:].strip()) >= MIN_LINE:
            # Deleted files have no new path, so key them by the old one.
            lines[new_path or old_path][line[0]].append(line[1:].strip())
    all_added = {l for f in lines.values() for l in f["+"]}
    all_removed = {l for f in lines.values() for l in f["-"]}
    shares = {}
    for path, side in lines.items():
        added_share = sum(l in all_removed for l in side["+"]) / len(side["+"]) if side["+"] else 0
        removed_share = sum(l in all_added for l in side["-"]) / len(side["-"]) if side["-"] else 0
        shares[path] = max(added_share, removed_share)
    return shares


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    repo, base, head = sys.argv[1:]

    stats = numstat(repo, base, head)
    whitespace_stats = numstat(repo, base, head, "-w")
    renamed = renames(repo, base, head)
    moved = moved_shares(repo, base, head)

    for path, (added, removed) in sorted(stats.items()):
        note = ""
        if path in renamed:
            note = f"from {renamed[path][0]}"
        if path in renamed and renamed[path][1] == 100:
            tag = "renamed"
        elif path not in whitespace_stats and (added or removed):
            # git diff -w leaves out files whose only changes are whitespace.
            tag = "whitespace"
        elif moved.get(path, 0) >= MOVED_SHARE and added + removed >= 3:
            tag, note = "moved", f"{moved[path]:.0%} of changed lines appear on the other side elsewhere"
        elif GENERATED.search(path):
            tag = "generated"
        elif TEST.search(path):
            tag = "test"
        elif DOCS.search(path):
            tag = "docs"
        else:
            tag = "core"
        print(f"{tag:<10}  +{added:<5} -{removed:<5}  {path}" + (f"  ({note})" if note else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
