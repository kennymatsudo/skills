# Caller search prompt

Fill in the placeholders and pass the text below as the subagent's prompt.

---

You are finding how some methods fit into the codebase, so another agent can write a short docstring about each method's role. Return evidence, not docstrings.

Read only. Never edit files, and never run the code, its tests, or a build.

## Repo

{REPO_ROOT}

## Methods

{METHODS}: one per line, as `path:line symbol`.

## For each method

- **Callers:** every place that calls it, with `path:line`. Follow imports, re-exports, route and job registrations, and config, not just the name. A matching name in another module is a guess until you find the import or registration.
- **What callers use it for:** one line per distinct use.
- **Handoffs:** what it returns or passes on, and what consumes that, with `path:line`.
- **Timing:** any ordering or repeat-call rule the code enforces, such as "must run after X" or "safe to call twice", with the line that enforces it. Skip this when there is none.

Mark anything you could not confirm as unconfirmed. Return a short block per method in that order.
