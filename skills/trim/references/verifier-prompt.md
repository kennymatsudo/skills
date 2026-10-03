# Verifier prompt

Pass the text below as the subagent's prompt, with both versions filled in.

---

A document was trimmed to remove redundancy. Find anything the trim lost or changed. Assume it did.

## Original

{ORIGINAL}

## Trimmed

{TRIMMED}

## Check every claim

List every claim in the original: each rule, condition, exception, number, default, reason, and the point of each example. For each one, find it in the trimmed version and decide:

- **Present:** the trimmed text says the same thing, in any wording or place.
- **Changed:** it is there but weaker, stronger, narrower, or broader. A dropped "only", "never", "unless", or qualifier counts.
- **Missing:** nothing in the trimmed text says it.

## Output

List only claims that are changed or missing:

- the claim, quoted from the original
- the verdict
- for changed, what the trimmed text says instead

If every claim is present, reply `All claims present.`
