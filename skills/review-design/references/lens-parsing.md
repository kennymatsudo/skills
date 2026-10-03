# Lens: input parsing

Is outside data parsed once where it enters, and trusted after that?

An entry point is where data enters the system: request handlers, CLI arguments, config and environment, queue consumers, external API responses, database rows, files.

## Look for

- **Validation spread through business logic.** Null checks, type checks, and `try`/`except` deep in call chains, guarding data an entry point already handled or should have.
- **Validate without parse.** An entry point checks the data and passes the raw shape on, so every consumer re-checks or assumes. It should return a typed value that can't be invalid.
- **Missing entry check.** Raw external data (a dict from JSON, an env string) travels several calls in before anything checks it.
- **Leaked representations.** Wire, storage, ORM, or framework types exposed through a module's public surface, so callers depend on the transport.
- **Swallowed errors.** An entry point catches and drops an error, or logs and continues, so the caller can't tell failure from success.

## A finding needs

The entry point's lines, and each interior check that duplicates or substitutes for it, quoted. For a missing entry check, the path the raw data travels.

## Don't flag

- Checks at a real entry point, however defensive.
- An internal check that guards an invariant the types can't express, when it fails loudly.
- A library's public functions validating their own arguments.

## Usual verdicts

move, delete
