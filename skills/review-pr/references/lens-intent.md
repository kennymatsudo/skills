# Lens: gaps against the requirements

Does the change do what it was asked to do? A PR can be bug-free and still not solve the problem it was opened for.

Go through `intent.md` item by item:

- **Each requirement:** find the code that meets it, and trace one realistic input through it. Flag a requirement that is missing, met only for some inputs (only the happy path, only one of the user types, only new records and not existing ones), or met somewhere no caller reaches.
- **Each author's claim:** check it against the code. "No behavior change", "backwards compatible", "behind a flag", and "covered by tests" are the claims most often wrong; confirm the flag gates every new path and the tests exercise the claimed case.
- **Changes nobody asked for:** a behavior a user or caller would notice that no requirement or claim mentions. Flag it only when it makes something worse for someone.

If `intent.md` has no requirements source, check only the author's claims.

## Don't flag

- Requirements the description says are deferred to a later PR.
- Disagreement with the requirement itself. That's a question for the ticket, not a defect in the code.
