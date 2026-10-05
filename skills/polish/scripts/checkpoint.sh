#!/usr/bin/env bash
# Snapshot the working tree, or restore it to a snapshot, without touching the
# index, HEAD, or stashes. Covers tracked and untracked files; ignored files are
# left alone.
# Usage: checkpoint.sh save            prints a snapshot id
#        checkpoint.sh restore <id>    makes the working tree match the snapshot
set -euo pipefail

usage() {
  echo "usage: checkpoint.sh save | checkpoint.sh restore <id>" >&2
  exit 2
}

cd "$(git rev-parse --show-toplevel)"

# Build a throwaway index of the working tree as it is now, seeded from the real
# index so unchanged files aren't rehashed.
snapshot_index() {
  cp "$(git rev-parse --git-path index)" "$1" 2>/dev/null || true
  GIT_INDEX_FILE=$1 git add -A
}

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

case "${1:-}" in
  save)
    [ $# -eq 1 ] || usage
    snapshot_index "$tmp/now"
    GIT_INDEX_FILE=$tmp/now git write-tree
    ;;
  restore)
    [ $# -eq 2 ] || usage
    tree=$(git rev-parse --verify "$2^{tree}")
    snapshot_index "$tmp/now"
    # Files created since the snapshot: checkout-index won't remove them.
    GIT_INDEX_FILE=$tmp/now git diff --cached --name-only -z --diff-filter=A "$tree" |
      xargs -0 rm -f --
    GIT_INDEX_FILE=$tmp/then git read-tree "$tree"
    GIT_INDEX_FILE=$tmp/then git checkout-index -a -f
    ;;
  *)
    usage
    ;;
esac
