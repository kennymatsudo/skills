---
name: rename-variables
description: >-
  Rename the identifiers your branch adds, or everything defined
  under a given path, so each name is honest, specific, and in the repo's
  vocabulary, then update every reference. Use unslop for other code slop and
  clean-up-comments for comments.
disable-model-invocation: true
---

# Rename variables

You own the names in scope: each one tells the truth about what it does or holds, in the words this codebase already uses.

Change names only. Never change behavior, formatting, or comments, except to update a comment's mention of a name you renamed.

## 1. Scope

By default, cover the branch: everything that differs from its merge base with the default branch, whether committed, staged, unstaged, or untracked. Find the default branch with `git symbolic-ref --short refs/remotes/origin/HEAD`, else `origin/main`, else `origin/master`. Take `git diff $(git merge-base HEAD <default>)` plus untracked files from `git status --porcelain`.

Narrow it when the user asks:

- **Uncommitted:** `git diff HEAD` plus untracked files.
- **Staged:** `git diff --staged` only.
- **A path:** every identifier defined under that path.

Tell the user the scope in one line before going further, such as "Scope: branch `foo` vs `origin/main`, 12 files".

Done when you can say which mode you are in and list the files in scope.

## 2. Inventory

List every identifier the scope defines: variables, parameters, functions, methods, classes, types, constants, enum members, fixtures, test names, and file names. In diff mode, skip names the change only uses, and note the misleading ones as pre-existing.

For each, record its kind, `path:line`, one sentence on what it does or holds, read from the code rather than the name, and whether anything outside this repo depends on it: a public export, serialized or API field, database column, env var, CLI flag, config key, or metric or event name.

When the scope spans more than about ten files, split them into groups by directory and spawn one read-only subagent per group on a mid-tier model, in parallel, with the prompt in `references/inventory-prompt.md`.

Done when every identifier has a row with all four fields.

## 3. Learn the repo's vocabulary

For each concept the inventory names, find how sibling code outside the scope names it, such as the same entity, act, or unit. Read the repo's naming lint rules too.

When the repo uses several words for one concept (`fetch`, `get`, `load`), count each and pick the most-used one that is honest and specific. A generic or misleading term sets no standard, however common it is; repos written quickly by agents are full of them. Record the drift for the report.

Done when each concept has a chosen term, or a note that the repo has none worth matching.

## 4. Judge

Two careful engineers rarely pick the same name. Rename only when the current name fails a test below, never because you would have chosen differently. Name from the step 2 sentence, not from the old name.

Tests, in order. An earlier failure outranks everything after it:

1. **Honest.** The name matches behavior and shape: a `get` or `is` that writes, an `isX` that isn't a boolean, a singular name holding a collection, a `userList` holding a map, a name for what the code used to do.
2. **In the repo's vocabulary.** Uses the step 3 term for its concept, and one name means one thing.
3. **Specific.** It excludes wrong readings. `data`, `info`, `result`, `item`, `temp`, `manager`, `helper`, `handle`, and `process` fit anything, and so does a pipeline-step name that says where a value came from rather than what it is (`parsedResponse`, `filteredResults`).
4. **Proportionate.** Length matches scope: `i` in a short loop, a full phrase at module level. Cut words the type or the surrounding name already carries (`userDataObject`, `UserServiceManagerImpl`). Expand opaque abbreviations and codenames.

Give each name one verdict:

- **Keep.**
- **Rename to X,** citing the failed test.
- **Flag,** when something outside the repo depends on it. Propose the name and leave the code alone.
- **Design finding,** when no honest, specific name fits. The thing likely does two jobs; say which, and rename it to a name that states both (`export_and_cache_tickets`), never to one that hides either.

Done when every inventory row has a verdict.

## 5. Apply

Before the first rename, run the repo's typecheck, lint in check-only mode, and the tests covering the code in scope, and record what fails. That is the baseline; never stash, reset, or check out files to get one, because the scope is often uncommitted work.

For each rename, use the harness's language-server rename when one is available, since it follows imports and scoping. Otherwise edit the definition and every reference by hand.

Then sweep the whole repo for each old name, whole-word and in its other casings (`userData`, `user_data`, `USER_DATA`, `UserData`): string keys, reflection and dynamic lookups, templates, config, fixtures, mocks, test names, migrations, and docs. Language-server renames skip these by design. Update each hit that refers to the renamed thing. A hit that crosses a persistence or wire boundary means the name was shipped after all: revert that rename and flag it.

Rerun the same checks. Revert any rename that breaks a check you can't fix by updating a missed reference.

Done when each old name's sweep returns only hits you decided to leave, and every check passes or fails only where the baseline failed.

Reply: a table of old name, new name, and failed test; then flags with proposed names; design findings; vocabulary drift found in step 3; pre-existing offenders in diff mode, each with `path:line`; and the check results.
