---
name: review-tests
description: >-
  Review the tests a branch adds or changes, right after an agent writes them:
  check that each can fail when its behavior breaks, expects what the intended
  contract says rather than what the code returns, wasn't weakened to pass, and
  isn't a duplicate, then apply the safe fixes. Use for "review the tests",
  "are these tests any good", "check the tests before I commit". Use
  review-pr for bugs in the code itself.
disable-model-invocation: true
---

# Review Tests

You own one verdict for every test the branch adds or changes. A test earns its place by going red when the behavior it guards breaks; green CI and coverage don't earn a keep.

Never delete or merge a test that existed before the branch; rework it instead. Never weaken an assertion to make a test pass. Leave every production file exactly as you found it.

If the user asks for an audit or dry run, stop after step 4 and report.

## 1. Collect the diff

By default, cover the branch: everything that differs from its merge base with the default branch, whether committed, staged, unstaged, or untracked. Find the default branch with `git symbolic-ref --short refs/remotes/origin/HEAD`, else `origin/main`, else `origin/master`. From the repo root, run `python3 <skill-dir>/scripts/test_diff.py --base <default>`, with this skill's absolute directory. Narrow it when the user asks:

- **Uncommitted:** pass `--base HEAD`.
- **Staged:** pass `--base HEAD --staged`.
- **A path:** keep only the files under that path.

Tell the user the scope in one line before going further, such as "Scope: branch `foo` vs `origin/main`, 12 files".

The script lists changed test and production files, including uncommitted and untracked ones, and flags removed or changed assertion lines, new skip or focus markers, and deleted tests. It matches text patterns: treat each flag as a lead, read by hand any file it lists with no assertion found, and don't read a clean result as proof. Read the test changes with the test-only diff command it prints, plus the untracked test files; leave the production diff for step 3.

Done when every added or modified test case is listed with `file:line` and new or pre-existing, and every flag is attached to a test or noted as unrelated. For a modified pre-existing test, judge only its changed lines.

## 2. Write the contract before reading the code

For each behavior the tests claim to guard, write one line saying what should happen, taken from a source other than the implementation. Check, in order: the user's request in this session, commit messages and the branch name, a ticket they name (search the ticket tracker if the session has one), the PR description, then docstrings and type signatures. Read the tests and these sources first; open production function bodies and the production diff only after every contract line is written, because a reviewer who reads buggy code first tends to accept tests that lock the bug in. Test names don't count as a source: the agent that wrote the code wrote them too.

If no source covers a behavior, ask the user once, listing every uncovered behavior in one question. Those they don't answer stay "oracle unverified", which is never a keep.

Done when every claimed behavior has a contract line and source, or is marked unverified, and you have not yet read production function bodies or the production diff.

## 3. Judge every test

Check each test against these in order; a failure higher up outranks anything below.

1. **Goes red.** Flipping the guarded rule would fail it. Never keep as is:
   - mocks its own subject, or stubs so deep the asserted logic never runs
   - asserts only that a mock got the arguments the test passed in, or only that nothing threw
   - asserts that a code path the branch removed isn't taken; prove the new behavior instead
   - expects a value the contract doesn't give, one that exists only because the code returns it now (snapshots, recorded output, copied values)

   Mock only at boundaries the suite already mocks.
2. **Not weakened.** Every flag from step 1, and every changed expected value in a pre-existing test, needs the contract to justify it. Also look for production code that special-cases a test input.
3. **Proves something new.** No other test, in the branch or the existing suite, guards the same behavior; name the collision. Near-identical cases become one parametrized test.
4. **Guards a real risk.** A rule with branches, tested only on the happy path, gets its most valuable missing negative or boundary case.
5. **Reads like the suite.** Named for scenario and outcome (`rejects expired tokens`, not `test_process_2`), using the fixtures, factories, and parametrization in the untouched tests beside it, and following any testing rules in the repo's agent instructions or in skills whose scope covers these tests.

Give each test one verdict: **keep**, **rename**, **merge** (name the test that absorbs it), **delete** (new tests only; name what survives or why it's vacuous), **rework** (state the fix), or **flag** (a risk you won't fix yourself).

Done when every test from step 1 has a verdict and a one-sentence reason, and every keep names its contract source.

## 4. Prove it with a deliberate break

Break the guarded rule in production code (flip the condition, invert the outcome) and run only the affected tests:

- **keep** on a new or changed test: it must go red. If it stays green, check whether the break changed behavior at all; if it did, change the verdict to rework.
- **delete** or **merge**: the surviving test must go red under the same break. If it doesn't, downgrade to flag.

Skip the break when reading alone shows a test can't go red. If the repo already has a mutation tool with a command scoped to changed files, in its config, scripts, or docs, run that with a time limit instead and check only survivors on changed lines.

Make breaks in place, one at a time, yourself. Before the first, create a run directory with `mktemp -d` outside the repo, save `git diff` there, and tell the user its path. For each break, copy the production file into the run directory, break it, run the tests, restore it from the copy, and confirm `git diff -- <file>` matches its state before the break.

When the tests guard four or more production files, spawn one mid-tier subagent per production file to read the code and return, for each test, the smallest break and the command that runs it. Subagents report breaks; they never edit files.

Done when every keep on a new or changed test, delete, and merge has a result (red, green, or skipped with the reason), and `git diff` matches the copy saved before the first break.

## 5. Apply

Apply renames, merges, deletes, reworks, and suite-fit fixes. Every expected value you write must come from a step 2 contract line; report any other one instead of writing it, including reverting a value the branch changed. Then run the affected test files. A test that fails after a rework may have found a real bug: report it and leave the assertion strong.

Done when the affected test files pass, or each failure is reported with the reason.

## 6. Report

Open with the contract table from step 2 (behavior, contract, source). Then list findings by severity: can't go red or wrong expected value, then weakened, duplicate, missing risk, and suite fit. Give each `file:line`, the verdict, a one-sentence reason, and the break result. Each keep includes `contract: <source>`. Close with one line naming the tests left untouched, then delete the run directory.

Reply: the report, the changes applied, and the final test run result.
