# Verification rules

Copy this file into the kit as `rules.md`. Replace each `<...>` with what the repo uses, and delete any section for a kind of piece the kit does not have yet. Every piece in the kit follows these rules. A piece that cannot follow one names the exception in its own help text and in the feature file that uses it.

## Project workflow

Requirements source: `<source or none>`. Coverage map: `<existing location, features/requirements.md, or none>`. Current results: `<existing location or status.md>`. Evidence: `<location>`. Use the user's declared workflow and existing project conventions before these defaults; keep these pointers current so every skill uses the same homes.

## Code under test

Every result records which version produced it. For Git code, record the commit, branch, dirty state, and whether the commit is on the relevant default branch. An unreadable version is unknown. A pass on one version is evidence only for that version.

## Lanes

Each lane proves more than the one before and costs more. Climb only as far as the claim needs, and name the lane in every result.

| Lane | Who may run it | What it can prove |
| -- | -- | -- |
| 1. Unit | Agent, always | `<the code's own logic, with external systems mocked>` |
| 2. Local read | Agent, once the doctor passes | `<state that already exists, read through probes>` |
| 3. Real system | Agent, only with the ask flag | `<behavior that crosses a real external or shared system>` |
| 4. Human action | `<the user, or an action through the real operator API>` | `<what only a person or operator can trigger>` |

A lane cannot prove a claim about a system it mocks. Report such a claim as not verified and name the lane that would settle it.
Before a live run, check that the running processes use the checkout under test. A stale process makes the verdict invalid even if the check passes.

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
- **Hints.** `next` lists follow-up probe commands. `problems` lists each invariant the current state breaks, with its name and kind. Confirm every entry with the read it names before reporting it.
- **Secrets.** Redact any value whose key looks like a secret, token, or password.
- **Shared reads.** A check that needs the same fact calls the same read function the probe uses, so a probe can re-check any verdict.

## Invariants

An invariant is a rule that holds whatever happened, written as code in `<invariants module>`. It judges any state, including one no check anticipated, so probes, checks, and exploration ask the same question the same way.

- **One function per state it judges,** taking state the caller already read and returning violations, each with the invariant's name, its kind, and a detail. It reads nothing itself.
- **Kinds.** `safety` must hold at every moment: a violation is a break. `eventual` holds once the app settles (`<settle signal>`): a violation right after an action may be lag, so recheck after it settles. `lead` is worth a look and wrong only if it repeats or breaks another rule.
- **Missing versus empty.** A value that could not be read is not judged. A value read and found absent is.
- **Break-tested.** Each invariant reports a violation on a planned break, like a check.

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
- **Wait for the state.** A step that judges what a page or a polled service shows waits up to one refresh cycle for the expected state, rather than sampling once.
- **Wanted but not built.** A check for behavior the team wants and has not shipped stays in the kit and fails. Report it as Failed with its tracking issue. When it starts passing, the run says so, so the tracking note gets removed. A failing step never stops independent steps after it.
- **Break-tested.** A check counts as proven only after it failed on a planned break: a scratch copy with the behavior reverted. Record the break in the feature file.
- **Exit codes.** 0 passed. 1 a step failed. 2 stopped or could not run.

## Exploration

`exploration.json` in the kit holds the settings the explore-bugs skill reads:

```json
{
  "ledger": "<evidence dir>/exploration-ledger.jsonl",
  "kinds": ["timing", "order", "identity", "input-shape", "lifecycle", "external-side", "code-reading"]
}
```

The ledger lives beside the evidence it points at.

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

Read the current results home named under Project workflow before a run. Afterward, update it with the exact version tested, outcome, evidence, and any new limit on what a pass means. Feature files describe intended behavior; the results home records what happened.

Report each sub-feature as one of:

- **Verified:** the check, its lane, the entry point, the evidence file, and the code line.
- **Failed:** the step that failed and what it read.
- **Not verified:** why. Name the missing check, or the blocker (account, entitlement, OS, external state, human-only start) and the route tried. Never report a skipped entry point as verified through a different one.
