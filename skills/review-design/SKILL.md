---
name: review-design
description: >-
  Review an implementation (your branch or the codebase) against software design
  principles, including domain boundaries and service layering: one evaluator
  per principle in parallel, a checking pass that must
  cite code to keep or drop each finding, then a ranked report you can act on here
  or hand off. Use for "design review", "review the design of my branch", "what
  should I refactor", "review this service's structure". Use review-pr for bugs.
disable-model-invocation: true
---

# Design Review

You own a ranked list of design findings that survive a second look. Two findings that hold beat ten the user has to re-check. "No findings" is a valid result.

Report only, and never run the code or its tests. Run this skill's script from the repo root as `python3 <skill-dir>/scripts/claims.py`, with the absolute path of this skill's directory, and keep its files in a run directory made with `mktemp -d` outside the repo. Change code only after the user picks a finding and chooses to implement it here.

## 1. Pick the scope

- **Branch (default).** Everything that differs from the merge base with the default branch, whether committed, staged, unstaged, or untracked. Find the default branch with `git symbolic-ref --short refs/remotes/origin/HEAD`, else `origin/main`, else `origin/master`. Run `claims.py context <run-dir> --base <default>`. For uncommitted work only, pass `--base HEAD`; for staged changes only, add `--staged`; for a path, review only that path. The script writes the diff, changed files, and untracked files to `<run-dir>/context.md` so the lenses don't each rediscover them. Read it, then list the modules on the other side of each boundary the diff touches; a misplaced decision is often fixed in code the diff never opened.
- **Codebase.** The user says "the codebase" or "the repo", names a module or a pain point, or the branch has no changes. Start in the area they named. Otherwise list hot spots with `git log --since=6.months --name-only --format= | sort | uniq -c | sort -rn | head -30` and start there, because a refactor pays off where code keeps changing.

Then map the domains, the areas of the product the code is organized around, from what the repo declares rather than its folder layout: workspace or package manifests, import-rule or visibility config, a code owners file, modules' declared exports. If it declares none, use the top-level source directories, and if those don't name areas of the product, ask the user which directories are domains. Then, for each domain in scope, sort its files into layers: entry points (handlers, views, controllers, consumers, tasks), coordination (services, use cases), decisions (domain models, rules), and storage or outside systems (repositories, clients). Take the layer names from the repo's framework and most common layout, and mark files that fit no layer. Pass both maps in the scope.

Tell the user the scope and the maps' source in one line before going further, such as "Scope: branch `foo` vs `origin/main`, 12 files; 9 domains from the workspace manifest, layers from the Django app layout".

Done when you can say "branch `<name>` against `<base>`, context in `<run-dir>/context.md`, plus boundary modules `<list>`" or "codebase, starting from `<area or hot spots>`", name the domain map's source, and every file in scope has a layer or is marked as fitting none.

## 2. Run the lenses

Spawn one subagent per lens, all in parallel in one message, on a mid-tier model. Give each the prompt in `references/lens-prompt.md`, filling in only its placeholders: the scope from step 1, the absolute path of its lens file, and its output path `<run-dir>/lens-<lens>.json`, where `<lens>` is the file's suffix (`depth`, `ownership`, and so on). The lens files are for the subagents; don't read them yourself. If the harness cannot spawn subagents, run the lenses yourself one at a time with the same prompt.

| Lens | File |
|---|---|
| Depth and dead weight | `references/lens-depth.md` |
| Ownership of decisions | `references/lens-ownership.md` |
| Change locality | `references/lens-locality.md` |
| Domain model and types | `references/lens-domain.md` |
| Module boundaries and placement | `references/lens-modules.md` |
| Layers and service shape | `references/lens-layers.md` |
| Input parsing | `references/lens-parsing.md` |
| Reruns and shared writes | `references/lens-reruns.md` |
| Enforced rules | `references/lens-enforcement.md` |
| Testability | `references/lens-testability.md` |

Then run `claims.py batch <run-dir>`. It numbers every claim, groups claims that share a verdict and cite overlapping lines, and writes checker batches holding only each group's claim text and evidence. Overlapping lenses then cost one check, not several. If it reports a missing or malformed lens file, rerun that lens.

Done when the script prints the claim and group counts and the batch files.

## 3. Check every group

Spawn one checker subagent per batch file, in parallel, on a mid-tier model, with the prompt in `references/checker-prompt.md`, the batch file's path, and the output path `<run-dir>/check-<N>.json`. Add nothing else to the prompt: the batch file is all the checker should see, so it judges the code rather than the reviewer.

Then run `claims.py status <run-dir>`. It prints each group's answer and fails if any group is unanswered or an answer is malformed; respawn the checker for that batch.

Done when the status script passes.

## 4. Settle, compose, and rank

