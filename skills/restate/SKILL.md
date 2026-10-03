---
name: restate
description: >-
  Restate the user's request in your own words, using the established name for
  the pattern or problem it describes, then wait for a yes or a correction
  before acting. Gives the user precise vocabulary to use next time. Load it
  before answering whenever the user asks to hear their request back, even
  when the task itself is in the same message: "restate", "repeat back what
  I'm asking", "tell me what you think I'm asking", "say it back to me". Use
  how to explain existing code instead.
---

# Restate

You own a restatement the user can confirm or correct in one reply, and the right name for what they described.

Work from the conversation alone. Don't read files or search first: the check is whether you heard the user, and the code tempts you to restate what it does instead of what they asked.

## 1. Restate the goal

Write the goal in one or two sentences, in your own words. Reusing the user's phrasing proves nothing.

Done when the goal fits in two sentences and shares no distinctive phrase with the request.

## 2. Name it

- **The user describes a design they want followed:** name that pattern.
- **The user asks you to solve something:** name the problem, such as thundering herd or N+1 queries, not a solution pattern. Naming a solution pushes them toward it before anyone has checked the fit.

For each term:

- Use it only when the request has the term's defining traits, and list the traits that matched.
- Define it in one line.
- Add one alias at most, when two names are common.
- When only part fits, say so: "closest is X, but you also want Y".
- When nothing fits, say there is no established name. Never coin one.

Name two terms at most; more turns the restatement into a glossary.

Done when each term has its matched traits and definition, or you have said there is no established name.

## 3. Wait

End with "Go ahead, or correct me?" and stop. Send nothing beyond the restatement, the terms, and this question: assumptions, clarifying questions, risks, and plans wait until the user confirms. Proceed only on a clear yes. A correction sends you back to step 1 with it folded in. A new question or a vague reply ("whatever you think") is not a yes; ask again.

Done when the user has said yes.

## 4. Proceed

Do the original task as confirmed, using the confirmed terms.

## Example

```
You want retries to stop piling onto the payments service when it recovers.

Name: thundering herd (also "retry storm"), many clients hitting a shared
resource at the same moment. Matched: many workers, one shared dependency,
retries firing together after an outage.

Go ahead, or correct me?
```

**Reply:** the restated goal, each term with its definition and matched traits (or that none fits), and the confirmation question.
