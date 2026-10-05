# Writing a skill

## Description

The description is the only thing the harness sees when deciding whether to load the skill. Write it for retrieval.

- Front-load what it does, then the triggers. Displays truncate, so the first sentence carries the key fact.
- Quote the phrasings that should trigger it, one per distinct case. Synonyms for the same case are waste.
- Name the nearest sibling ("use X for Y") and when to skip, so neighbors don't steal each other's triggers.
- Choose invocation on purpose. Make a skill model-invoked only when the agent must reach it unprompted or another skill must call it. Otherwise make it user-invoked with a one-line description for the human, because model-invoked descriptions compete for attention on every turn.
- Mark a user-invoked skill in two places, because harnesses disagree on where to look: `disable-model-invocation: true` in the frontmatter, and `agents/openai.yaml` holding `policy:` / `allow_implicit_invocation: false`, unless the repo's installer generates that file.

## Body

- Open with one line naming what the agent owns. Give numbered steps that each end on a "Done when" criterion that can pass or fail. Close with a `Reply:` line naming the deliverable.
- Keep only prose that changes a decision. Run a no-op pass: delete each sentence the model would follow anyway, the whole sentence rather than a few words of it.
- Tell the agent what to do. Give the why only where a rule looks wrong or arbitrary without it, in one clause.
- Phrase the target positively. Keep a prohibition only as a guardrail, paired with what to do instead.
- Reach for words the model already knows (tracer bullet, red-green, blast radius). One precise term replaces a sentence.
- When a step asks for a judgment over many items, make its criterion enumerate them: list every item, decide each, and put the decisions in the report. A judgment step without a list gets skipped silently.
- Inline what every path needs. Move what only some branches reach (subagent prompts, rubrics, examples, per-source details) into `references/`, one level deep, named by path from the body. Put deterministic work in `scripts/`, and say whether the agent runs or reads each one.
- Delegate to another skill by name, and tell the agent to load it, instead of restating it. Leave out any one harness's command syntax, such as a leading `/`.
- Write for every harness the skill installs to. Say "the agent" and "spawn a subagent", not one tool's API. Name a model tier ("mid-tier"), not a model.
- Point at the live source for volatile facts (model names, versions, paths, counts, API surfaces), and tell the skill to prefer what it finds there over anything written in it.

## An edit

Make the smallest change that fixes the stated failure. If the guidance was already there and got missed, move or sharpen it instead of adding more. After a model upgrade, prefer a deletion-only pass that removes what the model now does unprompted.
