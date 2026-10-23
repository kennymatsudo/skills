---
name: writing-style
description: >-
  The house style for prose a person reads later: docs, READMEs, guides,
  design records, plans, PR and commit text, and reports. Covers opening with
  the reader's problem, structure, headings, naming and defining terms,
  describing behavior instead of virtue, sentences, and punctuation. Load it
  before writing or editing such prose, or when another skill names it. Use
  for "follow our writing style", "write this doc in our style", "how should
  this README read". Skip chat replies and code comments. Use unslop to clean
  up a document that already exists.
---

# Writing style

You own prose that a reader who wasn't there understands on one read and acts on correctly.

Apply each section while drafting, then once more as a pass over the draft. Where a project's own instructions name its terms or formats, follow them over the general rule here.

## 1. Name the reader and the doc's job

State who reads this and what they need from it: a reference for how things are now, a plan, a decision record, a status log, a PR description, a how-to, a report. The job decides what belongs. Decision records, changelogs, status timelines, archives, and PR and commit text describe a change or keep history; every other doc describes the present.

Write for someone new to the project unless the job says otherwise. A report is read by people who didn't do the work, so describe results by what a user would notice, not by what the code did.

Done when you can say in one sentence who reads it and what they will do with it.

## 2. Structure

- **Point first.** The opening lines give the reader what they came for: the answer, the current state, the decision, or what to do. A README or guide opens with the situation the reader is in, the moment the tool is for, and only then says what the tool does. Move status banners, provenance, and setup behind the point, or cut them. Open each section with its own point too, so a reader who drifts off can restart at any heading.
- **Current truth only.** In a doc about the present, delete history: "previously", "no longer", "was X, now Y", "originally", "Corrected on (date)", "as of (date)", struck-through resolved items, and lists of what a change removed. State the current fact. When the history carries a reason the reader needs, keep it as a present-tense sentence ("X, because Y"). The history stays in git.
- **No meta commentary.** Cut text about the document instead of the subject: "This document covers...", tours of the doc's own structure, notes telling the next agent how to refresh the file, audience and reliability disclaimers, "Related reading" tours, "I found...", reassurance, and notes on which drafts were used.
- **Say it once.** Cut a TL;DR, summary, or conclusion that repeats the body, an intro that restates its heading, and a bold label that repeats the line it starts. Keep one summary at the top of a long doc.
- **Short paragraphs.** One idea each, one to three sentences.
- **Lists for parallel items only.** A chain of reasoning stays prose, because bullets drop the words that join it. A bullet that runs past two sentences is a paragraph. Nest at most one level. Steps that happen in order get numbers; nothing else does.
- **Tables and diagrams.** Table cells hold a word, number, or phrase; a cell holding sentences means the row is prose. Draw a diagram when it tells a story better than a paragraph.
- **One job per doc.** A doc that serves several readers or jobs (a plan with a status log and an onboarding guide inside it) gets split.
- **Messages end on the decision.** A reader skims a long message and approves it unread. Keep a message or report that asks for something short, and put the one decision on its last line.

Done when the opening answers the reader's question and every paragraph, list, table, and message passes the rules above.

## 3. Headings

A heading tells a scanning reader what the section says. Test each one: could it head a section in an unrelated doc? If so, rewrite it to name this section's content.

- **Name the content.** "Context" becomes "Why checkout retries twice". A task section starts with a bare verb ("Configure the cache"); a concept section is a noun phrase ("Retry budget").
- **Answer in the heading.** "Why SSE?" becomes "SSE was too slow for mobile".
- **No template, filler, or cute headings:** Overview, Background, Summary, Notes, Key takeaways, Why this matters, Conclusion, "Gotchas", "The secret sauce".
- **No colon subtitles, process headings, emoji, or numbers on sections that have no order.**
- **Earn the heading.** Merge a section of one or two lines into its neighbor. A doc that fits on one screen needs no headings. Never skip a level. Use sentence case.

Done when no heading could sit unchanged in an unrelated doc.

## 4. Terms

- **Define a term where the reader first meets it,** in a few words, even if a glossary has it.
- **One name per thing,** the same in every doc, skill, and tool in the project. Elegant variation (cycling synonyms to avoid repeating a word) makes the reader wonder whether two names mean two things.
- **Keep analogies out of names.** An analogy (a test bench, a notebook) can introduce and group ideas. The names are the terms the code, commands, and rules use. Never put an analogy word in a command, a file name, or a rule.
- **Plain words over jargon.** Keep the domain terms the reader's team uses. Replace metaphor jargon (substrate, north star, flywheel, surface, wedge) with the literal word.
- **Leave out what the reader would assume** without being told.

Done when every term a newcomer wouldn't know is defined at first use, and each thing has one name.

## 5. Sentences

Most moves below belong to one register, performed plainness: plain language overdone until it becomes ornament. Its marks are short declaratives in a row, moral adverbs, clauses that drop their objects, and aphoristic endings. It reads as copy, and readers recognize it as model-written. Fix the move wherever it appears; the examples show its shape.

- **Virtue claims.** Say what the tool does: "tells you which behaviors it couldn't test." Adverbs of manner ("plainly", "honestly", "transparently", "never hidden") claim candor instead of showing it, and readers discount self-described honesty.
- **Dropped objects.** A verb that leans on an object several clauses back ("prove it, and tell you when they can't") makes the reader reconstruct it. Restate the object: "when they can't prove it".
- **Slogans.** Antithesis ("prove X, and say when you can't"), aphorisms, fragments for effect, and tidy codas. Write the lumpier literal sentence. A slogan standing in for a rule becomes the rule with its object attached: "never a pass" becomes "a check that never failed on a planned break can't mark a behavior Verified".
- **Personified tools.** Tools don't say, want, know, or believe. They print, report, return, and tell you. The same goes for figurative verbs ("the cache remembers").
- **Puffery.** "pivotal", "a testament to", "plays a crucial role", trailing "-ing" clauses that add significance ("..., highlighting the need for..."). Say what happened or cut it.
- **False contrast.** "Not just X, but Y", "It's not X, it's Y", "rather than simply". State Y. Keep the contrast only when the reader would otherwise believe X.
- **Missing agent.** "The decision emerged", "queries are validated". Name who or what acts.
- **Portable sentences.** A sentence that could sit unchanged in another project's docs ("keeps the database close at hand") says nothing about this one. Replace it with the mechanism or a number, or cut it.
- **Throat-clearing and hedging.** "This can help you...", "I hope this helps", "It is important to note that", "In order to" (use "to"), "could potentially" (use "may"). Name real uncertainty once.
- **Dressed-up verbs.** "serves as" is "is"; "utilize" and "leverage" are "use"; "facilitate" is "help".
- **Telegraphese.** Arrows, dropped articles, and private abbreviations. Write whole sentences.
- **Tricolons and false ranges.** Groups of three that aren't naturally three; "from X to Y" where X and Y aren't the ends of a scale.

Done when no sentence matches a move above.

## 6. Punctuation and emphasis

- No em dashes; use a comma or a period. Use a colon only before a list or example.
- Bold only a lead-in or the one decisive detail, never whole sentences or every term.
- Straight quotes. No decorative emoji.

Done when the draft has no em dash, curly quote, or bolded sentence.

## Guardrails

- Never invent a fact, number, reason, or example to satisfy a rule. Where you lack the specific, cut the vague sentence or ask.

**Reply:** the written text. If a rule couldn't be met for lack of a fact, name the gap in one line.
