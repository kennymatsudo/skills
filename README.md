# kskills

My personal agent skills, in the [Agent Skills](https://agentskills.io) format. They work with Claude Code, Codex, Cursor, and any other agent the `skills` CLI supports.

## Skills

### General

| Skill | What it does |
| --- | --- |
| [clean-up-comments](skills/clean-up-comments/SKILL.md) | Rewrites, deletes, or adds comments on the current diff so they're plain and useful. Never touches code. |
| [commit](skills/commit/SKILL.md) | Stages changes and commits with a short title and scannable body, folding follow-ups into unpushed commits. |
| [how](skills/how/SKILL.md) | Explains how a system or code path works, one zoom level at a time, with every claim cited. |
| [rename-variables](skills/rename-variables/SKILL.md) | Renames identifiers your branch adds, or under a given path, so each is honest and in the repo's vocabulary, updating every reference. |
| [restate](skills/restate/SKILL.md) | Restates your request in its own words, with the established name for the pattern, and waits for a yes. |
| [review-design](skills/review-design/SKILL.md) | Reviews a branch or codebase against design principles, domain boundaries, and service layering, and returns a ranked, code-cited report. |
| [review-tests](skills/review-tests/SKILL.md) | Reviews the tests a branch adds or changes, proves each can fail, catches weakened tests, and applies the safe fixes. |
| [squash](skills/squash/SKILL.md) | Squashes a branch's unpushed commits, or the whole branch including pushed ones, into one commit describing the net result. |
| [trim](skills/trim/SKILL.md) | Cuts redundancy from any document without changing what it says. |
| [unslop](skills/unslop/SKILL.md) | Cleans AI slop out of prose or a code diff so a person wants to read it. |
| [update-agent-instructions](skills/update-agent-instructions/SKILL.md) | Proposes edits to AGENTS.md, CLAUDE.md, and skills from lessons in the current session. |
| [why](skills/why/SKILL.md) | Traces why code has its current shape through git, PRs, tickets, and docs, and says whether the reason still holds. |

### Verification

Skills for proving a change works on the running app, not just in tests.

| Skill | What it does |
| --- | --- |
| [build-verification](skills/build-verification/SKILL.md) | Sets up and grows a repo's verification kit so an agent can prove a change works on the running app. |
| [maintain-verification](skills/maintain-verification/SKILL.md) | Audits a repo's verification kit against the code and running app, and fixes the kit's own files. |

## Install

With the [`skills` CLI](https://skills.sh), for any supported agent:

```sh
npx skills add kennymatsudo/skills          # pick skills and agents interactively
npx skills add kennymatsudo/skills --list   # list skills without installing
npx skills add kennymatsudo/skills -s <skill-name> -g   # one skill, user-level
```

As a Claude Code plugin:

```
/plugin marketplace add kennymatsudo/skills
/plugin install kskills@kskills
```

## Layout

Each skill is a folder under `skills/` with a `SKILL.md`:

```
skills/
  <skill-name>/
    SKILL.md        # required: YAML frontmatter (name, description) + instructions
    scripts/        # optional
    references/     # optional
```

The folder name must match the `name` field in the frontmatter. Use lowercase letters, numbers, and hyphens.

```markdown
---
name: my-skill
description: What it does, then when to use it. The agent sees only this line when deciding to load the skill.
---

# My Skill

Instructions...
```

## Add a skill

1. Create `skills/<skill-name>/SKILL.md`, or run `npx skills init skills/<skill-name>`.
2. Check it is found: `npx skills add . --list`.
3. Add a row to the matching table under [Skills](#skills).
4. Commit and push. Users get it with `npx skills update` or `/plugin marketplace update`.

The Claude Code plugin picks up every folder under `skills/` automatically, so the manifests in `.claude-plugin/` need no edits when you add a skill.

## Acknowledgments

Many of these skills draw on ideas from [Matt Pocock's skills](https://github.com/mattpocock/skills), [pstack](https://github.com/cursor/plugins/tree/main/pstack), and Cursor's [cursor-team-kit](https://github.com/cursor/plugins/tree/main/cursor-team-kit). A skill that adapts their text carries the original license in its `THIRD_PARTY_LICENSE.md`.
