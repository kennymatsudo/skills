# Code

The standard is what a careful engineer on this codebase would have written. Before editing a file, read the rest of it, one or two neighbors, and the repo's agent instruction files for local conventions: error handling, naming, imports, test style, and existing helpers.

Agent code tends to grow rather than look wrong, so most fixes are deletions.

## Checklist

List each instance on the branch's changed lines, then fix or keep it:

- **Hollow tests.** Tests that assert on a mock they set up, assert nothing, check that the language works, or duplicate another test. Rewrite the assertion to check what a caller observes, or delete the test and say so in the reply.
- **Speculative abstraction.** An interface, base class, factory, registry, or config option with one implementation or one caller. Inline it.
- **Compat shims in new code.** Aliases, re-exports, feature flags, fallback paths, or "kept for backwards compatibility" wrappers for code this branch introduced or fully migrated. Change the callers and delete the shim.
- **Defensive code on trusted paths.** Null checks on values the type or caller guarantees, try/catch that swallows, re-logs, or rethrows unchanged, fallback values (`?? 0`, `.get(key, {})`, `or []`) that turn a broken caller into quietly wrong output, and validation repeated at every layer. Delete a guard only after confirming the guarantee in the type or every caller. Keep guards at system boundaries: user input, network, files, external APIs.
- **Type escapes.** Casts to `any`, `type: ignore`, non-null assertions, and similar escapes that only silence an error. Fix the type, or keep the escape with its reason when the fix is out of scope.
- **Dead code.** Unused parameters, imports, variables, and helpers, unreachable branches, and commented-out code.
- **Reinvented helpers.** Search the repo for an existing function that does the same job; call it and delete the copy. When the branch writes the same logic twice, keep one and call it from both places.
- **Noise.** Logs and prints that narrate progress, and debug output left behind.
- **Deep nesting.** Flatten with early returns when it shortens the code.
- **Drift.** Naming, error handling, or structure that differs from the surrounding file without a reason.
- **Comments.** Load the clean-up-comments skill if it is installed. Otherwise delete comments that narrate the next line, the edit history, or the conversation, and keep the ones that explain why.

## Guardrails

- Make the smallest edit that removes the slop. No broad rewrites or renames the diff didn't need.
- Leave public APIs, schemas, and migrations as they are; report slop there instead.
