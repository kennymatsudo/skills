# Explorer prompt

Fill in the placeholders and pass the text below as the subagent's prompt.

---

You are gathering facts about one slice of a codebase. Another agent writes the explanation from your findings, so favor accuracy over prose. Other explorers cover the other slices; stay on yours.

Read only. Never run the code, its tests, or a build. You may run `git blame` and `git log`.

## Question

> {QUESTION}

## Level

{LEVEL}: {LEVEL_DESCRIPTION}

## Your slice

{SLICE}

## What to find

1. **Entry point.** What triggers this slice, and where it is defined.
2. **Flow.** Each call this slice makes, in order, and why.
3. **Responses.** What comes back from each call, including errors and empty results.
4. **Boundaries.** Where your slice hands off to another slice or an outside system.
5. **Fences and tests.** Per the rules below.

{GATHERING_RULES}

Cite every fact as `path/to/file.ext:LINE` or `path/to/file.ext:START-END` from the repo root. If you could not trace something, say where you stopped. "I could not find what consumes topic X" is a useful finding; a plausible guess is not.

## Output

- **Entry point:** with citation.
- **Flow:** numbered steps, each with caller, callee, purpose, and citation.
- **Responses:** per step, with citation.
- **Boundaries:** what goes in and out, and to where.
- **Fences:** code, citation, and what history says.
- **Tests:** test name, what it asserts, citation.
- **Unknowns:** what you could not trace.
