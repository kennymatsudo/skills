# Reviewer subagents

Spawn two subagents in parallel on a mid-tier model, each with the Whimsical MCP's `fetch` tool. Neither gets your plan, your reasoning, or this skill. Each sees only the board and what the reader would know, so its read isn't anchored on yours.

## Clarity reviewer

Fill in the bracketed parts:

> You are seeing a diagram for the first time. Fetch Whimsical board [board id] as an image (`fetch` with `image: true`). Its intended reader is [audience]. Read it the way that reader would.
>
> 1. In two or three sentences, say what the diagram tells you. Use only what is on the board.
> 2. Say where your eye went first and in what order it moved. Name each place where you had to search, backtrack, or guess.
> 3. List each layout defect with the boxes or labels it involves: arrows that cross or overlap, arrows pointing against the reading direction, clipped or covering labels, misaligned lanes, crowded or empty areas.
> 4. List anything the legend doesn't explain.
>
> Report in under 250 words. Don't suggest a redesign. Report what you saw.

## Accuracy reviewer

> Check a diagram against its source. Fetch Whimsical board [board id] as an image (`fetch` with `image: true`), then read [source: file paths, or the pasted design notes]. The diagram is meant to answer: [question].
>
> 1. List each box and arrow that the source contradicts or doesn't support, with the line in the source.
> 2. List each component, step, or failure path that the source treats as important and the diagram leaves out.
> 3. Check each arrow's style: solid means the caller waits for the answer, and dotted means it doesn't (a webhook, queued job, poll, or scheduled run). List any that are wrong.
> 4. Say whether this is the right kind of diagram for the question. If a sequence, state, or ER diagram would answer it better, say which and why in one sentence.
>
> Report in under 250 words. Cite the source for every claim.

## Using the reports

Judge each finding yourself and act only on what you can confirm in the snapshot or the source. A reviewer's misreading of a correct diagram counts as a clarity defect when the reader would make the same mistake.
