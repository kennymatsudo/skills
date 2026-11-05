# Tuning the map skill

A repeatable loop for improving `skills/map/` against a real repo: run the skill, measure the map it builds, look at the page, have reviewers critique it, then fix the prompts, checks, or renderer. Paste the prompt below into a new session started at this repo's root, with `<TARGET_REPO>` replaced by the repo to map.

A round on a medium repo costs about $6 and 30 minutes, most of it background building, so four rounds come to roughly $25. Raise `--max-budget-usd` for a large monorepo.

```
Iterate on the /map skill (skills/map/ in this repo): its prompts, its checks in scripts/map_file.py, and its UI in scripts/render_html.py. Goals, in order: accuracy, speed, and a UI that matches how a senior developer reads an architecture. No repeated information, no text without a purpose, and a short, plain role for every box.

Test target: <TARGET_REPO>. Never edit that repo. Clone it into your scratchpad and run the skill on the clone.

Loop until a round makes no improvement worth keeping, or 4 rounds, whichever comes first:

1. Run. Map the clone headlessly with the skill read by path, not as an installed plugin, because the installed kskills plugin may predate the changes:
   claude -p "Map this repo. Read <this repo>/skills/map/SKILL.md and follow it exactly, including building ahead in the background." --add-dir <this repo>/skills/map --permission-mode acceptEdits --allowedTools "Bash Read Write Edit Glob Grep Agent" --max-budget-usd 15 --output-format json
   Record cost, time taken, and how many boxes were still unbuilt at the end.

2. Measure. From .map/map.json count the boxes, arrows, findings by severity, unknowns, and paths. Then grade each item:
   - findings or unknowns that restate another one
   - unknowns that are only code nobody read yet
   - roles that repeat a box's name or describe how it works instead of what it does
   - code mapped under two boxes
   - arrows with no citation, or with a wrong one
   Spot-check at least 5 citations against the code.

3. Look. Open .map/map.html in a browser tool at desktop size, and screenshot level 1, one level 2, and one call path. If file:// URLs are blocked, serve the page through a route on the browser tool instead of starting a local server. Save screenshots inside this repo, and delete them when done.

4. Critique. Spawn 3 subagents in parallel on a mid-tier model, one each as a UX designer, a DX engineer, and a staff architect. Give each the screenshots, map.json, and the skill's files, and ask for its top 5 problems with evidence. Judge every point yourself before acting on it: accept it, reject it, or change it, with one line of reasoning per point. Do not accept a critique just because a subagent made it.

5. Fix. Change the prompts, the checks, or the renderer. Where a rule can be enforced in code, enforce it in map_file.py rather than only asking for it in a prompt. Run the old map.json through the new checks to see what they catch.

Constraints:
- Keep Pele (https://pele.run/) as the renderer, loaded from cdn.jsdelivr.net at a pinned version at least two weeks old.
- Follow AGENTS.md: no tool or product names in the skill, name a model tier and not a model, and validate with skills/create-skill's validator, `npx skills add . --list`, and `claude plugin validate .`.
- Do not commit. When done, report a table of metrics before and after for each round, the critiques you accepted and rejected with your reasons, and what is still open.
```
