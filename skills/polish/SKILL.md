---
name: polish
description: >-
  Polish a finished branch in one run: apply the strong findings from a design
  review, then review the tests, rename identifiers, cut code slop, clean up
  comments, and tidy the docs the branch touches, leaving every change
  uncommitted for review. Use for "polish", "polish my branch", "I'm done
  implementing". Use commit afterward.
disable-model-invocation: true
---

# Polish

You own a branch that reads as if written carefully the first time, behaving as it did before except where a strong design finding changed it, and a report that lets the user check every change before committing.

Leave the result uncommitted. Never commit, stash, reset, or check out files; roll back only with this skill's checkpoint script.

## Scope

By default, cover the branch: everything that differs from its merge base with the default branch, whether committed, staged, unstaged, or untracked. Find the default branch with `git symbolic-ref --short refs/remotes/origin/HEAD`, else `origin/main`, else `origin/master`. Take `git diff $(git merge-base HEAD <default>)` plus untracked files from `git status --porcelain`.

Narrow it when the user asks:

- **Uncommitted:** `git diff HEAD` plus untracked files.
- **Staged:** `git diff --staged` only.
- **A path:** only that path.

Pass this scope to every step. Tell the user the scope in one line before going further, such as "Scope: branch `foo` vs `origin/main`, 12 files".

## Steps and how to run them

| Step | Skill | Runs on |
|---|---|---|
| 1. Design | review-design | the scope |
| 2. Tests | review-tests | test files in scope |
| 3. Names | rename-variables | code in scope |
| 4. Code slop | unslop, code mode | code in scope |
| 5. Comments | clean-up-comments | code in scope |
| 6. Docs | trim, then unslop prose mode | markdown and text files in scope |

The order matters: refactors land before anything polishes them, names settle before comments mention them, and dead code goes before its comments get rewritten.

Find each skill's `SKILL.md` in this skill's parent directory first, resolving symlinks, then in the harness's other skills directories. Load it and follow it yourself, in this session. Don't hand a step to a subagent: most steps spawn their own subagents, and a subagent often can't. A skill you can't find is reported as skipped, not installed; the other steps still run.

Where a step ends by asking which finding to act on, polish answers for the user as below. Questions about intended behavior, such as review-tests asking for a contract source, still go to the user. Keep only each step's counts, flags, and reported bugs; the final report needs nothing else.

Run `<this skill's directory>/scripts/checkpoint.sh save` before step 1 and after every step, and record each id. It snapshots the working tree, including untracked files, without touching the index.

## 1. Set up

Create a run directory with `mktemp -d` outside the repo. Run the repo's typecheck, lint in check-only mode, and the tests for the files in scope, and record what fails: that is the baseline for step 8. Save the start checkpoint and tell the user its id.

Done when you have the scope's file list, the baseline, the start checkpoint id, and each step's skill found or marked not installed. If the scope is empty, say so and stop.

## 2. Design

Run review-design through its report, on this run's scope. Its report-only rule gives way here: apply every finding that is strong and not contested, in rank order, using its implement-here path. For each:

1. Re-read the lines it cites. If an earlier refactor changed them, mark it superseded and skip it.
2. Save a checkpoint.
3. Implement it: pin the behavior, and confirm the pin goes red when you break the code it covers, since a pin that can't fail lets any refactor through. Then change the code in small steps that keep it passing.
4. Keep it when the pinning test passes and no check fails beyond the baseline. Otherwise restore the checkpoint with `checkpoint.sh restore <id>` and mark it reverted, with the reason.

Done when every strong finding is applied, reverted, or superseded, and every other finding is listed as unapplied.

## 3. Tests

Run review-tests. The pinning tests from step 2 are in scope like any other new test.

Done when review-tests reaches its report.

## 4. Names

Run rename-variables on this run's scope.

Done when rename-variables reaches its reply.

## 5. Code slop

Run unslop in code mode on the code files in scope.

Done when unslop reaches its code reply.

## 6. Comments

Run clean-up-comments.

Done when clean-up-comments reaches its report.

## 7. Docs

If the scope holds markdown or text files, run trim on each, then unslop in prose mode.

Done when each doc file in scope is trimmed and unslopped, or the step is marked as having no docs.

## 8. Check

Rerun the step 1 checks. For each new failure, find the first step whose checkpoint shows it by diffing checkpoints with `git diff <before-id> <after-id>`, and report it against that step. Don't fix it here.

Done when every check passes or fails only where the baseline failed, or each new failure is tied to a step.

Reply:

- One line per step: done, skipped (with why), or nothing to change, plus its main counts.
- Design: each finding applied, reverted (with why), superseded, or unapplied, by title. Offer a handoff prompt for any unapplied one.
- Every bug, flag, and hard-to-follow spot the steps reported, with `path:line`.
- The check results against the baseline.
- The start checkpoint id, with `checkpoint.sh restore <id>` to undo the whole run and `git diff <id-before> <id-after>` to see one step's changes.
- Next: review the diff, then commit.
