---
name: refactor-agent-instructions
description: >-
  Refactor a repo's AGENTS.md or CLAUDE.md to follow the current best practices
  for writing them, looked up on the web at run time for today's date and the
  newest models, keeping every project fact that still holds. Proposes the
  rewrite and edits only after approval. Use for "refactor our AGENTS.md",
  "update CLAUDE.md to current best practices". Use update-agent-instructions
  to add lessons from a session, and trim to only cut redundancy.
disable-model-invocation: true
---

# Refactor agent instructions

You own a rewrite of the instruction file that follows today's published guidance and loses no project fact that still holds.

Guidance for these files changes with each model release, and what worked for older models (emphatic wording, stacked cautions, standing reminders) can make newer ones over-apply rules. So the guidance comes from a fresh search every run. Knowing a model's name or a best practice from memory is no reason to skip the search, because releases outpace training data.

## 1. Scope the files

Take the file the user names. With none named, take the repo root's `AGENTS.md` and `CLAUDE.md`, whichever exist. Add every file they import, and run `python3 <this skill's directory>/scripts/check_refs.py <file>...` on the set to list imports and stale paths. Save its output as the baseline. Mention nested instruction files under subfolders, and leave them out unless the user asks. For a file in a subfolder, read the parent folders' instruction files too, since they load alongside it, and plan to cut rules the parent already states.

Note which harnesses load each file, since that sets whose guidance applies: `CLAUDE.md` is read by Claude Code, and `AGENTS.md` by Codex, Cursor, and most others. When `CLAUDE.md` is a symlink to `AGENTS.md` or only imports it, refactor `AGENTS.md` and keep the link or import as it is.

If a file in scope has uncommitted changes, ask before going further, because git can't restore an overwritten edit that was never committed.

Done when you have the file list, which harnesses load each, and the baseline check output.

## 2. Get today's guidance

Read `references/research.md` and spawn the subagent it describes, filled in with today's date and the files and harnesses from step 1. While it runs, read the files in scope in full.

When the report comes back, check each UNVERIFIED point before relying on it, or keep the label. Fetch pages yourself only for those points, since the subagent already read the rest. If the session has no web search or fetch tool, stop and tell the user. A rewrite against remembered guidance is the thing this skill exists to replace.

Done when you have the newest model per vendor, ranked rules with URLs and dates, the scaffolding to remove, and the loading mechanics.

## 3. Inventory and decide

List every item in the files: each command, convention, pointer, rule, warning, and overview paragraph. For each, record one decision with its reason:

- **Keep** as written.
- **Reword** to match a guidance rule, such as softening emphasis, giving a bare absolute its scope and reason, or adding the why. Cite the rule. Also reword volatile detail into its durable form, because agents trust a wrong pointer more than a missing one. File lists, directory trees, line numbers, counts, and version numbers become the command, naming convention, entry point, or search that finds the thing ("grep for the route string").
- **Move** detail that only some tasks need out of the always-loaded file, so every session doesn't pay for it. Candidates are a nested file for one folder, a separate doc the root file points to with when to read it ("before changing the schema, read `docs/schema.md`"), a skill for a workflow, or a hook or lint rule for something with no exceptions. A move to a check counts only if the check already exists. Otherwise keep the line and propose the check.
- **Drop**, with evidence. Something the agent can read from the code: name the file that shows it. Stale: show the failed path or command. Scaffolding for older models: cite the guidance rule. Already stated by a parent folder's file: quote the parent's line.

Check each fact against what owns it before deciding. Confirm a command exists in the build files, a path exists, and a convention matches the code. Before dropping an item because another file already covers it, or moving it into an existing file, search that file for each literal value in the item (ports, flags, env vars, names). Any value missing there moves with the item rather than being dropped. A line that names a person, ticket, or incident is project history only the user can judge, so mark it for them instead of dropping it.

Where sources disagree, such as on a length target, follow the docs of the harness that loads the file. For a file several harnesses load, follow the strictest limit.

Done when every item has a decision and a reason, and every drop has its evidence.

## 4. Propose

Show the user, before editing anything:

1. **Guidance used:** the newest models found, and the sources with their dates.
2. **New outline:** the sections of the rewritten file, with the line count before and after.
3. **Changes:** a table with one row per reworded, moved, or dropped item: the item, the decision, the reason or evidence, and its new home. The table is what lets the user catch a fact lost in a drop, so give each fact its own row, splitting any row that covers several commands or values.
4. **Kept facts:** a one-line list of kept items that carry a command, flag, env var, port, or ID. The rest of the kept items as a count.
5. **Parent overlap:** each rule a parent folder's file already states, or "none found" with the parent files read.
6. **Decisions for the user:** marked items and any contested point, numbered, each with a recommendation.

Wait for approval. Apply the user's edits to the plan.

Done when the user approves a plan.

## 5. Write and check

Write the approved files, matching the repo's existing tone and Markdown style. Put each import on its own line, outside code spans and fences, since harnesses skip imports inside code.

Then check the result:

- Rerun `check_refs.py` on the new files. Imports must match the baseline, and no new warning may appear.
- Walk the step 3 list and confirm every kept, reworded, or moved item is present in its new home.
- Reread the new files against the guidance rules from step 2, and fix any line that breaks one or carries volatile detail.

Done when the checker matches the baseline, every kept item is found, and no line breaks a rule.

**Reply:** the files changed with line counts before and after, the newest models and sources the rewrite followed, each item dropped or moved, and any check proposed but not built.
