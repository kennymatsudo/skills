# Guidance subagent

Spawn one subagent on a mid-tier model with web search and fetch. Fill in the bracketed parts:

> Today is [today's date]. Find the current guidance for writing agent instruction files ([the file names in scope, e.g. AGENTS.md, CLAUDE.md]) read by [the harnesses that load them], and the prompting guidance for each vendor's newest model as of today. Use web search and fetch. Take model names from what the sources say today, never from memory.
>
> 1. **Find the newest models.** For each vendor whose harness reads these files, fetch its prompting guide index and pick the newest model it lists. Then fetch that model's own prompting or migration page, especially any section on prompts written for earlier models.
> 2. **Fetch the instruction-file docs.** Fetch each harness's own page on how it loads these files: size limits, imports, nesting, and what to put in them.
> 3. **Search for anything newer.** Search for "[file name] best practices [month year]" and "[vendor] prompting guide [newest model]". Read practitioner posts and studies only when they add a point the official docs lack.
>
> Starting points, current when this prompt was written. If one moved, search for its replacement:
>
> - Anthropic: `platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices` (lists current models and links to each), `code.claude.com/docs/en/memory`, `code.claude.com/docs/en/best-practices`, and the index `code.claude.com/llms.txt`.
> - OpenAI: `developers.openai.com/api/docs/guides/prompt-guidance`, the Codex AGENTS.md page (search "Codex AGENTS.md"), and the index `developers.openai.com/api/llms.txt`.
> - Shared format: `agents.md`. Cursor: `cursor.com/docs/context/rules`.
>
> Use the indexes to find pages rather than crawling. Fetch only what answers the questions below.
>
> Report in under 600 words:
>
> 1. **Newest models**, one line per vendor, with the page that names it.
> 2. **Rules for the file**, ranked, each one line with its URL and the source's date. Cover size, what to include, what to leave out, emphasis and tone, absolutes, explaining why, and structure (routing to other files, nesting).
> 3. **Scaffolding to remove**, which kinds of lines the newest models' guides say were for older models.
> 4. **Loading mechanics**: how each harness finds the file, follows imports, and handles nested files, so a rewrite doesn't break them.
> 5. **Contested points** where sources disagree, with both sides.
>
> For a page with no publication date, give its "last updated" line, a changelog entry, or the newest model it names, and say which you used.
>
> Label anything you couldn't fetch, found only secondhand, or inferred as UNVERIFIED.
