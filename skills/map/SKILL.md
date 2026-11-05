---
name: map
description: >-
  Map a codebase's architecture, starting with its services, datastores, queues,
  and outside systems and how they connect, then zooming into one service's
  components or one code path on request. Every box and arrow is cited and
  checked, and each level is saved to a local .map/ folder so later sessions
  reuse it. Use for "map", "map this repo", "more detail on X", "refresh the
  map". Use how to trace one flow.
disable-model-invocation: true
---

# Map

You own a map the user can trust while reading unfamiliar code. A smaller map with its gaps named beats a complete one with an invented arrow.

## Levels

| Level | Boxes | Arrows |
|---|---|---|
| 1. Services (default) | Deployable services, datastores, queues, and outside systems | Network calls and messages |
| 2. Components | The modules or classes inside one service that others call | Calls between them |
| 3. Path | One call chain inside one component, step by step | The order of calls |

The map file is `.map/map.json` at the repo root. Its fields, what counts as each kind of box, and a worked example are in `references/map-format.md`; read it before writing the file. `scripts/map_file.py` in this skill's directory checks, stamps, diffs, and merges into that file, and each stamp or merge also rewrites `.map/map.html`, a browser view of the whole map; run it, don't read it.

## 1. Load and scope

If `.map/map.json` exists, run `map_file.py stale <repo-root> .map/map.json`. Then pick one:

- **No target, map exists:** show the saved level 1 from the file, with a line naming each stale node and its changed files. Rebuild nothing until the user says "refresh", but run step 4 for whatever is not built yet.
- **No target, no map:** build level 1.
- **"More detail on X":** if X's children are in the file, show them, verifying them first if any is `"verified": false`, then run step 4 for them. If a background subagent is still building X, wait for it. Otherwise build one level below X, on X only. With no map yet, build level 1 first, so X has a node to hang from.
- **"Refresh":** rebuild the stale nodes, or the named ones, at their level.
- **A feature across several repos,** such as "map the checkout feature across these repos": the root is the folder holding those repos, and citations start there, such as `api/app/checkout.rb:12`. Take the feature's code from the docs that describe it, such as the agent instructions and design docs in the folder the user is in, and map only that code. The map goes in that folder's `.map/`. In the steps below, `<repo-root>` means that root; `stamp` records it, and later runs read it from the map.
- **"Build ahead":** run step 4 only, then reply with one line naming what started. Use it to resume background mapping that stopped.

Done when you can say `level N, covering <whole repo | node X>, from <file | fresh build>`.

## 2. Gather

Read code, configs, and schemas. Never run the code, its tests, or a build.

For level 1, inventory from deploy files first: compose files, Kubernetes manifests, Terraform, Procfiles, serverless configs, and build targets. In a monorepo they decide where one service ends, not the folder layout. Then find each connection.

- **One service, or a repo with three or fewer:** explore it yourself.
- **More:** split into 2 to 4 slices, one per service or group of services, and spawn one read-only subagent per slice in parallel on a mid-tier model, with the prompt in `references/explorer-prompt.md`. Fill `{KNOWN_NOTES}` with the findings and unknowns already on the slice's boxes, the boxes above them, and the boxes inside them.

The rules in that prompt bind you too: follow the wiring, not the names; record each arrow's evidence kind; put runtime-only wiring under Unknowns; stay at the level.

If a level would pass 20 boxes, group related services into `group` nodes and map their members one level down.

Done when every box has a citation and a role, every arrow has an evidence kind and a citation or is marked inferred, and every gap is an unknown.

## 3. Write and check

Write a first level 1 straight into `.map/map.json`, with the top-level `summary`. Write anything deeper, or a rebuild, as a fragment, `{ "parent": <node id>, "nodes", "edges", "findings", "unknowns", "paths" }` in `.map/fragments/<parent>.json`, and add it with `map_file.py merge <repo-root> .map/map.json <fragment>`, which swaps out that node's old children under a lock, checks the result, and stamps it. Before writing, count: each role is 70 characters or fewer and each arrow label 24 or fewer, with no file names in roles; `merge` refuses anything longer. Edit a fragment with the file-edit tool, not shell text substitution, which breaks on JSON. On first write, create `.map/.gitignore` containing `*` so the folder stays out of git without touching the repo's own ignore file. Write nothing outside `.map/`.

1. Run `map_file.py check <repo-root> .map/map.json`, or `merge` for a fragment, and fix every problem. A restated finding is dropped or folded into the one it repeats, never reworded to pass.
2. Spawn one read-only subagent on a mid-tier model with the prompt in `references/verifier-prompt.md` and only the new entries. For each entry it flags, correct it from the code, mark the edge inferred, move it to unknowns, move a misfiled unknown to findings, or drop a restated note.
3. Run `check` and then `map_file.py stamp <repo-root> .map/map.json`, or `merge` the corrected fragment again.

Done when the last `check` prints `OK` and the file is stamped, or the last `merge` succeeded.

## 4. Build ahead in the background

Every level is saved, so building ahead is a one-time cost per repo, and it makes each later drill-in instant. Keep the map one level ahead of the deepest level built, down to level 3:

1. **Queue.** After any level is built or merged, run `map_file.py queue <repo-root> .map/map.json`. It prints `build <id>` for each box to build, most findings and arrows first, and `skip <id>` for small leaf components whose citation already says everything. Merge an empty fragment for each skipped box so it is marked loaded. Every kind has a level under it: a `service` or `group` its components, a `component` its call paths, a `datastore` its tables or collections and who reads and writes each, and a `queue` its queues or topics and who publishes and consumes each.
2. **Run.** Keep at most six background subagents running at once, each on a mid-tier model with the prompt in `references/background-prompt.md`, its `{KNOWN_NOTES}` filled as in step 2. Don't wait for them: send the reply now.
3. **Check and continue.** When one reports back, run step 3's verifier on its fragment, set `"verified": true` on the entries that hold up, merge the fragment again, queue the new boxes it added, and start the next queued build. When one finds nothing under its box, such as an outside system with no code in the repo, merge a fragment with no nodes, so the box is marked loaded and never queued again. When one cannot finish, do the same with one unknown naming where it stopped.

Each fragment arrives with `"verified": false` on its nodes. Where the harness cannot run a subagent in the background, skip this step. Where it does not report back when one finishes, the first six still land and the rest wait for the next "build ahead".

Done when the queue is empty, and each spawned subagent has merged its fragment or reported why it could not.

## Reply

Answer from the file, at the scoped level:

- **Overview:** the map's `summary`, or the scoped box's role. If the target was ambiguous, one line naming what you picked.
- **Key findings:** up to three, bugs first, one line each with its severity first and the citation at the end.
- **Diagram:** plain-text boxes and arrows in a code block, one per level shown, as in the worked example. Mark inferred arrows with a dotted line (`··▶`). Draw the main path left to right and keep lines from crossing; an arrow that would cross goes in the Boxes list instead, under the box it leaves.
- **Boxes:** one line each: name, role, citation.
- **Unknowns:** one line each.
- **Stale:** when shown from the file, which nodes changed since `built_at_commit`.
- **Next:** one line naming what the user can drill into, such as `more detail on API`, and what is being mapped in the background. Mention `.map/map.html` for the full diagram in a browser.

Say nothing about the checks when they passed.
