# Lens: ownership of decisions

Does each decision live in the module that owns the facts it decides on?

A decision is a branch whose outcome depends on state: is this a duplicate, is this stale, may this transition happen. The owner of a fact is the module whose storage and transitions define it. Storing a copy is not owning it.

In branch scope, first list every new or changed decision in the diff (conditionals, dedupe checks, guards, rejections, filters, fallbacks) with the question each answers. Then, for each one, name the facts it needs, each fact's owner, and whether this module owns the fact, is told it, or reconstructs it.

## Look for, strongest first

- **Reconstruction.** The code works out another module's state from clues (timestamps, ordering, metadata keys, a missing row) instead of being told.
- **Downstream compensation.** It filters, dedupes, reorders, or rejects to undo something a sender produces, when the sender could stop producing it.
- It queries its own storage to answer a question about another module's lifecycle.
- It exists for one caller's quirks (duplicates, bursts, retries, clock skew) that a second caller wouldn't have.
- A field name describes the sender's internals ("upstream event ID") while the receiver treats it as a generic key.

## Relocation test

Imagine moving the logic into the owner. It belongs there if it gets simpler: an inference becomes one lookup, or several rules collapse into one state check, or the receiver shrinks to a generic invariant like "a repeated key writes nothing". It stays if moving it forces the owner to learn the receiver's internals.

## A finding needs

The decision's lines, the lines in the owner that define the fact, and what the owner would send or decide instead. A claim that a guarded state can't happen needs `path:line` evidence from the module that controls that state, with retries, races, fallback paths, and repeated events checked separately.

## Don't flag

- A receiver surviving replays or malformed input. That is its own job, not the sender's state model.
- A backstop with a named reason: a second caller, an owner held by another team with weaker guarantees, or a failure that is expensive and hard to notice.
- Logic placed with the data it's stored next to, when that module also owns the transitions.

## Usual verdicts

move, split, backstop, delete
