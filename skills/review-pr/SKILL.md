---
name: review-pr
description: >-
  Review a pull request for defects it introduces: gather the ticket's intent,
  map who calls and consumes the changed code, run focused reviewers in
  parallel, then prove each finding with a failing test or a code trace and
  drop the rest. Reports a short ranked list with no nits, and posts to the PR
  only when asked. Use for "review PR #123", "review this PR", "find bugs in
  this branch", "is this safe to merge". Use walkthrough to understand a PR
  without judging it, and review-design or review-tests for design or test
  quality.
---

# Review PR

You own a short list of defects this PR introduces, each proven, that the author would thank you for. Two findings that hold beat ten the author has to argue with. "No findings" is a valid result.

Run every step in order and write every file, even when the PR looks simple. A single careful read is what the user had without this skill; the lenses, the caller map, and the separate checkers are what catch the bugs a single read misses. If a step can't run, say which and why in the report.

## The bar

A finding names a concrete input or state, reachable from code that exists, that makes the changed code do one of these:

- **High:** lose or corrupt data, open a security hole, cause an outage, get money wrong, or break a caller or consumer that ships today.
- **Medium:** return a wrong result, crash, or miss a requirement the ticket states, for a user or caller who can hit it.

Its cause is a line the PR added, changed, or removed. Everything else is below the bar and is never reported, not even as an optional section: style, naming, formatting, docs, "consider" suggestions, refactors, performance without a measured or obviously large cost, what a linter or type checker already catches, problems that existed before the PR, and hypotheticals that need an input nothing produces.

Run this skill's script from the repo root as `python3 <skill-dir>/scripts/review.py`, with the absolute path of this skill's directory, and keep its files in a run directory made with `mktemp -d` outside the repo.

## 1. Find the change

Accept a PR number or link, or a branch. With none given, use the current branch's PR.

- **A PR:** `gh pr view <pr> --json number,title,body,url,author,isDraft,baseRefOid,headRefOid,commits,closingIssuesReferences,comments,reviews,statusCheckRollup`, or the session's code host tool. Fetch the head with `git fetch origin pull/<number>/head`.
- **A branch with no PR:** the base is the default branch (`git symbolic-ref --short refs/remotes/origin/HEAD`, else `origin/main`) and the head is the branch tip. Uncommitted work is out of scope; say so if there is any.

Run `review.py context <run-dir> --base <base> --head <head>`. It writes `context.md` with the diff numbered by head line, and `changed.json` for step 4. If the diff only touches docs, generated files, or lockfiles, say there is no code to review and stop.

Add a worktree at the head with `git worktree add --detach <run-dir>/head <head>`, so the user's checkout never changes. Set it up to run one existing test the way the repo's agent instructions or README say. Never point it at shared databases, queues, or remote services. If setup needs those, or takes more than a few minutes, record `tests can't run here: <reason>` in `context.md` and continue; checkers then prove by code trace.

Done when `context.md` exists and names either the working test command or why tests can't run.

## 2. Gather intent

Write `<run-dir>/intent.md` with three sections:

- **Requirements.** Numbered, from linked tickets: IDs in the title, branch, description, or commits, plus closing issue references. List the session's tools, including ones the harness names but loads on demand, and look each ID up with any that can search a ticket tracker. Report a tracker as unsearched only after finding no tool for it or a lookup failing, and say which. With no ticket, take the requirements from the description and say so.
- **Author's claims.** What the description and commits say the change does, does not change, and was tested with, each phrased as a claim to check ("description says the old endpoint still works"). Leave out the author's judgments of safety or quality; they make reviewers miss bugs.
- **Already raised.** Open review threads and failing checks, one line each, so nobody repeats them.

Done when every requirement is numbered with its source, or the file says no requirements source was found.

## 3. Map the blast radius

Write `<run-dir>/map.md`. List every symbol the diff changes: functions, classes, endpoints, schemas and migrations, config keys, events and messages, CLI flags. For each, give:

- **Upstream:** who calls it or produces its input, as `path:line` from `git grep <name> <head>`.
- **Downstream:** who consumes what it returns, writes, or emits: callers using the result, readers of the table or event, API clients, other services. For names that cross a repo boundary (routes, topics, table names), search other repos with the session's code search tool if there is one, else mark "other repos unsearched".

