# Working in kskills

Agent skills in the [Agent Skills](https://agentskills.io) format, published through the `skills` CLI and as a Claude Code plugin marketplace. The README has the install commands and the skills index.

## Repo rules

- One folder per skill: `skills/<name>/SKILL.md`, with `references/` for material only some branches read and `scripts/` for deterministic checks. The plugin auto-discovers skills, so no manifest edits.
- Skills must stand alone. No paths into other repos, the author's machine, or another skill collection's setup files.
- Write for every harness: say "spawn a subagent", not a tool name, and name a model tier ("mid-tier"), not a model.
- Name the kind of tool a skill needs (ticket tracker, chat, code host), never the product. Have the skill list the session's tools, match each by what it can search rather than its name, and report a kind with no tool as unsearched, not empty.
- The main agent synthesizes and judges, on whatever model the user chose. Subagents gather evidence on a mid-tier model. Don't add a separate stronger synthesizer.

## Creating or adapting a skill

Follow this repo's `skills/create-skill/SKILL.md`, not an installed create-skill of the same name. It covers research, settling the design with the user, drafting, validation, testing, and name collisions with installed skills. This repo adds:

- **Validate.** After its validator, run `npx skills add . --list`, and `claude plugin validate .` if the Claude Code CLI is installed.
- **Trim.** Follow this repo's `skills/trim/SKILL.md` on the new skill.
- **Commit.** Follow this repo's `skills/commit/SKILL.md`, not an installed commit skill of the same name. Separate commits per concern, for example repo setup apart from a new skill.
- **README.** Add or update the skill's row in the README's skills index.
