# Diagram checklist

Twelve pass/fail checks. The score is the number that pass, and the bar is 11. Each check comes from a rule in SKILL.md or the research behind it, so passing them means the board does what the skill promises. A failure has to name the exact place on the board. "Could be clearer" is not a failure.

1. **Title and scope.** The title names what the board answers, as a question or a "How X works" phrase. A subtitle or note gives its scope, its status, and where anything left out is shown.
2. **Right kind, one level.** The diagram kind fits the question (see `diagram-types.md`), and every box sits at the same zoom level.
3. **Legend matches.** Every color, shape, fill and line style on the board has a legend entry, and every legend entry is used.
4. **No collisions.** No arrow crosses a box, a label or another arrow, and no two arrows overlap.
5. **One reading direction.** The main path runs left to right or top to bottom, and no arrow points back against it. Shared or merged lines don't count as backward. On a parts board, the lower track's answers run right to left by design; judge only the upper track.
6. **Labeled arrows.** Every arrow that carries something has a label of 5 words or fewer, with a verb. A branch arrow may carry its condition instead ("method = UPS"). The trunk and bar of a branch tree carry nothing, so they need no label. Arrows doing the same kind of action use the same verb.
7. **Unambiguous order.** Wherever position alone doesn't show which step comes first, numbers or titles do. Each one reads in a consistent sequence, and parallel lanes count their own steps with a letter (4a, 5a and 4b), so a shorter lane simply ends sooner.
8. **Every story ends.** Each request reaches a visible reply or end state, failures included. Each state that isn't final shows what moves it on, or the subtitle says where that's shown.
9. **Shared things drawn once.** Within one diagram, a datastore, job or service that several paths share appears once, or as clearly marked parts of one thing, such as record boxes inside one store band. Separate sequence-diagram panels for separate scenarios may repeat participants.
10. **Sync and async are honest.** Solid and dashed lines match the legend's meaning for every arrow, including writes and callbacks.
11. **Risk marked.** A known gap from the source is shown in red, next to what it's about, with a legend entry, and red means nothing else. The filled branch point is the board's focal element, not a risk accent. Pass if the source names no gap.
12. **Readable when shared.** No text is clipped, cut off at an edge, or overlapped. Captions and notes are at least the default label size.

## Running it

Spawn a fresh subagent on a mid-tier model with the Whimsical `fetch` tool, and give it only the board id, the source the board was drawn from, and this file's checks. Never add explanations, design reasons or rebuttals of an earlier verdict. A checker that has been told why a choice is fine stops checking it, and in testing that inflated self-scores by 3 to 6 points. When you think a FAIL is wrong, fix the board's wording so a fresh checker reads it correctly. It fetches the board as an image and answers each check PASS or FAIL. Every FAIL comes with the exact spot and the smallest fix. It ends with the count, such as "Checklist: 10/12".

It judges only these twelve checks. Taste outside them doesn't move the score.
