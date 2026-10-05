---
name: pr-description
description: >-
  Write or rewrite a pull request title and body, whether opening a new PR or
  updating an existing one: one or two sentences on why, then a few
  high-level bullets, in the repo's PR template when it has one. Offers notes
  for review bots on changes that look wrong on purpose. Use for "write a PR
  description", "update the PR description", "rewrite the PR body",
  "something to paste into the PR", and when opening a PR. Use commit for
  commit messages.
---

# PR description

You own a PR body a reviewer can read in under a minute: why the change exists, and what it does at a high level.

## 1. Find the change set

Gather in parallel:

- `git rev-parse --show-toplevel`, `git rev-parse --abbrev-ref HEAD`, `git rev-parse HEAD`, and `git status --short`
- `gh pr view --json number,title,body,url,baseRefName,headRefOid,state`
- Root-level `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING*`, and `.github` guidance on PR titles or bodies

Classify the PR lookup as open, closed or merged, absent, or failed (auth, network, repository), and keep `gh` errors visible. Treat a closed or merged PR as absent unless the user wants its historical diff.

**Open PR.** Describe the host's state: the base is `baseRefName`, and the diff is `gh pr diff <number>` plus `--name-only`. If local `HEAD` differs from `headRefOid` or the tree is dirty, name those changes and leave them out unless the user wants the upcoming local state. The existing body supplies facts to keep (ticket, links, test plan, reasons the author gave), never a draft to patch: step 4 writes the lead and bullets fresh from the whole diff, even when one commit is new.

**No open PR.** Resolve the default branch with `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`. Prefer a verified `origin/<base>`; fall back to a local `<base>` and say it may be stale. Read `git log <base>..HEAD --oneline` and `git diff --find-renames <base>...HEAD` with `--stat` and `--name-status`. If the tree is dirty, ask once whether to include it; if yes, diff the merge base against the working tree and read the untracked files.

If no source gives a trustworthy base, ask. Read any `AGENTS.md`, `CLAUDE.md`, or `CONTRIBUTING*` between the root and the changed files; the more specific one wins.

Done when the base, the diff source, the local/remote relationship, the existing title and body, and every changed file are accounted for.

## 2. Pick the layout

A repository template wins over the default layout. If the existing PR body clearly fills in a template, use that template's structure. Otherwise check these regular files in order, in either casing (`pull_request_template.md` or `PULL_REQUEST_TEMPLATE.md`):

1. `.github/pull_request_template.md`
2. `pull_request_template.md`
3. `docs/pull_request_template.md`
4. Markdown files directly inside `.github/PULL_REQUEST_TEMPLATE/`, then `PULL_REQUEST_TEMPLATE/`, then `docs/PULL_REQUEST_TEMPLATE/`

A single file beats a directory. A directory template only applies when the author picks one, so with several candidates, ask which, unless the existing body clearly matches one. List them with `rg --files <dir> -g '*.md' | sort`.

With a template, keep its required headings, order, checklists, metadata, automation markers, closing keywords, and bot-managed comments. Replace instructional HTML prompts with answers, tick a box only with evidence, and write `N/A` where an answer is required. Never fill a slot with a made-up value: an example ticket like `XXX-123` stays out until you have the real one. A section about what the author did, such as a manual test plan or its evidence, gets only steps the session shows were done; otherwise leave it for the author. Put the lead and bullets from step 4 in the section that asks what changed and why.

With no template, the body is the lead paragraph and the bullet list, with no headings.

Done when the layout is chosen and, with a template, each section is mapped to what goes in it.

## 3. Sort the changes

Read the diff, and read surrounding code only where the diff doesn't show what a change is for. List every changed file or group of files and put each in one bucket:

- **Headline.** What the PR exists to do. These become the bullets.
- **Supporting.** Tests, docs, renames, formatting, generated and lock files, and other churn that follows from a headline change. Left out of the body.
- **Unrelated.** Changes outside the PR's purpose. Each gets a bullet, so the branch's mix is visible.

Take the motivation and goal from the conversation, the commits, a linked ticket, or the existing body. If none of them says why, ask the user one question rather than guess. Commit messages are written for the code's maintainers, so take their reasons, not their wording.

Then list **look-wrong candidates**: changes a careful reviewer reading only the diff would likely flag as a bug, such as a removed check, a widened permission, a swallowed error, or a skipped test. Keep a candidate only when its reason comes from a source: a decision in this session, a commit message, a code comment, a ticket, or the user. A reason you inferred from the diff alone doesn't qualify.

Done when every changed file has a bucket, the motivation is sourced or asked for, and each look-wrong candidate has its source named.

## 4. Write

Write for a reviewer who hasn't opened the code yet: what users, operators, and callers will notice. Code identifiers, SQL, type-checker terms, exception types, and metric names stay out unless the reviewer must act on one, such as a new setting to configure.

- **Lead.** One or two sentences: the problem, then what the change sets out to achieve. No windup.
- **Bullets.** One per headline change, plus unrelated ones, three to six. Each is one line saying what changed in behavior, never file by file. Leave out supporting changes unless they are the point of the PR.
- **Flat.** No bold sub-labels ("What changes", "Heads up", "Out of scope") and no headings beyond the template's.
- **Net diff.** Describe the branch against its base. Leave out anything added and then removed within the branch, and don't say "no longer" about something the branch itself introduced.
- **Plain words.** Gloss a domain term once if no plain word works. Leave out jargon and internal shorthand.
- **Describe, never grade.** No sentence claiming the change is safe, correct, well tested, or low risk.
- **Short.** Under 150 words and at most six bullets, not counting template boilerplate. If it runs over, cut bullets before you cut the lead.
- **Title.** Follow repository convention; otherwise a short imperative naming the outcome. Keep a good existing title.

Keep closing keywords and useful existing links. Facts with no source stay out.

Done when the lead opens with the problem, every bullet maps to a headline or unrelated change, no supporting change appears without reason, and `wc -w` run on the lead and bullets exactly as they will be posted shows they are within the limits.

## 5. Offer review-bot notes

Skip this step when step 3 found no look-wrong candidates. Otherwise read `references/review-notes.md` and follow it.

Done when each candidate has the user's choice and the chosen notes are written.

## 6. Present and apply

Read `references/apply.md` and follow it. Keep unresolved questions for the author outside the PR body.

Done when the title and body are shown, the clipboard result is reported, and each PR edit is declined or confirmed and its result reported.

**Reply:** the title and body, the slots left for the author (ticket link, test plan), the clipboard result, which review-bot notes were added and where, and the PR edit result if one was made.
