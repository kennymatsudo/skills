# Inventory prompt

Fill in the placeholders and pass the text below as the subagent's prompt.

---

You are listing the identifiers some files define, so another agent can judge their names. Return evidence, not new names.

Read only. Never edit files, and never run the code, its tests, or a build.

## Repo

{REPO_ROOT}

## Files

{FILES}: one per line. In diff mode, also the changed line ranges; list only identifiers those lines add or rename.

## For each identifier

Cover variables, parameters, functions, methods, classes, types, constants, enum members, fixtures, test names, and file names.

- **Where:** kind and `path:line` of the definition.
- **What it is:** one sentence on what it does or holds, read from the code. Ignore what the name suggests. Note any side effect, such as a write, network call, or mutation of an argument.
- **Outside dependents:** whether anything outside this repo depends on the name: a public export, serialized or API field, database column, env var, CLI flag, config key, or metric or event name. Give the evidence line, or "none found".
- **Concept:** the domain concept it names, such as "customer", "fetch from remote", or "retry delay", so the caller can compare vocabulary across groups.

Mark anything you could not confirm as unconfirmed. Return one row per identifier.
