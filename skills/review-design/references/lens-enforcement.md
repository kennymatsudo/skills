# Lens: enforced rules

Is each rule the code depends on enforced by the code, or only by a reader remembering it?

## Look for

- **Rules kept in prose.** A comment, docstring, README, or agent instruction file states a rule that a type, lint, assertion, test, or generated file could enforce: "call `init()` before `send()`", "update the enum in `types.ts` too", "never import from `internal/`".
- **Required call order with no guard.** An object that must be built, then configured, then used in that order, where calling out of order fails quietly or later.
- **Hand-kept copies.** A type, list, or schema copied by hand from one that another file owns (an API spec, a migration, a proto), instead of derived from it.
- **Conventions enforced by review.** History shows the same correction repeated in commits ("forgot to register", "add to the list too").

Prefer the strongest enforcement that fits: a type that can't be built wrong, then a lint or banned import that fails CI, then one shared helper, then a runtime check.

## A finding needs

The rule's text, quoted, and the code it governs. Name the mechanism that would enforce it.

## Don't flag

- A comment that explains why, when no mechanism could check it.
- A rule already enforced elsewhere. Search for the lint, test, or check before reporting.

## Usual verdicts

move, delete
