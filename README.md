# kskills

My personal agent skills, in the [Agent Skills](https://agentskills.io) format. They work with Claude Code, Codex, Cursor, and any other agent the `skills` CLI supports.

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
3. Commit and push. Users get it with `npx skills update` or `/plugin marketplace update`.

The Claude Code plugin picks up every folder under `skills/` automatically, so the manifests in `.claude-plugin/` need no edits when you add a skill.

## Acknowledgments

Many of these skills draw on ideas from [Matt Pocock's skills](https://github.com/mattpocock/skills), [pstack](https://github.com/cursor/plugins/tree/main/pstack), and Cursor's [cursor-team-kit](https://github.com/cursor/plugins/tree/main/cursor-team-kit). A skill that adapts their text carries the original license in its `THIRD_PARTY_LICENSE.md`.
