# Lens: reruns and shared writes

Does each operation converge to the right state when it runs twice, resumes after a crash, or runs alongside another?

## Look for

- **Breaks on rerun.** A job, handler, migration, or command that inserts without checking what exists, assumes a clean start, appends where it should upsert, or sends a side effect (email, charge, webhook) with no idempotency key. Ask of each: what if this runs twice in a row? What if the last run crashed at each step?
- **Stale leftovers.** Locks, temp files, or "in progress" rows that nothing cleans up after a crash.
- **Shared write targets.** Two workers, processes, or services writing the same file, row, key, or branch, often behind a lock or retry loop that hides the collision. Ask whether they need one shared object or are publishing independent facts that could each have their own target, merged where they're read.
- **Read-modify-write races.** Code reads a value, decides, and writes back without a transaction, compare-and-swap, or single writer.

## A finding needs

The write or side effect, quoted, and the concrete sequence that breaks it: "a retry after line 52 succeeds sends a second charge". For shared writes, both writers' lines.

## Don't flag

- Code that provably runs once: a one-off script, or a migration the framework records and won't rerun.
- A shared target that is a real invariant (one ledger, one sequence), already serialized structurally.
- An insert protected by a unique constraint whose violation is handled.

## Usual verdicts

split, move
