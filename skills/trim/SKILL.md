---
name: trim
description: >-
  Cut redundancy from a document without changing what it says: rules stated
  more than once, near-duplicates worded differently, explanations the reader
  would act on anyway, and sentences that carry nothing. Edits in place, then
  reports each cut. Works on any document (skill, AGENTS.md, README, design
  doc, PR description). Use for "trim this", "is there anything redundant",
  "what can you cut from this skill". Use unslop to restructure or fix
  wording.
---

# Trim

You own a shorter document that says everything the original said.

Only cut. Never add content, reorder sections, or reword a sentence, except to merge two copies of one point. Note structural or wording problems in the report for the unslop skill instead of fixing them.

## 1. Scope

The target is a file, a skill directory, pasted text, or the last document produced in the session. Copy the original to a scratch file; the verifier needs it. Name the reader: a model for agent instructions, a human otherwise. For an agent skill, also read `references/skills.md`.

Done when the original is saved and the reader is named.

## 2. Find candidates

Read the whole target, including every file it links to that the reader will load. List each candidate with its location:

- **Duplicate.** One point stated in two or more places, in any wording. Two copies that disagree are a conflict, not a duplicate.
- **Default.** Generic advice that could appear unchanged in any document of this kind, such as "read a file before editing it". A definition or claim about this document's subject is never default, even when it sounds obvious.
- **Empty.** A sentence that carries no rule, fact, or reason, such as an intro that restates the heading.

Done when every paragraph has been checked and each candidate is on the list.

## 3. Decide

Decide each candidate, and record the decision for the report:

- **Duplicate:** keep the copy at the point of use, where the reader is when they need it. If neither copy is, keep the more specific one. When the other copy holds a detail the kept one lacks, fold that detail in, then delete the other copy.
- **Conflict:** keep both and report them. The user decides which is right.
- **Default or empty:** cut it.
- **Reasons:** keep at least one copy of every reason a rule gives. A rule without its why can't be safely changed later.
- **Pointers:** keep cross-references like "see Audit". Before deleting a heading, anchor, or exact phrase, grep the repo for links or scripts that point at it, and keep it if anything does.

Done when every candidate is marked cut, merged, kept, or conflict.

## 4. Apply and verify

1. Make the cuts and merges.
2. Spawn one subagent on a mid-tier model with the prompt in `references/verifier-prompt.md`, the original, and the trimmed text. Do not give it the decision list.
3. For each claim it reports missing or changed: if it is a planned default or empty cut, leave it out. Otherwise restore it.

Done when every verifier finding is restored or matches a planned cut.

**Reply:** the line count before and after, then the cuts grouped as duplicate (with where the kept copy lives), merged, default, and empty, one line each. Then conflicts and any structure or wording problems for unslop. For pasted text, include the trimmed text.
