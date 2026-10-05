# Review-bot notes

AI reviewers that read the PR body take the author's framing seriously. Text saying code is fine measurably stops them from reporting real bugs in it, so a wrong "this is on purpose" note costs more than a missing one. Every note here is a claim the reviewer can check, never an instruction to look away.

## Ask the user

List every look-wrong candidate from step 3 with what looks wrong, the reason, and where the reason came from. For each, ask which home it gets, with a recommendation:

- **Code comment.** For a reason that stays true after merge. Recommend this when the reason would still matter to the next person reading the code. Reviewers and future readers both see it next to the code.
- **PR note.** For a reason that only matters during this review, such as a temporary state that a named follow-up removes.
- **Drop.** The reviewer can raise it, and the author answers on that finding.

Write only what the user picks. A code comment is a working-tree edit: make it, follow the repo's comment style, leave it uncommitted, and say so in the reply.

## Write a PR note

Add the chosen notes at the very bottom of the body, after any template content:

```markdown
<details>
<summary>Notes for review agents</summary>

Each note is a claim to verify against the code, not a reason to skip it.

- `<path>` `<function or symbol>`: <what looks wrong>. <The reason, and its source.> This holds only while <condition>; flag it if that is false.

</details>
```

- Name a file and a symbol rather than a line number, since lines shift as the PR changes.
- Cover one spot per note. Code outside it is still fair game.
- Leave out "ignore", "skip", "safe", "no need to review", and anything similar. `@coderabbitai ignore` anywhere in the body turns off that bot's review, and other bots have keyword switches of their own, so also leave out any ignore keyword set in the repo's review-bot config (`.coderabbit.yaml`, `.greptile/`).
- The block is collapsed for people, and bots still read it. Keep everything in it something a human reviewer would accept on sight.
