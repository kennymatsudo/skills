#!/usr/bin/env bash
# Fold the staged changes into an unpushed commit and replace its message.
# Usage: fold.sh <commit> <message-file>
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "usage: fold.sh <commit> <message-file>" >&2
  exit 2
fi

target=$(git rev-parse --verify "$1^{commit}")
msg=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")

if git diff --cached --quiet; then
  echo "nothing staged" >&2
  exit 1
fi

if ! grep -qx "$target" <<< "$(git rev-list HEAD --not --remotes)"; then
  echo "refusing: $1 is on a remote or not on this branch" >&2
  exit 1
fi

parent=$(git rev-parse --verify --quiet "$target^" || true)
if [ -n "$(git rev-list --merges "${parent:-$target}..HEAD")" ]; then
  echo "refusing: merge commits between $1 and HEAD" >&2
  exit 1
fi

if [ "$target" = "$(git rev-parse HEAD)" ]; then
  git commit --amend --quiet -F "$msg"
else
  # --fixup=amend rejects -m and -F, so an editor override writes the message.
  # The first line must stay "amend! <old subject>" for autosquash to match it.
  amend=$(mktemp)
  trap 'rm -f "$amend"' EXIT
  { printf 'amend! %s\n\n' "$(git log -1 --format=%s "$target")"; cat "$msg"; } > "$amend"
  GIT_EDITOR="cp $amend" git commit --quiet --fixup="amend:$target"
  GIT_SEQUENCE_EDITOR=: git rebase --quiet --interactive --autosquash --autostash ${parent:---root}
fi

git log --oneline ${parent:+"$parent..HEAD"}
