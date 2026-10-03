---
name: commit
description: >-
  Stage changes and commit them with a short title and a scannable body,
  folding follow-up changes into unpushed commits they belong to. Use for
  "commit this", "commit my changes", "make a commit", "amend that". Use
  squash to restructure a branch's existing commits.
---

# Commit

You own a history where each commit is one concern, described in as few words as a reader needs.

## 1. Read the changes

Run `git status`, `git diff`, `git diff --staged`, `git log -10 --format=%s`, and `git log --oneline HEAD --not --remotes` (the unpushed commits).

Done when you know what changed, the repo's subject style, and which commits are unpushed. If nothing changed, say so and stop.

## 2. Plan the commits

Group the changes by concern, using as few commits as tell the story. Supporting edits (tests, docs, fixtures, formatting) ride with the change they support. Split only when a concern could be reverted or reviewed on its own.

For each group, pick a home:

- **Fold** into an unpushed commit when the group continues that commit's concern, such as a fix to code it added or a follow-up the user asked for.
- **New commit** otherwise.

Keep each file whole in one group, since partially staged files make pre-commit hooks stash and restore the rest. Read untracked files, and leave out credentials, build output, and scratch files.

Done when every changed file has a home or is named as left out.

## 3. Write each message

Write from the staged diff, and take the reason from the conversation. If neither shows why, leave the why out rather than guessing.

- **Title.** Imperative, completing "If applied, this commit will…". Capitalized, no period, about 50 characters, 72 at most. Name the behavior that changed, not the symbol. Match the repo's prefix style only when most recent subjects use one.
- **Body.** Skip it when the title says enough. One concern with a reason worth keeping gets a blurb of one to three sentences. Several distinct parts get short bullets, one per part. Wrap at 72.
- **Leave out** tests, docs, formatting, lint, and dependency bumps unless they are the whole change. Also leave out file lists, counts, restatements of the diff, process narration ("This commit…", "Per review"), hedging ("should fix"), and co-author or tool-attribution trailers.
- **A fold** gets a message rewritten to cover the combined change, as if written once.

Done when every planned commit has a message that passes these rules.

## 4. Commit

Ask and wait only when the plan splits the diff into more than one commit or the diff may hold secrets or personal data. Show each message in a code block, marked new or fold with its target.

For each commit, stage its files with `git add <files>`, then:

- **New:** `git commit -F <message-file>`.
- **Fold:** run `scripts/fold.sh <commit> <message-file>`. It refuses pushed targets.

If a pre-commit hook rewrites files and aborts, re-stage those files and retry once. Never use `--no-verify`. If a rebase stops on a conflict, run `git rebase --abort` and report.

Done when `git status` shows only what you left out and `git log` shows the planned commits.

**Reply:** the resulting `git log --oneline` for the commits made or rewritten, and anything left out.
