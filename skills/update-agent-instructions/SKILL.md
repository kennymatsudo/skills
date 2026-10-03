---
name: update-agent-instructions
description: >-
  Update the agent's instructions (AGENTS.md, CLAUDE.md, global guides,
  skills) with lessons and search shortcuts from this session, routing each to
  the narrowest file that should hold it and proposing deletions of lines the
  session proved wrong. Edits nothing until the user approves. Use for "update
  agent instructions", "anything to add to AGENTS.md", "update AGENTS.md from
  this session", "what should we add to our instructions".
disable-model-invocation: true
---

# Update agent instructions

You own a short list of instruction edits, each backed by something that happened in this session, and the restraint to propose none when nothing qualifies.

Instruction files are loaded on every turn and only grow. A line that doesn't change what an agent does costs every future session and dilutes the lines that do. Proposing nothing is a good outcome.

## 1. Collect evidence

Work from the session itself. If earlier turns were summarized and the harness keeps a transcript file, spawn one mid-tier subagent to read it and list the moments below, quoting each.

List every moment of these kinds:

- **Correction.** The user corrected the agent, or rejected its output.
- **Failed attempt.** A command, approach, or assumption that failed before one worked.
- **Wasted search.** Several searches or file reads to find something one well-aimed search would have found.
- **Wrong instruction.** A line in an instruction file or skill that pointed wrong, was out of date, or conflicted with another.
- **Standing rule.** The user said how things should always be done.

Done when each moment is listed with a one-line quote or summary. If the list is empty, stop and say so.

## 2. Turn each moment into a candidate

Write each as the rule a future agent should follow, with its reason in one clause. Then test it. It survives only if all four hold:

- **Not inferable.** An agent would not do this unprompted, and it isn't already stated by the code, config, types, `--help`, or an existing instruction. A rule the user states still fails when any capable agent follows it anyway ("use clear names"). To check, read the target file in step 3 before deciding.
- **Durable.** Still true after files move, names change, and versions bump. Rewrite volatile detail into its stable form, or drop it.
- **Changes a decision.** A future agent would act differently, not just know more.
- **Safe to share.** No secrets, personal data, or machine-specific paths in a shared file.

For a wasted search, keep how to find the thing, not where it is today:

- **Keep:** commands, naming conventions, entry points, stable boundaries ("handlers live under `api/`"), and the search that finds it ("grep for the route string, not the handler name").
- **Drop:** file lists, directory trees, line numbers, counts, and "X is in file Y" when Y is likely to move. A wrong pointer costs more than none, because agents trust it.

Run each surviving search or command now and confirm it finds what the rule claims.

Done when every moment is marked kept (with its rule) or dropped (with the failed test).

## 3. Pick the home

For each kept rule, take the first home that works:

1. **A check.** A lint rule, test, hook, type, or script can enforce it. Propose the check instead of prose.
2. **An existing skill.** The rule belongs to a workflow a skill owns, and that skill was loaded this session.
3. **A folder's instruction file.** It applies only under one directory. Never put a navigation rule here: an agent reads that file only after it already found the folder.
4. **The repo's instruction file.** It applies across this repo. When the harness file only imports another (a `CLAUDE.md` that imports `AGENTS.md`), edit the imported file.
5. **The user's global instructions.** It applies across all the user's repos. If the global file points to topic guides, use the matching guide.

Read the target before proposing. If you can't read it and it isn't already loaded in the session, name it as the home and say it is unread instead of proposing text. If it already says this clearly, drop the candidate. If it says this but the agent missed it, propose a rewording or move, not a second copy. If the new rule supersedes or contradicts a line there, propose deleting or replacing that line.

Deletions come only from evidence in this session. A full pass over a file belongs to a trim skill.

Done when every kept rule has a target path and section, and every target was read or marked unread.

## 4. Propose and apply

Show every proposal and wait for the user to pick. For each:

- **Lesson:** the rule, one line.
- **Evidence:** the session moment.
- **Edit:** the target path and the exact text to add, replace, or delete.

Then list dropped moments, one line each with the reason.

Apply only what the user approves, matching each target file's style. For a skill change larger than a few lines, or a new check, follow the create-skill skill if it is installed.

Done when every approved edit is applied.

**Reply:** the edits applied with their paths, then any checks or skill changes handed off.
