# Lens: domain model and types

Does the data structure encode the domain, or do conditionals and runtime checks hold it together?

## Look for

- **Scattered conditionals.** The same branching on a kind, status, or flag repeats across files. A new variant would add one more branch in each. A state machine, lookup table, or tagged union would hold it once.
- **Booleans that must stay in sync.** Two flags, or a flag and an optional field, where some combinations are meaningless: `completed: true` with no `completed_at`.
- **Illegal states the types allow.** Optional fields whose valid combinations live in a comment or a runtime check. The test: if you can write a comment explaining when the combination is valid, the type is too loose.
- **Primitive obsession and data clumps.** Raw strings or ints carrying meaning (`user_id` and `order_id` both `str`), or the same three parameters passed together through many functions.
- **Lies to the type checker.** Casts, `any`, non-null assertions, or ignore pragmas that cover a fact nobody proved.
- **Non-exhaustive matching.** A match or switch on a variant that would compile silently if a new variant were added.
- **Temporal decomposition.** Modules named for steps (load, validate, transform, save) that each repeat the same domain rules.

## A finding needs

Each repeated branch or each runtime check that a better type would remove, quoted, and the structure that replaces them.

## Don't flag

- Branching that appears once and is clear where it is.
- A dynamic language or a codebase with no type checker, for type-only findings. The structural findings still apply.
- A precise type that would make nothing safer. Strengthen a type only where a runtime check, null check, or "can't happen" throw shows it is too weak.

## Usual verdicts

merge, move
