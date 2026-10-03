# Handoff prompt

Fill in the template below for the picked change set and print it in one code block. A fresh agent has none of this session's context, so paste the evidence in rather than referring to the review.

---

Refactor in `{REPO_ROOT}`, on branch `{BRANCH}` at commit `{SHA}`.

## The problem

{PROBLEM}

Evidence:

{EVIDENCE: each path:line with the quoted lines}

## The change

{One numbered step per finding, in the set's order, each with its MOVE. Each step is its own commit.}

{For a move or split: what the owning module now decides or sends, and what the receiving module enforces on what it gets.}

{For a relocate: the target path, every import to rewrite, and any boundary config or exception list to update. Move or rename in its own commit with no content changes, so history follows the file.}

Out of scope: {anything nearby the review chose to leave alone, and why}.

## How to do it

1. Pin the current behavior before editing: {the existing test that covers it, or the test or recorded output to add}.
2. Make the change in small steps, running the pinning test after each one.
3. When logic moves between modules, edit and test both sides.

## Done when

- {The observable result, such as "`billing/invoice.py` no longer reads `updated_at`, and the duplicate-invoice test passes."}
- The pinning test and the existing suite pass.
