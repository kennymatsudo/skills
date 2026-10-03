# Building each piece

Write tools in the repo's own language and expose them the way the repo already exposes developer commands. Put new tools in new files; wiring them into an existing Makefile or package manifest needs the user's OK for that edit. Reuse the repo's existing database and API clients. If the kit has a shared reads module, add new reads there.

## Doctor

Build from the start command and ready signal found in discovery. Report each process, its code (commit and dirty state of the checkout it runs from), its ports, and auth. When the app runs from a different checkout than the current one, report that checkout's commit, not the current one's.

**Proof:** run it against the app started the real way (exit 0) and with the app stopped or on a wrong port (exit 1 with a reason). Show both outputs. If the real start needs a human, prove it against the instance the user started, and if stopping it would disturb them, show only the first output and say the second was not run.

## Feature file

Draft it from the code. For a feature you have not traced, follow the how skill if installed, at the component level, for the feature's entry point. Write sub-features as user-visible behaviors, one per line. Mark every new ID "No check yet." unless this request also adds its check.

**Proof:** `<check command>` passes.

## Probe

Pick the question an agent would otherwise answer with raw SQL or curl. Name the command after the thing it reads (`probe order <id>`), not the table or route.

**Proof:** run it on a real ID (exit 0, show the JSON) and on a made-up ID (exit 1, show the hint). Confirm it only reads: for a database, the transaction is read-only; for HTTP, the method is GET.

## Action

Use the same entry point a real user or operator uses. Decide with the user whether it needs the ask flag: anything outside this machine, shared, paid, or rate-limited does. Record how it decides ownership.

**Proof:** with the user's OK for this run, run it once and read the result back with a probe. Run it without the ask flag and show the refusal.

## Check

Map it to the sub-feature IDs it proves. Drive the real entry point, wait on a ready signal or a probe rather than a fixed sleep, and read back every side effect.

**Proof, in order:**

1. Run it on the current code. It passes, and its evidence file matches the format in `rules.md`. If it fails, confirm from the code that the behavior is really broken, report that as a product bug, and invert the next steps: plan the smallest fix instead of a break, and the check must pass on it.
2. Plan one break: the smallest edit that makes the behavior wrong while the code still builds, such as skipping the write or returning the old value. Before running `git worktree add`, tell the user `Planned break: <the edit>`, or `Planned fix: <the edit>` for an inverted proof.
3. Add a scratch git worktree, make the break there, and run the check against that worktree. It must fail on the step that covers the broken behavior.
4. Remove the worktree. Never make the break in the user's checkout.
5. Write `Break-tested <date>: <what was broken>.` on the proof line, or for an inverted proof, `Not break-tested: broken on current code; passes on a planned fix (<the fix>).`

If the running app cannot be pointed at a scratch worktree (one instance per machine, human-only start), ask the user whether to run the break against their instance, and restore it right after. If they decline, write `Not break-tested: <reason>.` and report the check as unproven.

## Scenario

A scenario is a check that walks several sub-features in one user journey. Build it only when the user asks or when the steps cannot run apart (each depends on state from the last). Give it its own feature file that links to the per-feature files, and prove it like a check, with one planned break per sub-feature it claims.
