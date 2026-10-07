---
name: maintain-verification
description: >-
  Audit a repo's verification kit against its requirements, the code, and the
  running app: map every requirement clause to a check, check the feature map's
  format, read each feature's source in parallel, drive every feature live,
  re-run planned breaks for changed checks, and fix only the kit's own files.
  Use for "audit the verification kit", "is the feature map current", "does
  every requirement have a check". Use build-verification to add to a kit.
disable-model-invocation: true
---

# Maintain verification

You own an honest answer to "can agents still trust this kit?", and the kit fixes that make the answer yes. Cover every feature from source and drive every feature live. Fix the kit; report the product.

## Outcomes

End with exactly one:

- **clean:** every feature covered from source and live, nothing to fix.
- **changed:** kit corrections made and proven, left as one reviewable change.
- **blocked:** coverage could not finish. Say what blocked it.

## 1. Find the kit

Look for `verify-*/rules.md` in the repo's skills directories. Several: ask which. None: stop and point the user at the verification skill.

Done when you have the kit path and have read its `SKILL.md`, `rules.md`, and `features/README.md`.

## 2. Run the mechanical check

Run the kit's `check.py`, in its scripts directory, with `--evidence-dir` set to the kit's evidence directory. Fix every error in the map itself: missing or extra index entries, malformed lines, proof commands whose files moved. Keep each warning about stale or missing evidence for step 6.

A kit without `check.py` skips this step; note that in the reply.

Done when `check.py` exits 0 and you have a list of stale sub-features.

## 3. Map the requirements

Skip this step when the kit has no `features/requirements.md`, and say so in the reply. Its format is under "Requirements coverage" in the feature map reference of the build-verification skill. A green run proves only the claims someone listed; this step finds requirements that never became a sub-feature.

Read the source the file names and note when it was last updated. If neither the source nor `features/` changed since the file's checked date, skip to step 4 and carry the open items into the reply.

1. Break each requirement into clauses: each state, direction, count, or ordering it names. "Messages arrive in order exactly once" is three clauses. A requirement too vague to break down gets a proposed edit asking its owner for the clauses. Add requirements the design docs state that the source does not.
2. Give each clause the first outcome that fits:
   - A sub-feature proves it: `ids: <IDs>`.
   - The team knows the requirement and the source lacks it: `not in source`, and propose adding it.
   - The source contradicts the code, a design doc, or the agreed scope: add no check; record it under "Conflicts with the source", naming both sides, as an edit its owner can paste.
   - The expected behavior is undecided: `blocked on decision: <the decision>`.
   - None of these: add the sub-feature to its feature file with `No check yet.` and set `No check yet`.
3. Go the other way: a sub-feature no clause, design doc, or scope needs gets a proposed removal or `out of scope: <reason>`.
4. Update the checked date.

Hand fact lookups (whether a change is merged, where the code decides a behavior) to subagents on a mid-tier model, each answer carrying its `path:line` or URL, and check that evidence. Split clauses and choose outcomes yourself; a summary that drops a clause is the failure this step exists to catch. Never edit the requirements source; its owner decides.

Done when every clause and every sub-feature has exactly one outcome, and `check.py` exits 0.

## 4. Read the source

Spawn one read-only subagent per feature file, in parallel, on a mid-tier model, with the prompt in `references/reader-prompt.md`. Readers never run the app and never edit.

Done when every feature file has a returned report.

## 5. Reconcile

For each report, spot-check the drift it cites against the code, without re-proving claims it found clean. Collect user-facing surfaces readers found with no feature file; keep only those with a cited source path, and carry each one into triage as a finding. Merge the live recipes into as few app states as practical.

Done when every cited drift is confirmed or dismissed, with the reason.

## 6. Drive every feature live

Follow the kit's own `SKILL.md` to check the instance and drive. Run every sub-feature's proof command at least once, plus the live recipe for any sub-feature marked "No check yet" or "Unreachable". Throughout:

- Run the doctor before the first drive, after any failed drive, and reset or relaunch when the app is wedged in a state the doctor cannot see.
- Confirm evidence files still exist after every cleanup.
- Clean up whatever a failed drive left behind before the next one.
- An "Unreachable" sub-feature stays unreachable only with its blocker and the route tried. If the blocker is gone, it is drift.

For each check whose own code changed since the date on its "Break-tested" line, re-run its planned break the way the verification skill proves a check, or mark it "Not break-tested".

Done when every sub-feature has a live result: passed, failed, or not run with a reason.

## 7. Triage

Sort every finding:

- **Map drift:** the feature file describes the app wrongly. Fix the file.
- **Kit gap:** working behavior the kit cannot drive or read. Fix the tool, following `rules.md`, and re-drive it live.
- **Product bug:** the app is broken. Record it with the failing step and evidence. Never edit product code or soften the map to hide it.

Run `check.py` again after the fixes.

Done when every finding has a category and every kit fix has been driven live.

## Guardrails

- Edit only files inside the kit and the tools it owns.
- Drive and stop only instances this run started, or ones the user named.
- Run an action with a real or shared side effect only after the user's OK in this session.
- Ask before committing or opening a pull request.

Reply: open with what the user should do next in plain English, grouped by who acts (the requirements owner, a developer, the user) and ordered by risk. Write each item as the behavior a user would notice, not a clause or ID, and link every issue and pull request with its repo. Then the detail: the outcome; how many features and sub-features were covered from source and live; requirement clauses with no check, and proposed edits to the source; each fix, by category; each product bug, with its evidence file; and sub-features still not verified, with why.
