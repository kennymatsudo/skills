# Testing a skill

Every run is a fresh headless session with no memory of this one. Fixed startup overhead dominates a short run's cost, so the savings come from running fewer sessions, not shorter ones.

## Setup

1. **Pick the scratch repo.** Clone one of the user's own local repos into a scratch directory, once per test run. Ask which if it isn't obvious; don't use a public repo the user doesn't work in.
2. **Pick the models.** Iterate with every arm on a mid-tier model. Once the with-skill arm wins, run it once on the user's session model to confirm it holds there.
3. **Hide the draft from the baseline.** The baseline arm runs where the draft isn't visible: a separate clone, with no path to the draft in its prompt. A baseline that finds the draft copies it, and the comparison means nothing.
4. **Move rivals aside.** For a trigger test, move any installed skill that shares the new skill's triggers out of the skills directory, and restore it afterward.

Give each scratch repo its own mid-tier subagent that seeds it, runs both arms, judges from the transcripts, and cleans up, so raw transcripts stay out of the main thread. The subagent returns the scores and quotes; the main agent makes the call.

## Behavior test

Use this when a skill changes what the agent does.

1. **Write 2-3 prompts** a user would actually send, with concrete context: file names, the situation, a little backstory. Leave out words like test, eval, grade, or rubric; an agent that knows it is being evaluated behaves differently.
2. **For a skill that edits code, seed planted cases first.** Commit the base, then seed the change and write an answer key: what must survive, what must go, what must be added. Confirm `git diff` against the base shows every planted case, since gitignored paths drop files silently. Copy the seeded clone once per arm.
3. **Run both arms in parallel** with `scripts/run_arms.py`. Run it, don't read it:

   ```bash
   python3 <this skill's directory>/scripts/run_arms.py --prompt-file prompt.txt --model <tier> \
     --arm with=<clone-a> --preamble with="Read <draft>/SKILL.md and follow it." \
     --arm base=<clone-b> --out <scratch>/runs
   ```

   - **The with-skill arm** is told to read the draft's `SKILL.md`.
   - **The baseline arm** gets nothing for a new skill. For an edit, it gets the snapshot of the old version, or the installed version when that is the comparison the user cares about.
   - Each arm saves its transcript and `git diff`, and the script prints cost, time, and turns per arm. It drives Claude Code; for another harness, run its CLI headless (`codex exec --json`, `pi -p --mode json`) in each clone and save the output the same way.
4. **Judge from the transcripts and diffs**, never from a run's own summary. For each arm answer: did it hit each step's "Done when"? Did it follow each rule the skill states? Against the answer key, what did it keep, cut, and add wrongly? Is the with-skill arm better than the baseline, and at what cost difference? Did the skill send it down steps that added nothing? When the arms are close, give both to a separate judge without saying which is which, in both orders, and keep only a verdict that holds in both.
5. **Separate setup from skill.** When a run's behavior traces to the scratch repo's own agent instructions or the user's global instructions, judge it as that setup, not a skill defect, and don't add repo-specific rules to the skill. Check any fact the arms disagree on against the code.
6. **Fix the general cause**, not the one prompt. Cut parts that caused wasted steps. If every run hand-wrote the same helper, bundle it as a script. Drop a rule whose check passes in both arms; it isn't earning its tokens. Rerun only the failed cases, with a setup that exercises the fix.

Done when the with-skill arm beats the baseline on accuracy at no worse cost, or on cost at equal accuracy, on the prompts that exercise the change, and the session-model confirmation run agrees. Stop after two rounds without a clear gain, and report what's still failing.

## Trigger test

Use this for a model-invoked skill with a new or changed description, or one that didn't fire. Routing differs by harness and model, so test in each harness the skill installs to.

1. **Use the saved queries** at `<skill-dir>/evals/triggers.json`, a list of `{"query": "...", "should_trigger": true}`. If there are none, write 10 to 16 once, so every later change reruns the same set.
   - **Half should trigger.** Vary them: formal and casual, short and long. Include some that never name the skill, and some multi-step tasks where the need surfaces partway.
   - **Half are near misses.** They share keywords with the skill but belong to a sibling skill or to none. Obviously unrelated queries test nothing.
   - **Make every query substantive.** Agents skip skills for tasks they can finish in one step.
2. **Show new or changed queries to the user** and adjust them. Mark about 40% `"holdout": true`, and tune only against the rest.
3. **Measure with `scripts/trigger_test.py`**, cheapest tier first. Run it, don't read it:

   ```bash
   python3 <this skill's directory>/scripts/trigger_test.py --harness <claude|codex|pi> \
     --skill <skill-dir> [<skill-dir> ...] [--proxy] [--runs 1] [--description "<candidate>"]
   ```

   - **Proxy (`--proxy`).** One model call gets every installed model-invoked description and all the named skills' queries, and says which skills it would load for each. Use it on every description change to catch descriptions stealing each other's queries. It is optimistic, missing skills loaded partway through the work, so label its results as a proxy and never stop at it.
   - **Real sessions.** Each query runs in a fresh headless session with a uniquely named copy of the skill. A session ends as soon as it loads either copy, or after `--give-up-after` tool calls without one. With `--runs 3`, a query stops once one outcome has a majority. With `--description`, loads of the installed original are reported as `(original fired)` and mean the old description won. Use `--runs 1` for a routine change. Use `--runs 3` in every harness the skill installs to after a model upgrade, a rewritten description, or a disagreement between the proxy and a real run.
4. **Before tuning for a miss**, run the installed version on the same query. A miss both versions share comes from the test setup, not the description.
5. **Fix misses in the description only:** front-load the missing case, add the phrasing the user actually typed, and name the sibling that stole a near miss.

Done when every held-out should-trigger query fires and no near miss does in real sessions, in each harness tested. Report the description before and after, with the scores per harness and which tiers ran.

## Cleanup

Delete the scratch clones and anything the runs created, and restore any skill moved aside. Done when `git status` in the user's real repos matches how you found them.