Run `claims.py findings <run-dir>`. It prints each kept group with its claims, then a "To settle" list of refuted and unresolved groups. Each group becomes a finding with the group's verdict. Join groups only when they share a verdict and propose the same move, and list every group id the finding covers. Never join groups with different verdicts, split a group, or change a verdict. Use the narrowed wording where given. If you think a verdict is wrong, add that to the finding's "Case for leaving it" line, using the definitions in `references/lens-prompt.md`. Kept `ask` groups become questions for owners, not ranked findings.

Settle each group on the "To settle" list:

- **Refuted.** Read the lines the checker cites. Drop the group if they show it is wrong. If they don't, mark it contested.
- **Unresolved.** Mark it contested.

Strength comes from the checker's confirmed cost, not the lens's stated one, less any part its confirmed case for leaving it explains:

- **Strong.** The confirmed cost shows compensating code, commits changing the same files together for this reason, two or more copies of the same decision added or edited in the last six months (code that differs for a confirmed reason is a variant, not a copy), or a doc or agent instruction file that presents dead or replaced code as current. Agents copy all of these.
- **Worth exploring.** Anything else: the confirmed cost is none, a single instance, or copies only in code nobody has touched in six months. A `defer` finding is always worth exploring, and so is any finding in code no production path reaches, whatever its cost; rank those after the finding that names the code unreachable.

Findings that are each right can still clash when applied together. `findings` ends with pairs of kept groups whose cited lines sit near each other. Label every pair:

- **Subsumes.** One move removes the other's code. Fold the smaller finding into the larger.
- **Before.** One move makes the other smaller or safer. Order them.
- **Moots.** One move may delete or relocate the code the other improves. The other waits on it.
- **Conflicts.** The moves pull the same code different ways. The user decides.
- **Independent.** They share lines, not a decision.

Findings linked by any label but independent form one change set; every other finding is a set of its own. Order each set: deletions, then types and owners, then their callers, then moves and renames, each in its own commit. A set that needs an `ask` answer waits on it.

Rank sets by their highest finding. Rank two live ways of doing one thing first, because agents copy whichever they find. Then reconstruction of another module's state, compensation for another module's output, change that spreads across files, and the rest. Within a tier, rank more recent copies and more frequently changed code higher.

The top set is the one the user is most likely to act on, so read its code yourself, end to end along every path its findings name, and weigh its cost against its case for leaving it. If the read shrinks the cost, lower the strength; if it contradicts the claim, mark it contested. Then rank again.

Done when every group id appears in exactly one finding or is dropped or contested, each drop names the code that refuted it, the top set's code has been read end to end, every overlapping pair has a label, and every finding has a verdict, a strength, and a place in exactly one ranked change set.

## 5. Report

Write the report in the reply, not a file. Open with a one-line tally ("5 findings (2 strong, 3 worth exploring), 1 question for owners, 1 contested, 4 dropped after checking"), then the top recommendation and one sentence on why it comes first. Then each change set in rank order, titled for the whole refactor, with its findings in the set's order:

- **Title** naming the move, such as "Let Orders decide duplicates" or "Collapse the three pricing wrappers".
- Verdict, strength, group ids, and claim ids, on one line.
- **Cost:** the confirmed cost the strength rests on.
- **Files:** `path:line` for each location.
- **Problem:** one sentence on what hurts.
- **Move:** the smallest safe change.
- **Wins:** concrete gains, such as "tests hit one interface" or "delete 4 one-caller wrappers".
- **Case for leaving it:** the checker's confirmed case, or "none confirmed". Never substitute your own.

Then a **Target shape** section when any finding moves, splits, or relocates code across files: the affected part of the file tree as it is and as it would be after every such finding, each change marked with its finding's title. Build it only from findings in the report, so it shows where the refactors lead, not a redesign of your own. Skip the section when no finding changes the tree.

Then a **Decisions** section: each conflict between findings, with the one you'd pick and why. Then a **Questions for owners** section: each question, the confirmed facts behind it with `path:line`, and who can answer it. Then a **Contested** section: each claim, the evidence on both sides, and which way you lean. Then **Dropped after checking**: one line each, with the refuting `path:line`. In branch scope, end with one line listing the decisions in the diff that were checked and left as they are.

Ask which change set the user wants to act on, and whether to implement it here or get a handoff prompt.

Done when the reply holds every change set, the target shape if any finding changes the tree, and every decision, question, contested claim, and drop.

## 6. Act on a pick

Only when the user picks a change set. Work through its findings in the set's order.

- **Implement here.** Pin the current behavior first with a test or a recorded output. Change the code in small steps that each keep it passing. When a decision moves across a boundary, edit and test both sides.
- **Hand off.** Fill in `references/handoff-prompt.md` for the set and print it in one code block, ready to paste into a fresh agent.

Done when the change passes its pinning test, or the handoff prompt is printed.

Reply: the report from step 5, then the implemented change or the handoff prompt for the change set the user picked.
