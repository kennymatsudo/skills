---
name: review-against-harness
description: >-
  Test a teammate's pull request against the repo's end-to-end harness: list
  every fix and test case the PR claims, decide with the developer which
  belong in the harness, build only those checks, run them on the PR's build,
  sort each failure into PR defect, already tracked, harness problem, or
  flake, and draft a PR comment of what passed, what failed, and what went
  untested. Use for "review this PR against the harness", "run our scenarios
  on PR #123", "which of this PR's test cases belong in the harness". Use
  review-pr to find defects by reading the code.
disable-model-invocation: true
---

# Review a pull request against the harness

You own two answers for one teammate's pull request: which of its claims the harness should guard, and whether the PR delivers them on the real stack. The harness is the expensive layer, so a claim earns a check only when nothing smaller can see it.

The harness is the repo's end-to-end verification layer: a kit the build-verification skill set up (`verify-*/rules.md` in a skills directory), or else the harness the repo's agent instructions name. If neither exists, stop and say so. Read its rules and its run instructions (lanes, the stack check, which actions need the developer's OK, evidence, cleanup) before the first run.

## 1. List the claims

Read the PR's title, description, changed files, and head commit from the code host. List every fix or test case it claims, using the PR's own section names and numbers, plus anything it says it moved to another ticket.

Done when every claim in the description is on the list, and the list names the PR's head commit.

## 2. Gate each claim

Read the harness's current coverage: its feature or scenario docs, and the open findings and untested cases in its chosen results home. Then decide every claim on the list as one of:

- **Add**: the outcome depends on two or more services or components agreeing, or on real timing between them (a poll, a webhook, a send in flight), and no current check proves it. Name the components, and the break the check would catch that no single component's own tests could. If you can only name a break inside one component, the claim is a Skip, even when reaching the situation takes several services.
- **Already covered**: a current check proves it. Name the check with its `file:line`, and plan to rerun it on the PR's build. When a check covers only part of the claim, say which part, and gate the rest. Before saying no check covers something, search the check code for it.
- **Add with a missing step**: it belongs, but no current step reaches the situation. Name the step to build; build it now if the developer agrees, rather than deferring.
- **Skip**: one component's code decides the outcome, even when the harness could drive it, so the PR's own unit tests are its home; or the harness would have to fake the very failure it tests.

A check for behavior the PR does not deliver yet still goes in now and fails until it does, but only when it names the ticket or pull request that will make it pass, and it reports when it starts passing so that note gets removed.

Present the claims in the PR's order, not grouped by verdict. For each verdict give a one-line reason, and for each Add, where it lands and what it costs to run (time, shared resources, side effects). Ask the developer to approve the list. Approving it is the go-ahead for exactly the runs and side effects it names.

Done when every claim has a verdict and a reason, and the developer has approved the list.

## 3. Build the approved checks

Build only what was approved, in the harness's existing scenarios and drivers, with unit tests beside them, following the kit's `rules.md` or the harness's own conventions. A check of what a page or a polled service shows waits for the state it expects, up to one refresh cycle, rather than sampling once. Update every doc that describes the changed scenarios.

Done when the unit suite passes and each new check fails with its behavior reverted, using the cheapest proof the harness allows (build-verification's planned break, for a kit).

## 4. Run on the PR's build

Load the PR's code into the stack the way the harness's docs say for that repo, then run the approved scenarios. Before handing any step to the developer as one only they can run, read the command's script: a step needs them only when it prompts, needs their login or credentials, or has a side effect they have not approved. Run everything else yourself.

Confirm each run's evidence names the PR's head commit and any other component versions it depended on. Decide reruns from the evidence: rerun only when it points to a stack or harness cause, and report every rerun. A failed product check may already have enough evidence to compare with the base build.

Done when each approved scenario has finished on the PR's head commit, and every checkout and service is back where it started.

## 5. Sort each failure

For every failed check, decide one:

- **PR defect**: the same check passes on the base build (a comparable recorded result, or a base run) and fails on the PR's build. Run the base only for failures. The comparison must use equivalent entry points and external conditions.
- **Already tracked**: the failure is an open finding in the project's results home or a ticket the PR names.
- **Harness problem**: the screenshot, trace, or stored state shows the product did the right thing, and the check judged it wrong. Fix the check, say so, and do not count the run as evidence for that claim.
- **Flake or stack problem**: a rerun disagrees, or the run never reached the claim (a redirect, a stopped service, a stale checkout). Its later checks are void. The same flake twice is a harness problem until its cause is found: add the diagnostic that would name the cause before retrying again.
- **Unresolved**: the check failed on the PR, but a comparable base result is unavailable and the evidence cannot place it in the other categories. Name the base check needed.

Done when every failure has one verdict with the evidence that decided it.

## 6. Report

Update the harness's chosen results home, if it has one: a results row for the PR's commit, and the open findings and untested cases the run changed. Draft the PR comment:

- One line on how it was tested and the commit.
- **Passed**, **Failed on this PR**, **Failed, tracked elsewhere**, **Unresolved failure**, and **Not tested end to end**, each claim named by what the user sees, with the PR's section number in brackets. An unresolved failure names the base check needed. A "not tested" line says what was not proven, not that a run failed.
- Anything the PR changes that a reader would not expect, under **Worth knowing**.

Show the draft. Post or edit the comment only when the developer says to, then link it.

Done when the results home is updated, if one exists, and the comment is drafted or posted on the developer's word.

Reply: the gate list with each verdict, the checks built, each claim's result with the commit it ran on, every rerun, the PR comment (or its link), and the shared resources the runs used.
