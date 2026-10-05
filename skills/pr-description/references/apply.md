# Present and apply

## Present

Show the title and the complete body in separate, labeled code blocks. For an existing PR, show the complete replacement and list in one line any fact it drops, such as a link, a ticket, a test-plan step, or a reason the author gave. Rewording or cutting earlier bullets needs no mention.

## Copy the body

Copy the body alone unless the user asked for preview only. Use whichever clipboard command exists:

- macOS: `pbcopy`
- Linux: `xclip -selection clipboard`, then `xsel --clipboard --input`
- WSL or Windows: `clip.exe`

Use a quoted heredoc so backticks and `$` stay literal:

```bash
cat <<'PRDESC_EOF' | <clipboard-command>
<description body>
PRDESC_EOF
```

If no clipboard command exists, say so and leave the body for manual copying.

## Edit an open PR

Ask `Update PR #<number> with this description? (yes/no)`. If the title changed, ask about it separately. Each yes covers only the edit it names.

On a yes for the body, pass it through standard input:

```bash
gh pr edit <number> --body-file - <<'PRDESC_EOF'
<description body>
PRDESC_EOF
```

Pass `--title` only after a yes for the title. Report the command result and PR URL.

## No open PR

Say the body is ready to paste and that `gh pr create` can open the PR. Opening it is a separate request.

## What this skill changes

Only two things, each with the user's yes: the open PR's title or body, and code comments the user chose in the review-bot notes step. Never stage, commit, push, or open, merge, close, or reopen a PR.
