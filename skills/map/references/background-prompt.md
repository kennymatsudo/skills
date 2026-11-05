# Background prompt

Fill in the placeholders and pass the text below as the subagent's prompt. `{LEVEL}` is the box's level plus one.

---

You are mapping one box of a codebase's architecture map one level deeper, in the background. The user is reading the map now and may click into this box later, so your work must be ready and correct by then. Nobody will answer questions; when the code points somewhere you cannot follow, record it as an unknown.

Read only, except for the two files named below. Never run the code, its tests, or a build.

## Your box

{BOX_NAME} (node id `{BOX_ID}`, a {BOX_KIND}), defined at {BOX_CITES}. Build level {LEVEL} under it.

## Already on the map

Findings and unknowns recorded for this box, the boxes above it, and its siblings. Do not restate them, even in other words; `merge` rejects a restatement:

{KNOWN_NOTES}

## Steps

1. Read `{EXPLORER_PROMPT}` and follow its rules and "What to find" for this box at level {LEVEL}. Its "Already on the map" is the section above.
2. Read `{MAP_FORMAT}` for the field names, what counts as each kind of box, and what belongs under findings versus unknowns.
3. Write `{MAP_DIR}/fragments/{BOX_ID}.json`: `{ "parent": "{BOX_ID}", "nodes", "edges", "findings", "unknowns", "paths" }`.
   - **A service or group:** up to 12 nodes, each with `"level": {LEVEL}`, `"parent": "{BOX_ID}"`, `"kind": "component"`, and `"verified": false`. Edges join two of your components. Name a call out of the service in the calling component's summary, such as "charges cards through Stripe". A component may cite several files; group files that do one job together into one box rather than one box per file.
   - **A datastore:** one `component` node per table or collection, from the schema or migrations, its summary saying what it holds and which boxes on the map read and write it, by box name, not file.
   - **A queue:** one `component` node per queue or topic, its summary naming which boxes publish to it and consume it. When the box is itself a single topic, its children are its consumer groups, not the topic again.
   - **A component:** no nodes. Up to three `paths` with `"node": "{BOX_ID}"`: the main call chains that start in this component, one step per call, each step cited. Add a finding only for a defect a step shows that the notes above do not cover.
   Before writing, count: each role is 70 characters or fewer and each arrow label 24 or fewer, with no file names in roles; `merge` refuses anything longer. Edit a fragment with the file-edit tool, not shell text substitution, which breaks on JSON.
4. Run `python3 {MAP_FILE_PY} merge {REPO_ROOT} {MAP_DIR}/map.json {MAP_DIR}/fragments/{BOX_ID}.json`. It prints each problem and refuses to merge until there are none. Fix the fragment and rerun until it prints `Merged`.

## Output

One line: `merged N components under {BOX_ID}` or `merged N paths under {BOX_ID}`, or what stopped you. Then your findings and unknowns, one line each with citations.
