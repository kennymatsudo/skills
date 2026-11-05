# Explorer prompt

Fill in the placeholders and pass the text below as the subagent's prompt.

---

You are gathering facts for an architecture map of one slice of a codebase. Another agent writes the map from your findings, so favor accuracy over prose. Other explorers cover the other slices; stay on yours.

Read only. Never run the code, its tests, or a build.

## Level

{LEVEL}: {LEVEL_DESCRIPTION}

## Your slice

{SLICE}

## Already on the map

{KNOWN_NODES}

Findings and unknowns already recorded for your slice, the boxes above it, and the boxes inside it. Do not restate them, even in other words:

{KNOWN_NOTES}

## What to find

1. **Boxes.** Each service, datastore, queue, external system, or component in your slice: its name, its role in 70 characters or fewer, its framework or product if it has one, and where it is defined or deployed. Follow `{MAP_FORMAT}`'s "What counts as what" for which code earns a box.
2. **Connections.** Each call or message from your slice to any box, on the map or new: what crosses, in a few words, and the wiring that proves it.
3. **Findings.** Up to three new defects, each `bug`, `risk`, or `gap` as `{MAP_FORMAT}` defines them, such as a path that never completes, a call made inside a transaction, or a race. None is fine. Put each on the box whose code shows it.
4. **Unknowns.** Questions the repo cannot answer, such as a host set by an env var nothing in the repo sets, with the file where you stopped. If the answer is in a file you have not read, read it instead.

Rules:

- **Follow the wiring, not the names.** A connection counts only when you find the client call, route registration, queue topic, or config that joins both sides. Name which of those it was. A matching name is a guess; report it as inferred.
- **Runtime-only wiring is an unknown.** Hosts read from env vars nothing in the repo sets, service discovery by name, and flags decided at runtime go under Unknowns, with where you stopped.
- **Stay at the level.** Validation rules, field names, and branches inside one component belong to a deeper level. Leave them out.

Cite every fact as `path/to/file.ext:LINE` or `path/to/file.ext:START-END` from the repo root.

## Output

- **Boxes:** name, kind, role, framework or product, citation.
- **Connections:** from, to, what crosses, evidence kind (`config`, `client-call`, `route`, `topic`, or `inferred`), citation.
- **Findings:** box, severity, text, citation.
- **Unknowns:** what, and where you stopped.
