# Verifier prompt

Pass the text below as the subagent's prompt, with both versions filled in.

---

A document was rewritten to read better: reordered, shortened, and reworded. Find any fact the rewrite lost or changed. Assume it did.

## Original

{ORIGINAL}

## Rewrite

{REWRITE}

## Check every claim

List every claim in the original: each fact, rule, condition, exception, number, date, name, link, command, reason, and the point of each example. For each one, find it in the rewrite and decide:

- **Present:** the rewrite says the same thing, in any wording or place.
- **Changed:** it is there but weaker, stronger, narrower, or broader. A dropped "only", "never", "unless", or qualifier counts, and so does a number or name that differs.
- **Missing:** nothing in the rewrite says it.

Also list any claim in the rewrite that the original does not support.

## Output

List only claims that are changed, missing, or unsupported:

- the claim, quoted
- the verdict
- for changed, what the rewrite says instead

If every claim is present and nothing is unsupported, reply `All claims present.`
