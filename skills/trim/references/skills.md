# Trimming an agent skill

A skill is read by several readers that see different text. Repetition that reaches a reader who can't see the other copy is load-bearing. Treat these cases as follows.

- **Subagent prompts.** A subagent sees only its prompt, never `SKILL.md`. Keep every rule it needs. When a prompt file restates rules from `SKILL.md`, cut the restatement from the prompt file and have `SKILL.md` say to paste those rules into the prompt.
- **Description and body.** The description is read alone, to decide whether to load the skill. Keep its triggers and sibling pointers even when the body repeats them. Cut body text that only restates the description, such as an intro saying what the skill is for.
- **Reference files.** A reference loads only on the branch that names it. When two references that load on different branches share a rule, keep both copies, or move the rule into `SKILL.md` if every branch needs it.
- **Other skills and scripts.** A rule that another skill or a bundled script already defines becomes a pointer: load that skill by name, or run the script.
- **Default test.** Keep guardrails, "Done when" criteria, and the reply line even when they read as generic. They change what the model does.