Paths only, no pasted code; reviewers open what they need.

Done when every changed symbol has an upstream line and a downstream line, each with locations, "none found", or "unsearched".

## 4. Review

Run each lens yourself, one at a time: read its file, follow `references/reviewer-prompt.md` as if it were your prompt, and write `<run-dir>/review-<lens>.json` before starting the next. One reviewer holding the whole diff and map finds as much as parallel reviewers, at a fraction of the cost.

When `context.md` says the diff is over the limit, split the changed files into groups that call each other, and spawn one subagent per group on a mid-tier model with the reviewer prompt, running all four lenses on its group: fill in the skill's directory for `{SKILL_DIR}`, name the group's files in the scope note, and set the output path to `<run-dir>/group-<n>-<lens>.json`. Merge each lens's group files into its `review-<lens>.json`.

| Lens | File |
|---|---|
| Correctness inside the diff | `references/lens-diff.md` |
| Contracts with callers and consumers | `references/lens-contracts.md` |
| Gaps against the requirements | `references/lens-intent.md` |
| Security and data | `references/lens-security.md` |

Then run `review.py collect <run-dir>`. It drops findings whose cause is not a changed line, groups findings that share a cause, and writes one `batch-<group>.md` per group. If it reports a missing or malformed review file, rerun that lens.

Done when `collect` prints its counts and batch files.

## 5. Prove each group

Spawn one checker subagent per batch file, in parallel, on a mid-tier model, with the prompt in `references/checker-prompt.md`, the batch file's path, the worktree path, the test command or the reason tests can't run, and the output path `<run-dir>/check-<group>.json`. Add nothing else; the batch is all a checker should see, so it judges the code rather than the reviewer.

Then run `review.py status <run-dir>`. It fails if any group is unanswered or an answer is malformed; respawn that checker.

Done when `status` passes.

## 6. Settle and rank

Run `review.py findings <run-dir>`. It prints kept groups (Proven or Holds) ranked by severity, Proven first, then the rest. For each kept group:

- **Read its code yourself** along the scenario's path, from the input to the wrong outcome. Drop it if the path breaks somewhere, citing where.
- **Apply the bar again.** Would the author change the code because of it? A finding that names no reachable input, or whose harm is cosmetic, drops as below the bar.
- **Check it against "Already raised".** Drop repeats.

Keep at most seven. When more survive, report the top seven and the count of the rest.

Done when every group in the `findings` output is reported or dropped with a one-line reason.

## 7. Report

Write the report in the reply. Open with a tally ("3 findings (1 high, 2 medium; 2 proven by a failing test). 9 candidates dropped: 4 below the bar, 3 refuted, 2 outside the diff."). Never approve, never say "LGTM", and never grade the PR overall. The report has no side-notes section, whatever reply style applies elsewhere: items below the bar appear nowhere, including under "also found" or "your call".

For each finding, in rank order:

- **Title** naming what breaks, such as "Refund retries charge the card twice".
- Severity, Proven or Holds, and the cause as `path:line`.
- **What happens:** the scenario, from input to wrong outcome, in two sentences.
- **Proof:** the command and the failing output in one line, or the cited trace.
- **Fix:** the smallest change, in one line.

Then **Not checked:** each source you couldn't search (a ticket tracker with no tool, other repos, tests that couldn't run). Then **Checked and fine:** one line naming the risky areas reviewers examined and left alone, so the author knows what was covered.

Offer to post the findings to the PR.

Done when every kept finding has its five parts and the report names everything not checked.

## 8. Post, only when asked

Only on an explicit request to post. Post one inline comment per finding on its cause line, through `gh` or the session's code host tool, as a single review with the comment event, never approve or request changes. Each comment states what breaks and the scenario in two sentences, the proof in one, and the fix in one, with no greeting, praise, or "nit". Show the user the posted review's link.

Done when the review link is shown.

## Cleanup

Remove the worktree with `git worktree remove --force <run-dir>/head` and delete the run directory. Done when `git worktree list` no longer shows it.

Reply: the report from step 7, and the review link if you posted.
