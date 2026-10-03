# Prose

Work top-down. Structure costs the reader more than word choice, so fix it first; a word-level pass over a badly shaped doc leaves a tidier wall of text.

## 1. Name the reader and the doc's job

State who reads this and what they need from it: a reference for how things are now, a plan, a decision record, a status log, a PR description, a how-to. The job decides what belongs. Decision records, changelogs, status timelines, and archives exist to keep history; every other doc describes the present.

## 2. Structure

- **Point first.** The opening lines give the reader what they came for: the answer, the current state, the decision, or what to do. Move status banners, provenance, and setup behind it, or cut them. Open each section with its own point too, so a reader who drifts off can restart at any heading.
- **Current truth only.** In a doc about the present, delete history: "previously", "no longer", "was X, now Y", "originally", "Corrected on (date)", "As built (updated ...)", "as of (date)", struck-through resolved items, and lists of what a change removed. State the current fact plainly. When the history carries a reason the reader needs, keep it as a present-tense sentence ("X, because Y"). Git keeps the rest.
- **No meta commentary.** Cut text about the document instead of the subject: "This document covers...", "This section explains...", tours of the doc's own structure, notes telling the next agent how to refresh the file, audience disclaimers, reliability disclaimers ("holds unless implementation proves otherwise", "check the code before assuming this landed"), "Related reading" tours of other docs, "I found...", reassurance, and notes on which drafts were or weren't used. A real maintenance rule belongs in the repo's agent instructions or a script; flag it in the reply.
- **Say it once.** Cut a TL;DR, summary, or conclusion that repeats the body, an intro that restates its heading, and a bold label that repeats the line it starts. Keep one summary at the top of a long doc.
- **Short paragraphs.** One idea each, one to three sentences. Split a paragraph the reader has to reread.
- **Lists for parallel items only.** Prose that is a chain of reasoning stays prose, because bullets drop the words that join it. A bullet that runs past two sentences is a paragraph; make it one. Nest at most one level. Steps that happen in order get numbers; nothing else does.
- **Tables for short comparisons.** Cells hold a word, number, or phrase. A cell holding sentences means the row is prose; rewrite it as a paragraph or a list.
- **One job per doc.** When a doc serves several readers or jobs (a plan with a status log and an onboarding guide inside it), flag the split in the reply. Don't split it unasked.

## 3. Headings

A heading tells a scanning reader what the section says. Test each one: could it head a section in an unrelated doc? If so, rewrite it to name this section's content.

- **Name the content.** "Context" becomes "Why checkout retries twice". "Notes" becomes what the notes are about. A task section starts with a bare verb ("Configure the cache"); a concept section is a noun phrase ("Retry budget").
- **State the answer, not the question.** "Why SSE?" becomes "SSE was too slow for mobile". A question heading followed by bold "Decision:" and "Rationale:" labels becomes one heading and plain prose.
- **No template or filler headings:** Overview, Background, Summary, Notes, Key takeaways, Key points, Why this matters, The bottom line, Conclusion, Next steps with nothing specific under it.
- **No cute or slang headings:** "Gotchas", "Known traps", "The secret sauce", "Four traps that have each cost real time". Name the trap instead ("Tokens expire after 15 minutes").
- **No colon subtitles** ("Caching: A Deep Dive", "Unsettled: target date"), process headings ("Source note", "Authority order"), emoji, or numbers on sections that have no order.
- **Earn the heading.** Merge a section of one or two lines into its neighbor. A doc that fits on one screen needs no headings. Never skip a level.
- **Sentence case.**

## 4. Sentences

Fix the move wherever it appears; the examples show its shape.

- **Inflated importance.** "pivotal", "a testament to", "plays a crucial role", trailing "-ing" clauses that add significance ("..., highlighting the need for..."). Say what happened or cut it.
- **Contrast framing.** "Not just X, but Y", "It's not X, it's Y", "more than an X", "rather than simply". State Y. Keep a contrast only when the reader would otherwise believe X.
- **Agentless voice.** "The decision emerged", "queries are validated". Name who or what acts.
- **Feeling instead of mechanism.** "Keeps the database close at hand" becomes the mechanism or a number. If a sentence could appear unchanged in another project's docs, it says nothing about this one; cut it.
- **Helpful boilerplate and chatbot tone.** "This can help you...", "Great question", "I hope this helps", "Let me know if". Cut.
- **Filler and hedging.** "In order to" becomes "to", "It is important to note that" goes, "could potentially" becomes "may". Name real uncertainty once, plainly.
- **Fancy words.** "serves as" becomes "is", "utilize" and "leverage" become "use", "facilitate" becomes "help". Replace metaphor jargon (substrate, north star, flywheel, surface, wedge) with the literal word.
- **Mannered prose.** Aphorisms, fragments for effect, personified code, figurative verbs ("the announcement has invited an audience"). Write the literal phrase.
- **Over-compression.** Arrows, dropped articles, and private abbreviations. Write whole sentences.
- **Forced patterns.** Groups of three that aren't naturally three; cycling synonyms for one thing (pick a name and repeat it); "from X to Y" where X and Y aren't ends of a scale.

## 5. Punctuation and emphasis

- No em dashes; use a comma or a period. Use a colon only before a list or example.
- Bold only a lead-in or the one decisive detail, never whole sentences or every term.
- Straight quotes. No decorative emoji.

## Don't overcorrect

- Keep every fact, number, link, command, condition, and caveat about the subject that the reader needs.
- Keep the connectives ("because", "but", "unless", "which means"). They carry how the facts relate, and the verifier checks facts, not links.
- Keep domain terms the reader's codebase or team uses.
- Keep the author's voice where it is plain already. Change what's broken, not what's merely different from how you would write it.
