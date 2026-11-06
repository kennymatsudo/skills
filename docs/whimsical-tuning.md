# Tuning the whimsical-diagram skill

A repeatable loop for improving `skills/whimsical-diagram/` against a real design doc: draw boards with the skill, look at them, have critics score them, then fix the rules, references, or scripts. Paste the prompt below into a new session started at this repo's root, with `<SOURCE_DOC>` replaced by the design doc to draw from and `<FOLDER_ID>` by a private Whimsical folder.

A round costs about $10 and 15 to 30 minutes for two questions, most of it the skill's own review loop.

Two lessons from the first eight rounds shape the prompt:

- Critics scoring 1 to 10 settle at 6 to 8 and drift by a point between rounds on boards that barely changed. Use their scores to find recurring problems, not as the stopping bar. Decide whether a round helped with a pairwise comparison in both orders.
- Fix a layout problem with a script, not more prose. The parts board went from 5.7 to 8 when its layout moved into `scripts/parts_board.py`; rules the agent had to apply by hand kept being broken.

```
Iterate on the whimsical-diagram skill (skills/whimsical-diagram/ in this repo): its SKILL.md, its references, and its scripts. Goal: boards an engineer would bring to a design review as is: accurate, uncluttered, one question per board, readable on first pass.

Source: <SOURCE_DOC>. Never edit it. Every board goes in the private Whimsical folder <FOLDER_ID>; nothing outside it.

Test questions, the same every round so rounds compare:
1. An overview: "What are the parts of <system>, and how does <one request> travel through it end to end?"
2. A detail question: "In one <exchange>, who waits, what are the timeouts, and how is it kept idempotent?"

Loop until two rounds in a row make no improvement worth keeping, or 6 rounds:

1. Run. For each question, draw headlessly with the skill read by path, prefixing board titles with the round ("R3 "):
   claude -p "Draw a Whimsical diagram. Read <this repo>/skills/whimsical-diagram/SKILL.md and follow it exactly, including its review loop. Question: <q>. Audience: engineers reviewing the design. Source: <SOURCE_DOC>. Create every board inside folder <FOLDER_ID>. Prefix titles with 'R<n> '. End with 'BOARD: <id>'." --add-dir <skill dir> --add-dir <source dir> --permission-mode acceptEdits --allowedTools "Bash Read Write Edit Glob Grep Agent mcp__claude_ai_Whimsical" --max-budget-usd 12 --output-format json
   Record cost, time, board count, and the skill's own checklist scores from the reply.

2. Look. Fetch each board as an image yourself and note what you see before reading any critique.

3. Critique. Spawn 3 subagents in parallel on a mid-tier model: a visual designer, a staff engineer, and a new engineer reading cold. Give each the board ids, the source path, and the skill path, with a fixed rubric (10: use as is; 8: one or two small fixes; 6: usable but cluttered or missing something; 4: misleading). Ask for a score per board, the top 5 problems naming the exact place, and the skill change that would prevent each.

4. Judge. Accept, reject, or change every point, one line each. Act on problems that recur across critics or rounds. Reject what the tool can't do (Whimsical lays out sequence diagrams itself) and what is an artifact of the test setup.

5. Fix. Where a rule can be enforced in a script, put it there. Check the scripts with a good spec and a bad one, and draw a script change on a scratch board in the folder before a full run.

6. Compare. When a round changes structure, have two fresh critics compare round 1's boards with the latest, in opposite orders. Trust a preference only if it holds both ways.

Constraints:
- Follow AGENTS.md: no tool or product names in the skill, name a model tier and not a model, and validate with skills/create-skill's validator, `npx skills add . --list`, and `claude plugin validate .`.
- Do not commit. When done, report a table of scores per round, the pairwise results, the critiques accepted and rejected with reasons, and what is still open.
```
