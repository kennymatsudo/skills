# Research subagent

Spawn one subagent on a mid-tier model with web search and fetch. Fill in the bracketed parts of this prompt:

> Research how practitioners approach [the job the skill does], to inform an agent skill that [one-sentence summary of the planned or source approach]. Use web search and fetch.
>
> Find substantive sources: practitioner essays, forum and issue threads with real discussion, official docs, and research papers. Skip SEO listicles.
>
> Report in under 700 words:
> 1. Ranked recurring themes, each with 1-3 URLs.
> 2. Gaps: what the approach above misses that sources recommend.
> 3. Contested points where sources disagree.
> 4. Anything that would make the work cheaper or faster without losing accuracy, with the evidence for it.
>
> Label anything you could not verify (couldn't fetch, secondhand, or inferred) as UNVERIFIED.

When relaying, keep it to the findings that change the draft, and carry the UNVERIFIED labels through.
