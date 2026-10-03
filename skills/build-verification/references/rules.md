# Verification rules

Copy this file into the kit as `rules.md`. Replace each `<...>` with what the repo uses, and delete any section for a kind of piece the kit does not have yet. Every piece in the kit follows these rules. A piece that cannot follow one names the exception in its own help text and in the feature file that uses it.

## Code under test

Every result records which code produced it: commit, branch, whether the tree was dirty, and whether that commit is on the main branch. Anything unreadable counts as not main. A pass on a commit that is not on main is reported with its branch and extra commits, never as a pass on main.

## Doctor

`<doctor command>` is read-only. It answers one question: is this instance worth driving?

- It reports whether each process is up, which code each one runs, which ports it holds, and whether auth is valid.
- Exit 0 means ready. Exit 1 means not ready, with each reason on its own line. Exit 2 means it could not tell.
- It prints one exact ready line, `<ready line>`, that tools may match on. Change the line only together with every tool that matches it.

## Probes

A probe answers a question about current state. `<probe command> <question> <args>`.

- **Read-only.** Database reads run in a read-only transaction. HTTP calls are GET only.
- **One JSON object on stdout.** Concise by default, with `--full` for the raw object.
- **Exit codes.** 0 answered. 1 not found, with `{"not_found": ..., "hint": ...}`. 2 could not answer, with `STOPPED: <reason>` on stderr.
- **Hints.** `next` lists follow-up probe commands. `problems` lists inconsistencies the probe noticed. Treat both as leads, not verdicts.
- **Secrets.** Redact any value whose key looks like a secret, token, or password.
- **Shared reads.** A check that needs the same fact calls the same read function the probe uses, so a probe can re-check any verdict.

## Actions

An action does something a real user or operator would do, through the same entry point they use.

- **Ask flag.** An action with a real or shared side effect refuses to run without `--i-was-asked`. Pass the flag only when the user asked for that action in this session.
- **Owned resources.** An action refuses to touch a resource this kit did not create, and says how it decided ownership.
- **No stand-ins.** Never forge the event, header, or marker the real system would produce, and never call an internal setter or test-only route instead of the real entry point. If the real path refuses, stop and ask.
- **Output.** One JSON object naming the action, the target, and the IDs it created. Exit 0 on success, 2 on refusal or error.

## Checks

A check proves one or more sub-features by driving the real entry point and reading back the result.

- **Read back every side effect.** A success status code is never proof. Read the stored row, the sent message, the written file, or the rendered screen by its exact ID.
- **Seen versus state.** Say whether the check reads what the user sees or only stored state. A state pass is not a user-visible pass.
- **Print as you go.** Each step prints its pass or fail as it happens, so a later crash cannot hide it.
- **Evidence before cleanup.** Write the evidence file before any cleanup, through a temporary file and a rename. Cleanup removes only what this run created and never deletes evidence.
- **No verdict without a check.** A run that only observed, or stopped early, saves `passed: null`. Null is never reported as a pass.
- **Count only fresh events.** A step that waits for an event counts only events that arrived after the step started.
- **Break-tested.** A check counts as proven only after it failed on a planned break: a scratch copy with the behavior reverted. Record the break in the feature file.
- **Exit codes.** 0 passed. 1 a step failed. 2 stopped or could not run.

## Evidence

Each check run writes one JSON file to `<evidence dir>/<check>-<timestamp>.json`:

```json
{
  "check": "checkout-pay",
  "sub_features": ["checkout.pay"],
  "passed": true,
  "reads": "state",
  "code": {"commit": "a1b2c3d", "branch": "main", "dirty": false, "on_main": true},
  "started_at": "2026-10-03T14:02:11Z",
  "finished_at": "2026-10-03T14:02:40Z",
  "steps": [
    {"name": "order is paid", "passed": true, "detail": "status=paid", "evidence": {"order_id": "o_123"}}
  ],
  "created": {"orders": ["o_123"]},
  "stopped": null
}
```

`passed` is `true`, `false`, or `null`. `stopped` holds the reason when the run stopped early. `created` lists what cleanup may remove.

## Reporting

Report each sub-feature as one of:

- **Verified:** the check, the entry point, the evidence file, and the code line.
- **Failed:** the step that failed and what it read.
- **Not verified:** why. Name the missing check, or the blocker (account, entitlement, OS, external state, human-only start) and the route tried. Never report a skipped entry point as verified through a different one.
