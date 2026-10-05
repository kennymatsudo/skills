# Deciding what a lesson becomes

Everything a skill makes the agent read costs attention: its description on every turn it might trigger, its body every time it loads. Treat deletion as the default improvement and addition as the thing that needs a reason.

## Pick the strongest home

Stronger homes enforce the rule without the agent's cooperation; prose is the last resort.

- **A check.** If a lint rule, type, schema, script, hook, or validator can enforce it, build that and write no prose. A skill that needs the rule runs the script.
- **Nothing.** A one-off, a fact the environment already states (config, types, `--help`, the code), or something the model already does unprompted. Point at the source if the skill needs it.
- **An edit to an existing skill.** A recurring correction inside a job some skill already owns.
- **A global rule or always-loaded instructions.** A rule that applies across many kinds of tasks, not one workflow.
- **A new skill.** A recurring multi-step workflow with its own trigger that no existing skill is a real home for.

Codify only what clears all four:

- **Recurs.** Seen in two or more sessions, or stated by the user as a standing rule. A skill distilled from one run over-fits to it.
- **Durable.** Still true once paths, commit hashes, versions, and code shapes have changed.
- **Changes a decision.** A future agent would act differently because of it, not just read more.
- **Safe to share.** No secrets, internal names, or machine paths.

## Update or create

Default to editing. Before creating anything, search the installed skills' names and descriptions for one that already owns the job.

- **The guidance exists but was missed.** Fix its placement or wording. Don't add a second copy.
- **The skill existed but didn't fire.** Fix the description, not the body.
- **The skill fired and still went wrong.** Edit the body, and only in skills the failing session actually loaded.
- **Create a new skill** only when it has a distinct trigger (a phrase the user actually types, or a situation the agent must recognize on its own) and no existing skill is a real home. Reuse motivates an extraction but isn't the test.
- **Extract shared material** into its own skill when two or more skills must invoke it. Otherwise it stays inside the skill that owns it.
- **Split a skill** only when its later steps tempt the agent to rush the earlier ones, or its branches share nothing.
- **Merge overlapping skills.** Keep the better-named one, delete the other, and name the replacement in the commit. Rename cleanly, updating every reference in the same change, rather than keeping an alias.
- **Delete a skill** that went unused or was absorbed elsewhere. An idle skill still costs its description and its upkeep.
