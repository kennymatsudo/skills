# Verifier prompt

Pass the text below as the subagent's prompt, with the new entries filled in.

---

You are checking new entries in an architecture map before a user relies on it. Assume they contain mistakes and find them. Read only; never run the code or its tests.

## New entries

{ENTRIES}

## Check every entry

Open the cited lines for each node, edge, finding, and path step, and decide:

- **Supported:** the lines show what the entry says.
- **Wrong:** the lines show something different. Say what they actually show.
- **Unsupported:** the lines exist but do not establish the entry, such as an edge inferred from a matching name, or a "service" that is only a folder with no deploy entry.
- **Wrong evidence kind:** the edge is real but was confirmed some other way than its `evidence` field says.
- **Misfiled:** an unknown that names a problem the code shows (a finding), or a finding that only describes how the code works today (drop it).
- **Wrong severity:** a finding marked `bug` that only fails under retries or concurrency (`risk`), or the reverse.

## Output

List only the entries that are not supported: the entry, the verdict, and what the code actually shows, with `path:line`.

If every entry is supported, reply `All entries supported.`
