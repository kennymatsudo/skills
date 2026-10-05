---
name: squash
description: >-
  Squash a branch's commits into one, either just the unpushed ones or the
  whole branch including commits already pushed. Lists each commit with a
  one-line summary, asks how far to go, then writes one message for the net
  result. Use for "squash", "squash my commits", "squash this branch",
  "collapse these into one commit". Use commit to make new commits or fold a
  follow-up into one.
---

# Squash

You own a branch whose squashed commit reads as if the work had been done in one go.

## 1. Find the range

Run `git status`. If anything is already staged, stop and ask: the reset in step 4 would fold it into the squash.

Find the default branch with `git symbolic-ref --short refs/remotes/origin/HEAD`, falling back to `origin/main`, then `origin/master`. The squash base is `git merge-base HEAD <default-branch>`, unless:

- The user named a base. Use theirs.
- The current branch is the default branch. The base is `origin/<current-branch>`, which covers only unpushed commits. If the user wants pushed commits too, ask how far back (a commit or a count) and use that as the base.
- No default branch exists on the remote. Ask the user for a base.

Done when `git log --oneline <base>..HEAD` lists the candidates. If it is empty, say there is nothing to squash and stop.

## 2. Summarize each commit

Run `git show <hash>` for each candidate and write a one-sentence plain-English summary. List them oldest first, marking each one reachable from `origin/<current-branch>` as pushed:

```
1. a1b2c3d — <summary> (pushed)
2. e4f5g6h — <summary> (pushed)
3. i7j8k9l — <summary>
```

## 3. Ask how far

Ask which of these to squash:

- **Unpushed only.** From the first unpushed commit to HEAD. No force-push needed.
- **Everything.** The whole list. When it includes pushed commits, say this rewrites history the remote already has and the branch will need a force-push.
- **From #N.** From commit #N to HEAD.

Wait for the answer. If the chosen range holds one commit, say there is nothing to squash and stop.

On the default branch, a range with pushed commits needs a second, explicit yes. Say that force-pushing it rewrites history everyone else has pulled, so it is only safe when nobody else works on the repo. Wait for the yes before resetting.

## 4. Reset

The reset target is the commit just before the first one being squashed, or the squash base for everything. Note the current HEAD hash, then run `git reset --soft <target>`.

Done when `git status` shows the squashed range as staged changes.

## 5. Commit

Follow the commit skill to write and make the commit; don't hand this step back to the user. If the commit skill isn't installed, commit with a short imperative title and a brief body.

The message describes the net end state of the whole range: what the code now does. Write it from the full staged diff, not from the last few commits. Don't narrate the individual commits or frame it as replacing or retiring an old approach, since the reader of one commit never saw the intermediate steps.

Done when `git log --oneline <target>..HEAD` shows one commit.

## 6. Hand back the push

Never push. If the squash rewrote pushed commits, tell the user the branch has diverged from `origin/<current-branch>` and that publishing it takes `git push --force-with-lease`.

**Reply:** the new `git log --oneline` for the branch, the old HEAD hash so the user can undo with `git reset --hard <old-head>`, and the force-push note if it applies.
