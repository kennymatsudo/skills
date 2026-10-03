---
name: why
description: >-
  Find out why code has its current shape: trace the history of the exact lines
  through git and PRs, follow the tickets, docs, and threads that history points
  to, and return a cited reason, whether it still holds, and how to change the
  code safely. Use for "why does X work this way", "why is this here", "why did we
  pick Y over Z", "is it safe to remove this", "where did this number come from".
  Use how for what the code does at runtime.
---

# Why

You own a reason the user can act on before changing code. A named gap beats a plausible guess, because the user will edit or delete code on the strength of your answer.

Read only. Never edit code, and never post, comment, or message anyone; draft the message instead. Skip analytics warehouses, log, metric, and trace tools, and error trackers unless the user asks for them.

## 1. Scope

Name the target (files, line ranges, symbols) and the question. If the target is vague, state your reading in one line and proceed. If the question carries a guess ("I assume it's for performance?"), record it as one candidate to test, not a conclusion to confirm. If the user proposes a change, record that too.

Done when you can say `why <question>, about <path:start-end>`.

## 2. Trace the lines' history

Do this yourself.

- Find where the behavior first appeared, not just the last touch. `git blame` shows only the latest edit. Use `git log -L <start>,<end>:<file>`, `git log -S '<literal>' --reverse` or `-G '<regex>'`, and `--follow` across renames. Skip formatting, move, and bot commits and keep going back.
- For each commit that changed the behavior, read the diff, not just the message. Messages often describe a different change, and a squash merge can hide which part carried the reason.
- Pull the pull or merge request through whatever reaches the code host: its CLI (such as `gh` or `glab`), its API, or a tool in the session. Read the body, the discussion, and the inline review comments. If nothing reaches the host, say so in Gaps.
- Search the code host's issues and pull requests, including closed and unmerged ones, for earlier attempts to change this behavior, and for the user's proposed change by name. A rejected attempt is the strongest evidence of whether a change is safe.
- Read comments near the target, tests that pin the behavior, and any ADR or design doc in the repo.
- Collect anchors: PR numbers, ticket IDs, links, incident IDs, authors, reviewers, dates, and alternatives that were named and rejected.

Done when you have reached the commit that introduced the behavior and listed the anchors. If a commit, PR, or comment already states the reason in full, skip to step 4.

## 3. Follow the anchors

Search outside git only with what step 2 found: ticket IDs, PR URLs, incident IDs, error strings, and the author's name within a few weeks of the merge date. A keyword sweep without anchors returns noise.

List the tools this session has and match each to the kind of source it reaches: ticket tracker, documents, chat, or enterprise search. Match on what the tool can search, not its name. One enterprise search tool can cover chat, docs, and tickets at once, so treat it as one source. Name each kind with no tool in Gaps, as unsearched rather than empty.

- **One or two anchors:** look them up yourself.
- **Several independent anchors:** spawn one read-only subagent per source on a mid-tier model, in parallel, with the prompt in `references/searcher-prompt.md`. Paste the evidence rules below into it. Never give two subagents the same source.

Hunt for rejected alternatives, and if the code is defensive (a guard, retry, timeout, limit, flag), for the incident or postmortem behind it.

Evidence rules:

- Quote the words that state the reason verbatim, with a link, ID, or hash.
- Read whole threads, tickets, and docs, paging through long ones; the reason is often in a reply or a later comment.
- Record every query, including the empty ones. A dead link, denied access, or expired history is a gap, not a "no".
- The code is not evidence for its own intent. A name or a pattern says what, not why.
- When two sources disagree, keep both.

Done when every anchor has been followed or recorded as dead.

## 4. Check whether the reason still holds

For each reason found, check today's code and config: whether the upstream bug is fixed in the pinned version, whether the service, flag, customer, API, or limit it names still exists, and whether the number still matches its source. Code with no visible caller may still run through dynamic dispatch, cron, admin tools, config, or a rare recovery path; treat it as unproven, not dead.

Done when each reason is marked still holds, expired, or can't tell, with the evidence.

## 5. Write the answer

Tag every claim:

- **Direct:** someone wrote the reason down. Quote it.
- **Supported:** several independent sources point the same way. Cite each.
- **Inferred:** your reading. Hedge it and show the chain ("given A and B, likely C").
- **Unknown:** goes in Gaps.

Weigh these candidates against each other rather than settling on the first: a deliberate choice, an accident or hack, a pattern copied from elsewhere, a reason that has since expired, and no reason ever existed.

Format. Drop any section with nothing in it.

- **Answer:** one to three sentences: the reason, its tag, and whether it still holds.
- **Evidence:** one bullet per finding: tag, quote, and citation (commit hash, PR link, ticket, doc or thread link, `path:line`).
- **Other explanations:** when the evidence fits more than one story, each with what supports and undercuts it.
- **Before you change it:** what to keep, what is safe to change, how to test the change safely (behind a flag, log before removing, run old and new side by side, or switch off and watch who complains), and the risks. Skip only when the user is plainly just curious.
- **Who to ask:** the author, reviewer, or ticket owner most likely to know, with a drafted question for them.
- **Gaps:** what you searched where, what came up empty, and which sources that bear on the question were unavailable.

Reply: the answer in this format.
