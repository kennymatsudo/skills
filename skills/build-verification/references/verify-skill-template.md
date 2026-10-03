# Template for `verify-<app>/SKILL.md`

Fill every `<...>` from discovery. Delete a line that does not apply rather than leaving it vague. The generated skill is read cold, mid-task, by an agent that has never seen the app, so give exact commands.

---

```markdown
---
name: verify-<app>
description: >-
  Prove a change to <app> works by driving the running <surface> and reading back
  the result, with evidence. Use before handing back any change to <app>'s
  user-facing behavior, or when asked to verify, prove, or check a <app> feature.
---

# Verify <app>

You own the claim that a change works, backed by evidence a reviewer can rerun. Follow `rules.md` for every proof and every report.

## 1. Check the instance

Run `<doctor command>`. Drive only an instance that reports ready and runs the code under test.

- Not running: <start it with `<start command>` and wait for `<ready line>` | ask the user to start it with `<start command>`; an agent cannot, because <reason>>.
- Running different code: say so and stop. Never restart an instance this session did not start.

## 2. Find the features

Open `features/README.md` and the file for every feature the change touches. List the sub-feature IDs the change could affect.

## 3. Prove each one

Run the command under "How to prove it" for each listed ID. When a line says "No check yet" or "Unreachable", report that ID as not verified with that reason. Do not substitute a different entry point.

## 4. Keep the map true

If the change adds, removes, or alters a user-facing behavior, update its feature file in the same change: the sub-feature line, how a user reaches it, and its proof line. Run `<check command>` and fix every error.

## 5. Clean up

Stop only what this session started. Keep the evidence files in `<evidence dir>`.

Reply: each sub-feature as Verified, Failed, or Not verified, per the Reporting section of `rules.md`, with the code line from the evidence.
```
