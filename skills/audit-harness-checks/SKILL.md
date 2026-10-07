---
name: audit-harness-checks
description: >-
  Periodic sweep of a repo's test harness for checks that would still pass if
  what they guard broke: hollow or weakened unit tests, scenarios that judge
  something other than stored state, probes that cannot fail, docs that point
  at commands that no longer exist, and tests that bless a useless check.
  Breaks each check in a scratch copy, has subagents find and then
  independently verify problems, fixes the clear-cut ones on a branch, and
  ends with a short readout. Use for "audit the harness checks", "are our
  tests fake". Use review-tests for one branch's new tests, and
  maintain-verification to drive the kit live.
disable-model-invocation: true
---

# Audit harness checks

You own one answer: would each check in this harness go red if the behavior it guards broke? A check that cannot fail, and a unit test that passes a check that cannot fail, are the worst outcomes here, because every run then reports a pass nobody earned.

The harness is the repo's end-to-end verification layer: a kit the build-verification skill set up (`verify-*/rules.md` in a skills directory), or else the harness the repo's agent instructions name. If neither exists, stop and say so. Never run live scenarios or touch shared or production systems; a claim only a live run can settle goes to the developer as a named scenario and break to run.

## 1. Gather the hard facts

From the harness's docs and agent instructions, find: where its check code and unit tests live, the unit suite command, how checks are named, the rules it promises (the kit's `rules.md`, or its trust or verification doc), any coverage map or status file, and the docs and skills that tell agents what counts as proof. Use the names you find in every command below.

Then run, in parallel where you can, and keep each output:

- The unit suite. If it fails, stop and report the failing tests; an audit of a red suite measures nothing.
- For Python check code, the three scripts in this skill's `scripts/` directory. Run them; read their `--help` only for flags.
  - `break_checks.py --harness <dir> --suite "<suite command>" --match "<check name regex>"`. It makes each check function return its all-clear value in a scratch copy and runs the suite. `SURVIVED` means no unit test can tell that check from a broken one. Add `--copy <path>` for anything else the suite imports.
  - `smells.py <dirs>`: leads for tests with no assertion, existence-only assertions, self-comparisons, skips, and broad excepts that swallow a failure.
  - `weakened.py --path <dir> --match "<regex>"`: every deleted test, removed assertion, new skip, and changed check since the last `Audit harness checks` commit, else 30 days.
- For other languages, do by hand what the scripts do: the repo's mutation tool scoped to the check functions if it has one, else a stub of each check's all-clear return in a scratch copy, and `git diff` since the last audit for removed assertions and new skips.
- Every probe and scenario runner's `--help`, for the commands and names that exist today.

Done when the suite is green and you hold each output, or the reason one could not run.

## 2. Find, in parallel

Split the harness into slices: one per feature area with its checks and their unit tests, one for UI drivers, one for the probe and read layer, and one for the verification docs and skills. Spawn one read-only finder per slice, on a mid-tier model, with the prompt in `references/finder.md` and the rubric in `references/rubric.md`. Give each finder the step 1 lines that fall in its slice. Every `SURVIVED` check and every `weakened.py` lead must come back with a finding or a reason it is fine.

Done when every slice is listed with its finder's return, and every finding has a `file:line`, quoted code, a rubric ID, and a "passes even when ... because ..." line. Drop any finding without one.

## 3. Verify, independently

Spawn verifiers on a mid-tier model with `references/verifier.md`, batching findings by slice. A verifier gets each finding's location, claim, and failure scenario, never the finder's reasoning, because a finder wants its finding to be real. Each finding returns `CONFIRMED` with the command and output that show the check staying green while broken, `REFUTED` with the code that defeats it, or `PLAUSIBLE` with the live scenario and break that would settle it.

Done when every finding is listed with its verifier's verdict and evidence. A finding with no verdict is neither fixed nor reported, and the readout's counts come only from these verdicts.

## 4. Fix and decide

Decide in the main session. Rank confirmed findings by what the guarded check protects, using the coverage map's risk or launch rows when the harness has one, highest risk first.

Fix now, on a new branch `audit-harness-checks/<date>`:

- A check with no failing-case test: add the test that feeds the broken case.
- A check that passes on empty, on an exception, or on the code's own output, when the design says unambiguously what it should check: tighten it.
- A command, flag, scenario name, probe subcommand, or path in a doc or skill that no longer exists: correct it.
- A coverage rating stronger than its evidence: lower it and name the planned break that would earn it back.
- A check that misled before the fix: record it where the harness tracks known gaps, if it has such a place.

Prove each new or changed test red-green: it fails against the broken copy and passes against the real code. A fix to a check needs a test too, one that fails when the fix is reverted. Then hand every new or changed test to a fresh verifier with the same break, so the audit cannot add a useless test of its own.

Leave for the developer, with a recommendation each: deleting a test or check, changing an expected value, a new check, invariant, or probe command, a change to what a read returns when it succeeds, anything `PLAUSIBLE`, and any fix in another repo.

Never loosen an assertion or change an expectation to turn a run green; a bug stays failing with the correct expectation and goes to the ticket tracker.

Rerun the unit suite and `weakened.py --since <branch base>` on your own diff; any lead it prints must be one you justify in the readout. Commit only this audit's hunks, titled `Audit harness checks: <one-line summary>`; the next audit finds its starting point from that title. Do not push.

Done when the suite is green, every fix has a red-green proof and a verifier's `CONFIRMED`, and the commit exists.

## Readout

The reader acts on this and nothing else, so keep it short, in plain words, and free of rubric IDs. Every item says what was wrong, what breakage it would have hidden, and what was done or needs doing.

```
Audit harness checks, <date>: <one line: can we trust the suite, and the biggest risk>
Since <short sha of weakened.py's starting commit> · <n> checks broken, <n> caught · <n> findings, <n> confirmed, <n> refuted

Needs you
1. <action>: <what breakage this hides, in user terms>. Recommend: <choice and why>.

Fixed (commit <sha> on audit-harness-checks/<date>)
- <check or test> could pass when <broken behavior>; <what changed>. Guards <feature or risk>.

Updated
- <file>: <what changed and why, one line>

Run live to settle
- <scenario> with <break>: would show whether <claim>.
```

Omit an empty section. "Needs you" holds at most five items, ordered by risk; list the rest in the commit body and end the section with `<n> lower-risk items in the commit body`. Refuted findings appear only in the count.

Reply: the readout.
