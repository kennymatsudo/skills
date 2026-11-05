---
name: how
description: >-
  Explain how a system or code path works, one zoom level at a time: services and
  how they call each other by default, then the components inside one service, then
  the method-by-method path, with every claim cited and checked. Use for "how does X
  work", "walk me through X", "what calls what", "more detail on Y". Use why for the
  reasoning behind a design, and walkthrough to understand what a PR changed.
---

# How

You own an explanation the user can trust without re-checking it. A short answer with gaps named beats a complete one with a wrong claim.

## Zoom levels

| Level | Shows | Entry point | Flow | Response |
|---|---|---|---|---|
| 1. Services (default) | Deployable services, datastores, queues, and outside systems at the edge | Public endpoint, event, or scheduled job | Network calls and messages | What crosses the wire, including errors |
| 2. Components | The main modules or classes inside one service | Route handler, consumer, or command | Calls between modules | Return types and raised errors |
| 3. Code | One path, method by method | Function signature | Each call and why it is made | Return values and branches |

Answer at level 1 unless the user asks for detail. If level 1 would show two hops or fewer, as in a repo with one backend, answer at level 2 and say so in the Overview. "More detail on Y" means one level down, on Y only. Level 3 covers a single path, never a whole service.

## 1. Scope

Name the target, the level, and the boundary: where the explanation starts and stops. If the request is ambiguous, state your reading in one line and proceed; the user can redirect.

If the target is a PR or a branch that is not checked out, fetch it and add a git worktree at its head. Run every later step, including subagents and the citation check, against that worktree, and remove it when done. Checks against local files pass even though they describe a different version.

Done when you can say `level N, from <entry> to <response>, covering <target>`.

## 2. Gather evidence

Read code, configs, and schemas. Allowed beyond reading: `git log` and `git blame` for fences. Never run the code, its tests, or a build.

- **One service or one path:** explore it yourself.
- **Several services or a broad target:** split it into 2 to 4 slices, such as one per service or one per hop, and spawn one read-only subagent per slice in parallel with the prompt in `references/explorer-prompt.md`. Run explorers on a mid-tier model, not the session's strongest. Paste the rules under "While gathering" into the prompt.

While gathering:

- **Follow the wiring, not the names.** Confirm a call by finding the client call, route registration, queue topic, or config that connects the two sides. A matching name is a guess.
- **Tests are a weaker witness than code.** Look only for tests of the target entry point or behavior. Cite a test when it asserts concrete inputs and outputs, an error or edge case, or links a bug. Skip tests that mock everything and only assert calls were made. When a test and the code disagree, the code says what happens and the mismatch is a finding.
- **Check fences.** A fence is code that looks wrong or redundant but may be deliberate: an odd guard, a retry, a sleep, a special case, a workaround. Run `git blame -L <start>,<end> <file>`, then `git log -1 --format=%B <commit>`, and read comments near the code. Stop there. Searching PRs, tickets, chat, or docs belongs to the why skill.

Done when every hop in scope has an entry point, the next call, and a response, each backed by a file and line or marked unknown.

## 3. Draft

Write the answer in the format below. Tag every claim:

- **Verified:** cite `path/to/file.ext:LINE` or `path/to/file.ext:START-END` from the repo root.
- **Inferred:** mark it `(inferred)` and say from what.
- **Unknown:** put it in Unknowns.

Done when no sentence makes an untagged claim about behavior, every Flow line is one sentence naming one hop at the scoped level, and the draft is about 40 lines or fewer.

## 4. Verify

1. Run `python3 scripts/check_citations.py <repo-root> <draft-file>` from this skill's directory, and fix every failure.
2. Spawn one read-only subagent on a mid-tier model, one that reads whole files rather than a search-only agent, with the prompt in `references/verifier-prompt.md` and only the draft, not your reasoning.
3. For each claim it marks wrong or unsupported: correct it from the code, downgrade it to inferred, or move it to Unknowns.
4. Rerun the script on the final text you will send.

Done when the script passes on the final text and every verifier finding is resolved.

## Format

Drop any section with nothing in it. Keep the reply to about 40 lines, diagram included. A hop is one row of the scoped level's Flow column: at level 1 a network call or message between services, at level 2 a call between modules. What happens inside a hop, such as a validation rule, a field name, a retry count, or an error class, belongs one level down, where "more detail on Y" reaches it. When the reply runs long, cut that in-hop detail first, then the lowest-ranked Fences and Unknowns.

- **Overview:** two sentences. What it is and what it does. If the request was ambiguous, add one line naming the target you picked.
- **Key findings:** up to three, one line each, the ones the reader would act on, such as a path that never completes or a race. Each is repeated with its citation in Fences or Responses.
- **Diagram:** a plain-text diagram in a code block, drawn with boxes and arrows, so it reads the same in a terminal, a chat window, or a PR. At level 1, the main path between services. At level 2, the components inside the service when more than two interact. At level 3, a numbered call chain instead. Use mermaid only when the user asks for it or the explanation goes into a file that renders it.
- **Entry Points:** each trigger and where it is defined, one line each.
- **Flow:** one sentence per hop in order: who calls whom, with what. Add why only when it is not obvious.
- **Responses:** a table with columns for case, status or return, and what the caller sees, covering success, error, and empty cases.
- **Fences:** at most three oddities on the path in scope, most consequential first, each with what the commit or comment says, or "No reason found in the code or commit history. The why skill can dig further." Leave out oddities in code the path does not execute, even in the same file or controller.
- **Unknowns:** what you could not trace, and where you stopped.

Put the citation at the end of its line. Say nothing about the verification step when it passed: no citation counts, no fixes you made along the way.

Reply: the verified explanation in this format, at the scoped level.
