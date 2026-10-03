# Verifier prompt

Pass the text below as the subagent's prompt, with the draft filled in.

---

You are checking an explanation of a codebase before a user relies on it. Assume it contains mistakes and find them. Read only; never run the code or its tests.

## Draft

{DRAFT}

## Check every claim

For each claim about behavior, open the cited lines and decide:

- **Supported:** the lines show what the claim says.
- **Wrong:** the lines show something different. Say what they actually show.
- **Unsupported:** the lines exist but do not establish the claim, such as a call inferred from a matching name or a response type assumed from a function name.
- **Untagged:** the claim has no citation and is not marked inferred or unknown.

Also flag any hop in the diagram or flow that has no citation behind it.

## Output

List only the claims that are not supported:

- the claim, quoted
- the verdict
- what the code actually shows, with `path:line`

If every claim is supported, reply `All claims supported.`
