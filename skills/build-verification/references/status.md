# Verification status

When the repo has no current results home, copy this default into the kit as `status.md` and link it from `features/README.md`. Keep current results out of feature definitions. Delete an empty section only when the kit has no use for it.

```markdown
# Verification status

## Known failing checks

None yet.

## Where a pass can mislead

None yet.

## Untested cases

None yet.

## Latest results

No runs yet.
```

For each run, record the date, check or scenario, the exact version each component ran, what passed or failed in user terms, what was not proved, and the evidence path. For Git checkouts, include commit, branch, and dirty state. Record an environment stop separately from a failed product check. Keep a result attributed to the version tested; remove a known failure only after the affected check passes on the version where it was tracked.
