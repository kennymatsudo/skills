---
name: build-verification
description: >-
  Set up and grow a repo's verification kit: the tools, feature map, and rules
  that let an agent prove a change on the running app with evidence. Sets up the
  kit when none exists, builds what an outcome needs ("prove checkout works"),
  or suggests what to add next, including the invariants and ledger settings
  explore-bugs needs. Every piece proves itself, and checks must fail on a
  planned break. Use maintain-verification to audit an existing kit.
disable-model-invocation: true
---

# Verification

You own a kit the user can trust: every piece in it has run against the real app, and every check has failed when the behavior broke. The user decides what the kit contains. Build what they ask for, and suggest only when they ask what to add.

## 1. Find the kit

Look for `verify-*/rules.md` in the repo's skills directories (`.claude/skills/`, `.agents/skills/`, `.pi/skills/`, `.cursor/skills/`).

- **None:** set one up, steps 2 to 4.
- **One:** grow it, steps 5 to 7.
- **Several:** ask which one.

Done when you know which branch you are on.

## 2. Discover

Spawn a read-only subagent on a mid-tier model with the prompt in `references/discovery-prompt.md`. Spot-check two of its citations. Ask the user only what the repo could not answer, one question at a time with your recommendation. Always confirm with the user anything that needs a human to start the app and anything with a real side effect.

Done when each of the ten discovery questions has a cited answer or the user's answer.

## 3. Write the skeleton

1. Pick the skills directory the repo already uses; if none, the one the current agent loads. Name the kit `verify-<app>` after the app.
2. Copy `references/rules.md` to `verify-<app>/rules.md`. Fill its `<...>` slots and delete sections for pieces the kit does not have yet.
3. Write `verify-<app>/SKILL.md` from `references/verify-skill-template.md`.
4. Write `features/README.md` from the index in `references/feature-map.md`, with an empty Features list.
5. Copy `scripts/check.py` to `verify-<app>/scripts/check.py`.
6. Build the doctor, following `references/pieces.md`.
7. Add the evidence directory to `.gitignore`. This is the one existing file the skeleton may edit without asking.

Done when `grep -rn '<[a-z]' verify-<app>` finds no unfilled slot.

## 4. Prove the skeleton

Run the doctor against the real app, following its proof in `references/pieces.md`. If the real start needs a human, ask the user to start the app that way and prove the doctor against that instance. Never start a substitute that skips the human step to get a ready result; if the user cannot start it now, report the doctor as unproven. Run `check.py`.

Done when you have shown the doctor's output and `check.py` exits 0. Then reply, or go on to step 5 if the user also asked for something.

## 5. Choose what to build

- **The user or explore-bugs asked for exploration setup:** the pieces are the ones under "Exploration setup" in `references/pieces.md`.
- **The user named an outcome** ("prove checkout works", "let agents see order state"): translate it into pieces, for example "feature file for checkout, a probe for order state, a check for checkout.pay". Read `features/` first and reuse what exists. The named outcome is the go-ahead to build them.
- **The user asked what to add, or named nothing:** spawn a read-only subagent on a mid-tier model with the prompt in `references/suggest-prompt.md`. If a ticket tracker is connected, give it recent bugs for the app. Show the top three to five suggestions in plain words with their reasons, and let the user pick.

If no one can pick, stop here and report the suggestions. Build nothing.

Done when the list of pieces is written in your reply before any file is created, and for suggestions, the user has picked.

## 6. Build each piece

Follow `references/pieces.md` for each kind and the kit's `rules.md` for its contract. Add or update the feature file line for every sub-feature a piece serves.

Done when every listed piece exists and its feature file line names it.

## 7. Prove each piece

Run each piece's proof from `references/pieces.md` against the real app and show the output. A check is proven only after it fails on a planned break in a scratch worktree. Then run `check.py`.

Done when a `Planned break:` or `Planned fix:` line went to the user before each worktree was created, every piece has shown its proof, every check line says break-tested or why not, and `check.py` exits 0.

## Guardrails

- Change product code only in a scratch worktree for a planned break, and remove the worktree after.
- Add new files freely, but edit an existing file outside the kit (a Makefile, package manifest, config, or CI file) only after the user agrees to that exact edit.
- Drive and stop only instances this run started, or ones the user named. Stop processes by the PID you started, never by name.
- Run an action with a real or shared side effect only after the user's OK in this session.
- Add levels of proof, extra skills, or workflow rules only when the user asks for them.

Reply: the kit path; each piece added, with the command that ran it and its result; each check's planned break and the failure it caused; sub-features still marked "No check yet" or not break-tested; and anything the user must do, such as starting the app.
