# Lens: correctness inside the diff

Does each changed line do what the code around it needs? This lens stays close to the diff on purpose: reviewers who roam the repo miss plain local bugs.

For each changed function, read the whole function at head, then check the changed lines against it.

## Look for

- Conditions that are inverted, off by one, or miss a case: empty, none or null, zero, negative, one item, the boundary value, duplicates.
- A value used before it's set, after it's freed or closed, or after it changed meaning in this diff.
- Errors caught and dropped, caught too broadly, or raised where the caller expects a return value. A new failure path that leaves state half-written.
- Early returns and `continue`s that skip cleanup, a counter, or a write the old code always did.
- Resources opened and not closed on every path: files, connections, locks, transactions.
- Concurrency: shared state changed without the lock the rest of the code uses, check-then-act races, async calls not awaited.
- Time, money, and units: time zones, float math on money, mixed units, integer division.
- A refactor that changed behavior: compare each moved or rewritten block with its base version (`git show <base>:<path>`) and name every input whose result differs.

## Don't flag

- Defensive checks for states the code shows are unreachable.
- Anything a type checker or linter in the repo already reports.
