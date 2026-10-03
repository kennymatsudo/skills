# Lens: testability

Can a test reach each behavior through the module's real interface, without mocking its insides?

## Look for

- **Logic tangled with I/O.** Business rules sit between database calls, HTTP calls, clock reads, or random numbers, so testing a rule needs mocks. A pure function the shell calls would be testable with plain inputs.
- **Tests that mock internals.** Existing tests patch private functions or fake another module's lifecycle to reach a branch. That branch likely lives in the wrong module or behind the wrong interface.
- **Extracted for testing, not for sense.** Small pure helpers pulled out so they could be unit-tested, while the bugs live in how they're wired together and nothing tests that.
- **Hidden inputs.** A function reads globals, environment variables, or singletons, so a test must set up the world to call it.

## A finding needs

The tangled code or the mocking test, quoted, and the interface a test would call after the change.

## Don't flag

- Mocks at a true outside boundary: a paid API, an email provider, the network.
- Missing tests on their own. This lens is about whether the design can be tested, not test coverage.
- Thin glue code whose only job is I/O.

## Usual verdicts

split, move
