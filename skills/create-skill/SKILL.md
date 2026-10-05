---
name: create-skill
description: >-
  Create, edit, adapt, merge, or retune an agent skill (a SKILL.md and its
  files): decide whether it should exist, research and draft it, validate it,
  and prove it beats a baseline in headless test runs, with cost measured. Use
  for "create a skill", "write a skill for X", "turn this into a skill",
  "adapt this skill", "update this skill", "this skill didn't trigger", "tune
  the description", or when another skill hands off skill authoring. Use trim
  to only cut redundancy from a skill, and update-agent-instructions to route
  session lessons across instruction files.
---

# Create skill

**You own the skill's correctness and its cost to every future session.**

## 1. Classify the job

Name one: **new skill**, **adapt** an existing one from elsewhere, **edit**, **tune description**, or **merge or delete**. A handoff from another skill usually names it. Unless the job is already a named edit, read `references/deciding.md` and apply it against the installed skills' names and descriptions.

Done when you have named the target skill, or you have a reason no skill is needed. If none is needed, stop and report that reason with the better home (a check, an instruction file, nothing).

## 2. Find the source

Installed skills are often symlinks. Resolve the real path (`readlink -f` on the skill directory) and work on the source there.

- **A new skill** goes in the repo or skills directory the user's other skills come from. Follow that repo's agent instructions for adding one. If there is no clear home, ask.
- **Never write into harness-managed directories**, like built-in skills or plugin caches. Updates overwrite them.
- **A skill copied from upstream** records its source and fork point. Read that record before changing it, and port upstream changes by diffing against the fork point.
- **A name collision** with an installed skill from another collection gets flagged to the user before anything is drafted.

For an edit, snapshot the current version to a scratch directory. It is the test baseline.

Done when you have an absolute source path and, for a new skill, the repo's steps for adding one.

## 3. Gather and settle

Take what you can from the conversation first: the steps that worked, the corrections the user made, the output they accepted. Keep any wording the user supplied verbatim.

- **Adapting a skill:** read its `SKILL.md` and every file it references. Summarize its intent for the user and flag mismatches: a description that promises what the body never does, dependencies on files the new home won't have, steps that don't earn their place. Don't copy it word for word.
- **New or adapted skill:** spawn the research subagent in `references/research.md`. While it runs, read the scripts and siblings you'll need. Relay its findings briefly.
- **Edit:** read the evidence of the failure (the transcript, the bad output) and state it in one sentence.

Then settle, one question at a time with a recommendation, whatever the conversation hasn't: the phrasings the user types, the deliverable, the invocation, the default behavior, what the skill must never do, where it ends and its nearest sibling begins, and which subagents run on which model tier. The user's stated workflow beats anything the research says.

Done when each of those is settled, and you have stated the problem and the finish condition in a sentence each.

## 4. Draft

Read `references/writing.md`, then write the skill at the source path. Skill edits drawn from a session's lessons affect every future session, so propose them and wait for the user's approval before writing.

Then run the no-op pass over everything you wrote or touched.

Done when the draft is saved at the source path.

## 5. Validate

Run `python3 <this skill's directory>/scripts/validate_skill.py <skill-dir>` and fix every error. It checks the frontmatter, name, and description; that links and bundled paths exist; that bold skill mentions resolve; that invocation is marked consistently across harnesses; and that no bare placeholder hides in rendered markdown.

Run each bundled script on one passing and one failing input. Then run the checks the repo's own instructions name for a skill change. For a rename, removal, or merge, grep for the old name across skills, agents, READMEs, and manifests, and fix every hit in the same change.

Done when the validator prints `OK`, every script behaves on both inputs, the repo's checks pass, and the grep returns nothing.

## 6. Test

Follow `references/testing.md`:

- **A skill that changes what the agent does, or an edit to one:** the behavior test.
- **A model-invoked skill with a new or changed description, or one that didn't fire:** the trigger test as well.
- **A style or tone skill, or a one-line edit:** a read-through shown to the user instead.

Then clean up as that file's last section says.

Done when you hold the evidence each test names, or the user has approved the read-through, and cleanup is done.

## 7. Hand off

Keep the skill change in its own commit, separate from feature work and from repo setup. When shared files like a README already hold unrelated edits, stage only this skill's hunks. If the repo installs skills by linking them, run its installer for a new skill.

**Reply:** the source path; what changed and the need behind it; the invocation choice; validator and script evidence; each test's result with cost per arm; and anything skipped, with the reason.
