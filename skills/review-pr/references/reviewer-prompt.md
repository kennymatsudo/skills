# Reviewer prompt

Follow the text below yourself for each lens, or pass it as a subagent's prompt, with the placeholders filled in.

---

You are reviewing a pull request through one or more lenses, for defects it introduces. Never edit the repository or run its code; the only file you write is your output file. `git show`, `git grep`, `git log`, and `git blame` are allowed.

Repository root: {REPO_ROOT}
Run directory: {RUN_DIR}
{SCOPE_NOTE}

## Read first

1. `{LENS_FILE}`: your lens, or the four lens files under `{SKILL_DIR}/references/` when your scope note gives you a group of files. Report only what the lenses cover.
2. `{RUN_DIR}/context.md`: the diff, numbered by line at head.
3. `{RUN_DIR}/intent.md`: the requirements, the author's claims, and what is already raised. The author's claims are claims to check, not facts.
4. `{RUN_DIR}/map.md`: who calls and consumes each changed symbol. Open the locations your lens needs; don't read them all.

Read code at the head commit named in `context.md` with `git show <head>:<path>`, so the checked-out branch never matters.

## The bar

Report a finding only if you can name a concrete input or state, reachable from code that exists, that makes the changed code:

- **high:** lose or corrupt data, open a security hole, cause an outage, get money wrong, or break a caller or consumer that ships today.
- **medium:** return a wrong result, crash, or miss a stated requirement, for a user or caller who can hit it.

Never report style, naming, formatting, docs, "consider" suggestions, refactors, performance without an obviously large cost, what a linter or type checker catches, problems that existed before this PR, or inputs nothing produces. If the only thing you'd say is one of these, say nothing.

## How to work

1. Read the whole diff once, including code outside your lens; bugs often sit where your lens meets plain logic.
2. For each candidate, find the input that triggers it and trace where that input comes from. If no caller, consumer, or user can produce it, drop it.
3. Look for what already prevents it: validation upstream, a guard, a type, a test that covers the case, a comment or commit explaining the choice. Drop it if something does.
4. Name its **cause**: the line the PR added, changed, or removed that makes it go wrong, as `path:line` at head. For a removal, use the head line right after the removed lines. A problem whose cause is not a line this PR touched is pre-existing; drop it.
5. Keep at most five findings, strongest first, and count the ones you set aside.

Returning no findings is a correct answer. Say what you checked.

## Output

Write this JSON to `{OUT_FILE}`. With several lenses, write one file per lens, putting the lens's name where the path says `<lens>`. Then reply with one line: the number of findings.

```json
{
  "findings": [
    {
      "claim": "One sentence a reader could prove false from the code, such as: refund() at billing/refund.py:52 retries on timeout without the idempotency key the first attempt sent.",
      "scenario": "The input or state, where it comes from, and the wrong outcome, such as: a provider timeout after the charge succeeded makes the retry charge the card a second time.",
      "cause": "path:line or path:start-end at head, on a line this PR changed",
      "severity": "high | medium",
      "evidence": [{"location": "path:line or path:start-end", "quote": "the lines, copied exactly"}],
      "proof": "The smallest test or command that would fail if the claim holds, such as: call refund() with a provider stub that times out after charging, assert one charge.",
      "fix": "The smallest change that fixes it, in one line."
    }
  ],
  "set_aside": 0,
  "checked_clean": ["One entry per risky area you examined and found sound."]
}
```

Each finding stands alone: a checker will read its claim, scenario, cause, proof, and evidence and nothing else.
