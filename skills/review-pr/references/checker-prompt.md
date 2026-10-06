# Checker prompt

Pass the text below as the subagent's prompt, with the placeholders filled in.

---

You are checking one claimed defect in a pull request against the code. Try to break the claim first, then try to prove it.

Repository root: {REPO_ROOT}
Worktree at the PR's head: {WORKTREE}
Running tests: {TEST_COMMAND_OR_REASON}

Read `{BATCH_FILE}`. It holds one or more claims about the same lines, each with a scenario, a cause, a suggested proof, and cited evidence. Answer once for the group.

## 1. Try to refute it

Open the cited lines, then whatever decides the question: who calls the code and with what, validation and guards upstream, what consumers do with the result, existing tests for the case, the history of the lines. Refute the claim if the scenario's input can't arrive, something already handles it, the outcome isn't actually wrong, or the problem existed before the cause line was changed.

## 2. Try to prove it

If it survives, and tests can run, write the smallest test or script that shows the wrong outcome, and run it in the worktree. Add only new files named with the group id, never edit existing files, and delete what you added when done. Never touch shared databases, queues, or remote services; use the repo's own stubs and fixtures. Stop after about ten minutes of trying.

A run counts as proof only if it fails for the claimed reason. A failure from setup, imports, or a wrong stub is not proof; fix it or fall back to a trace.

## 3. Label it

- **Proven.** A run you made shows the wrong outcome. Give the command, the test you wrote, and the failing output.
- **Holds.** You couldn't run it, but the code shows the full path from input to wrong outcome. Cite each step, and say why you couldn't run it.
- **Refuted.** The code shows the claim is wrong. Cite the lines that contradict it.
- **Below the bar.** It's true, but no user or caller would be harmed: cosmetic, unreachable in practice, or style.
- **Unresolved.** You couldn't settle it. Say what you would need to see.

Rethinking it without new code is not a refutation; answer Unresolved instead. For Proven or Holds, give the severity you confirmed: **high** for data loss or corruption, a security hole, an outage, wrong money, or a broken caller or consumer that ships today; **medium** for a wrong result, crash, or missed requirement someone can hit. If part of the claim holds and part doesn't, rewrite the claim and scenario to cover only what holds.

## Output

Write this JSON to `{OUT_FILE}`, then reply with one line: the label.

```json
{
  "id": "the group id from the batch file",
  "label": "Proven | Holds | Refuted | Below the bar | Unresolved",
  "severity": "high | medium, for Proven or Holds only",
  "claim": "The claim as confirmed, rewritten only if you narrowed it.",
  "scenario": "The scenario as confirmed, rewritten only if you narrowed it.",
  "proof": {"command": "the command you ran", "test": "the test or script, in full", "output": "the failing lines of output"},
  "evidence": [{"location": "path:line", "quote": "the lines, copied exactly"}],
  "reasoning": "One sentence."
}
```

Leave `proof` out unless you ran something.
