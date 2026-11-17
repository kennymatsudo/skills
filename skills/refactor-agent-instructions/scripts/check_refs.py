#!/usr/bin/env python3
"""Report the size, imports, and path references of agent instruction files.

Usage: check_refs.py [--root <repo-root>] <file> [<file> ...]

For each file, prints its line and byte count, every @import (a line-level
`@path` outside code, as Claude Code reads them), and every backticked token
that looks like a repo path. A path resolves if it exists relative to the
file's directory or to the repo root (default: the git toplevel, else the
current directory).

Errors (exit 1): an @import whose target is missing. A broken import silently
drops the instructions it was meant to load.
Warnings (exit 0): a backticked path that doesn't resolve. It may be stale, or
it may be an example, a glob, or a path created at build time; check by hand.

Run it on the files before a rewrite and again after: the imports should match
and no new warning should appear.
"""

import re
import subprocess
import sys
from pathlib import Path

FENCED_BLOCK = re.compile(r"^[ \t]*```.*?^[ \t]*```", re.MULTILINE | re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]+`")
# Claude Code treats @path as an import anywhere outside code, but in prose an
# @ is usually an email or a handle, so only count tokens that look like files.
IMPORT = re.compile(r"(?<![\w.])@((?:~|\.{1,2})?/?[\w.\-/]+\.[\w]+|[\w.\-/]*/[\w.\-/]+)")
BACKTICKED = re.compile(r"`([^`\s<>*{}$]+)`")
URL = re.compile(r"^[a-z]+://")


def repo_root(default: Path) -> Path:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True, cwd=default,
        )
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return default


def looks_like_path(token: str) -> bool:
    if URL.match(token) or token.startswith("-") or " " in token:
        return False
    return "/" in token or bool(re.search(r"\.(md|json|ya?ml|toml|py|ts|js|sh|txt)$", token))


def resolves(token: str, file_dir: Path, root: Path) -> bool:
    token = token.rstrip(".,:;)")
    if token.startswith("~/"):
        return Path(token).expanduser().exists()
    candidates = [file_dir / token, root / token.lstrip("/")]
    return any(p.exists() for p in candidates)


def check(path: Path, root: Path) -> int:
    text = path.read_text(encoding="utf-8")
    lines = text.count("\n") + (0 if text.endswith("\n") else 1)
    print(f"{path}: {lines} lines, {len(text.encode('utf-8'))} bytes")

    prose = INLINE_CODE.sub("", FENCED_BLOCK.sub("", text))
    errors = 0
    for target in sorted(set(IMPORT.findall(prose))):
        ok = resolves(target, path.parent, root)
        print(f"  import @{target}: {'ok' if ok else 'MISSING'}")
        errors += not ok

    no_fences = FENCED_BLOCK.sub("", text)
    for token in sorted(set(BACKTICKED.findall(no_fences))):
        if looks_like_path(token) and not resolves(token, path.parent, root):
            print(f"  warning: `{token}` does not resolve")
    return errors


def main(argv: list[str]) -> int:
    root = None
    if len(argv) >= 2 and argv[0] == "--root":
        root, argv = Path(argv[1]), argv[2:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip(), file=sys.stdout if argv else sys.stderr)
        return 0 if argv else 2
    errors = 0
    for name in argv:
        path = Path(name).resolve()
        if not path.is_file():
            print(f"{name}: not a file", file=sys.stderr)
            errors += 1
            continue
        errors += check(path, root or repo_root(path.parent))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
