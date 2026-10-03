---
name: maintain-verification
description: >-
  Audit a repo's verification kit against the code and the running app: check the
  feature map's format, read each feature's source in parallel, drive every
  feature live, re-run planned breaks for changed checks, and fix only the kit's
  own files. Use for "audit the verification kit", "is the feature map current".
  Use build-verification to add to a kit.
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

Run the kit's `check.py`, in its scripts directory, with `--evidence-dir` set to the kit's evidence directory. Fix every error in the map itself: missing or extra index entries, malformed lines, proof commands whose files moved. Keep each warning about stale or missing evidence for step 5.

A kit without `check.py` skips this step; note that in the reply.

Done when `check.py` exits 0 and you have a list of stale sub-features.

## 3. Read the source

Spawn one read-only subagent per feature file, in parallel, on a mid-tier model, with the prompt in `references/reader-prompt.md`. Readers never run the app and never edit.

Done when every feature file has a returned report.

## 4. Reconcile

For each report, spot-check the drift it cites against the code, without re-proving claims it found clean. Collect user-facing surfaces readers found with no feature file; keep only those with a cited source path, and carry each one into triage as a finding. Merge the live recipes into as few app states as practical.

Done when every cited drift is confirmed or dismissed, with the reason.

## 5. Drive every feature live

Follow the kit's own `SKILL.md` to check the instance and drive. Run every sub-feature's proof command at least once, plus the live recipe for any sub-feature marked "No check yet" or "Unreachable". Throughout:

- Run the doctor before the first drive, after any failed drive, and reset or relaunch when the app is wedged in a state the doctor cannot see.
- Confirm evidence files still exist after every cleanup.
- Clean up whatever a failed drive left behind before the next one.
- An "Unreachable" sub-feature stays unreachable only with its blocker and the route tried. If the blocker is gone, it is drift.

For each check whose own code changed since the date on its "Break-tested" line, re-run its planned break the way the verification skill proves a check, or mark it "Not break-tested".

Done when every sub-feature has a live result: passed, failed, or not run with a reason.

## 6. Triage

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

Reply: the outcome; how many features and sub-features were covered from source and live; each fix, by category; each product bug, with its evidence file; and sub-features still not verified, with why.
