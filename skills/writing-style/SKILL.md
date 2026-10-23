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

You own prose that a reader who wasn't there understands on one read and acts on correctly. Apply each section while drafting, then once more as a pass over the draft. A project's own instructions on terms or formats win over the rules here.

## 1. Name the reader and the doc's job

State who reads this and what they need from it: a reference for how things are now, a plan, a decision record, a status log, a PR description, a how-to, a report. The job decides what belongs. Decision records, changelogs, status logs, archives, and PR and commit text describe a change or keep history; every other doc describes the present. Write for someone new to the project unless the job says otherwise. A report is read by people who didn't do the work, so describe results by what a user would notice, not by what the code did.

Done when you can say in one sentence who reads it and what they will do with it.

## 2. Structure

- **Point first.** Open with what the reader came for: the answer, the current state, the decision, or what to do. A README or guide opens with the situation the reader is in, then says what the tool does. Status banners, provenance, and setup go behind the point or get cut. Each section opens with its own point, so a reader can restart at any heading.
- **Subject, present tense, once.** Every sentence is about the subject as it is now, said one time. That cuts four kinds of text. History in a doc about the present ("previously", "no longer", "originally", "was X, now Y", "Corrected on (date)", struck-through items, what a change removed): git keeps it, and a reason the reader needs becomes "X, because Y". Text about the document itself (what it covers, tours of its structure or of related reading, how to refresh it, which drafts were used, audience and reliability disclaimers, "I found...", reassurance). Repeats (a TL;DR, summary, or conclusion that restates the body, an intro that restates its heading, a bold label that repeats its line); one summary at the top of a long doc is fine. And anything the reader would assume without being told.
- **Paragraphs, lists, tables.** A paragraph is one idea in one to three sentences. Lists hold parallel items only, numbered only when the steps have an order, nested at most one level; a chain of reasoning stays prose because bullets drop the joining words, and a bullet past two sentences is a paragraph. Table cells hold a word, number, or phrase; a cell of sentences means the row is prose. Draw a diagram when it tells the story better than a paragraph.
- **One job per doc.** A doc serving several readers or jobs (a plan with a status log and an onboarding guide inside it) gets split.
- **Messages end on the decision.** A reader skims a long message and approves it unread. Keep a message or report that asks for something short, with the one decision on its last line.

Done when the opening answers the reader's question and every paragraph, list, table, and message passes the rules above.

## 3. Headings

A heading names what this section says, so it could not head a section in an unrelated doc. A task starts with a bare verb ("Configure the cache"), a concept is a noun phrase ("Retry budget"), a question becomes its answer ("SSE was too slow for mobile"), and "Context" becomes "Why checkout retries twice". That rules out Overview, Background, Summary, Notes, Key takeaways, Why this matters, Conclusion, cute headings ("Gotchas", "The secret sauce"), colon subtitles, process headings, emoji, and numbers on sections with no order.

Earn each heading: merge a section of one or two lines into its neighbor, and a doc that fits on one screen has none. Never skip a level. Sentence case.

Done when no heading could sit unchanged in an unrelated doc.

## 4. Terms

- **Define a term where the reader first meets it,** in a few words, even if a glossary has it, with "is", not "refers to": a word refers, a thing is. Coin a name only for a thing the doc returns to.
- **One name per thing** across every doc, skill, and tool in the project. Cycled synonyms make the reader wonder whether two names mean two things.
- **Analogies introduce ideas; names are the words the code, commands, and rules use.** Never put an analogy word in a command, a file name, or a rule.
- **Keep the team's domain terms.** Replace metaphor jargon (substrate, north star, flywheel, surface, wedge) with the literal word.

Done when every term a newcomer wouldn't know is defined at first use, and each thing has one name.

## 5. Sentences

Every sentence states something checkable about this subject, with its actor and its object in it, in plain words. Model-written prose fails this in one recognizable register, performed plainness: plain language overdone until it becomes ornament, which readers recognize as copy. The moves below are its shapes. Fix the move in any wording; each model generation swaps old tells for new ones.

- **Claims in place of facts.** Virtue adverbs ("plainly", "honestly", "transparently"), puffery and intensifiers ("pivotal", "a testament to", "plays a crucial role", "genuinely", "fundamentally", "deeply"), trailing "-ing" clauses that add significance ("..., highlighting the need for..."), and sentences that could sit in another project's docs ("keeps the database close at hand"). Say what the thing does ("tells you which behaviors it couldn't test"), with the mechanism or a number, or cut it. Readers discount self-described honesty.
- **Rhetoric in place of the rule.** Contrast ("not just X, but Y", "Y rather than X", "should not be confused with", "not because X": state Y, unless the reader would otherwise believe X), tricolons that aren't naturally three, false ranges ("from X to Y" where X and Y aren't the ends of a scale), fragments for effect, aphorisms, tidy codas, and a question or teaser that sets up the answer ("Why does this matter?", "Here's the catch:"). Write the lumpier literal sentence. A slogan standing in for a rule becomes the rule with its object attached: "never a pass" becomes "a check that never failed on a planned break can't mark a behavior Verified".
- **Missing actor or object.** Agentless verbs ("queries are validated", "the decision emerged"), unsourced claims ("experts say", "widely used"), personified or figurative tools (tools print, report, and return; they don't say, want, know, or remember), and a verb leaning on an object several clauses back ("prove it, and tell you when they can't" becomes "when they can't prove it"). Name who acts, who says so, and what is acted on; where no one does, cut the claim.
- **Dressed-up or clipped words.** "serves as" is "is"; "utilize" and "leverage" are "use"; "facilitate" is "help"; "in order to" is "to"; "could potentially" is "may". Cut "it is important to note", "this can help you", "I hope this helps", and name real uncertainty once. Arrows, dropped articles, and private abbreviations become whole sentences.

Done when no sentence matches a move above.

## 6. Punctuation and emphasis

- No em dashes. Where one joined two thoughts, write the joining word ("because", "which", "so") or split the sentence; a short aside goes in parentheses. Use a colon only before a list or example.
- Bold only the one decisive detail, or the lead-in of each item in a reference list the reader scans by key. A short list of claims with a bolded label and colon on every item reads as a key-takeaways box; write those as sentences. Never bold whole sentences or every term.
- Straight quotes. No decorative emoji.

Done when the draft has no em dash, curly quote, or bolded sentence.

## Guardrails

- Never invent a fact, number, reason, or example to satisfy a rule. Where you lack the specific, cut the vague sentence or ask.
- Never add opinion, first person, jokes, or asides to sound human. Plain formal prose is not a tell, and a performed personality is one.

**Reply:** the written text. If a rule couldn't be met for lack of a fact, name the gap in one line.
