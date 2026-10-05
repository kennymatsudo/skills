#!/usr/bin/env python3
"""Measure how often a skill's description gets it loaded, in a real harness.

Usage: trigger_test.py --harness {claude,codex,pi} --skill <skill-dir> [<skill-dir> ...]
                       [--queries <queries.json>] [--description TEXT] [--proxy]
                       [--runs 1] [--give-up-after 8] [--workers 4] [--timeout 90] [--model ID]

queries.json is a list of {"query": "...", "should_trigger": true|false}. It
defaults to <skill-dir>/evals/triggers.json, so a skill's queries are written
once and rerun on every change.

Each run is a fresh headless session in an empty scratch project that holds a
uniquely named copy of the skill, so a hit on the copy is unambiguous. The
installed original, if any, still competes. With --description, its loads are
reported separately, because they mean the old description won. Without it,
the copy and the original carry the same description, so a load of either counts.
Runs are real agent turns and cost what those turns cost, so a session ends as
soon as it loads either copy, or after --give-up-after tool calls without one
(0 runs to the timeout). With --runs above 1, a query stops once one outcome
holds a majority of its runs.

--proxy skips the sessions. One model call gets every installed model-invoked
skill's description and every query from all the named skills, and says which
skills it would load for each. It is a cheap estimate of routing, not a load,
and its results are labeled that way.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("trigger_test.py needs PyYAML: pip install pyyaml")

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def read_skill(skill_dir):
    """Return (frontmatter dict, SKILL.md text, end of frontmatter), or None if unparseable."""
    try:
        text = (skill_dir / "SKILL.md").read_text()
        match = FRONTMATTER.match(text)
        meta = yaml.safe_load(match.group(1)) if match else None
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(meta, dict):
        return None
    return meta, text, match.end()


def model_invoked(skill_dir, meta):
    """False when any harness is told the skill is user-invoked only."""
    if meta.get("disable-model-invocation") is True:
        return False
    policy = skill_dir / "agents" / "openai.yaml"
    if policy.exists():
        try:
            data = yaml.safe_load(policy.read_text()) or {}
        except yaml.YAMLError:
            return True
        if (data.get("policy") or {}).get("allow_implicit_invocation") is False:
            return False
    return True


def install_candidate(harness, skill_dir, description, scratch):
    """Copy the skill under a unique name where the harness discovers it."""
    meta, text, end = read_skill(skill_dir)
    original = meta["name"]
    candidate = f"{original}-candidate-{uuid.uuid4().hex[:6]}"
    meta["name"] = candidate
    if description:
        meta["description"] = description

    project = scratch / "project"
    project.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    parent = {
        "claude": project / ".claude" / "skills",
        "codex": project / ".agents" / "skills",
        "pi": scratch / "pi-skills",
    }[harness]
    target = parent / candidate
    shutil.copytree(skill_dir, target)
    frontmatter = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=10_000)
    (target / "SKILL.md").write_text(f"---\n{frontmatter}---\n{text[end:]}")
    return project, target, original, candidate


def command_for(harness, query, project, target, model):
    if harness == "claude":
        # Plan mode keeps every tool visible, as in real use, but blocks changes.
        cmd = ["claude", "-p", query, "--output-format", "stream-json", "--verbose", "--permission-mode", "plan"]
        if model:
            cmd += ["--model", model]
    elif harness == "codex":
        cmd = ["codex", "exec", "--json", "--skip-git-repo-check", "-s", "read-only", "-C", str(project)]
        if model:
            cmd += ["-m", model]
        cmd.append(query)
    else:
        # Only the read tool: a Pi run has no sandbox, and loading a skill needs nothing else.
        cmd = ["pi", "-p", "--mode", "json", "--no-session", "--tools", "read", "--skill", str(target)]
        if model:
            cmd += ["--model", model]
        cmd.append(query)
    return cmd


def tool_inputs(harness, event):
    """Yield the input of each tool call in one stream event, never its output.

    Output is excluded because a directory listing that merely names the skill
    would otherwise count as loading it.
    """
    if harness == "claude" and event.get("type") == "assistant":
        for block in event.get("message", {}).get("content", []):
            if block.get("type") == "tool_use":
                yield block.get("input", {})
    elif harness == "codex" and event.get("type") == "item.started":
        item = event.get("item", {})
        if item.get("type") == "command_execution":
            yield {"command": item.get("command", "")}
    elif harness == "pi" and event.get("type") == "tool_execution_start":
        yield event.get("args", {})


def loads(tool_input, name):
    """True when a tool call invokes the named skill or reads its SKILL.md."""
    if isinstance(tool_input, dict) and tool_input.get("skill") == name:
        return True
    return f"/{name}/SKILL.md" in json.dumps(tool_input)


def run_once(harness, query, project, target, original, candidate, timeout, model, give_up_after):
    """Return ("candidate" | "original" | None, other skills loaded) for one headless session."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    proc = subprocess.Popen(
        command_for(harness, query, project, target, model),
        cwd=project, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
    )
    verdict = None
    others = set()
    calls = 0
    timer = threading.Timer(timeout, proc.kill)
    timer.start()
    try:
        for line in proc.stdout:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            for tool_input in tool_inputs(harness, event):
                calls += 1
                if loads(tool_input, candidate):
                    verdict = "candidate"
                elif loads(tool_input, original):
                    verdict = "original"
                elif isinstance(tool_input, dict) and isinstance(tool_input.get("skill"), str):
                    others.add(tool_input["skill"])
            if verdict or (give_up_after and calls >= give_up_after):
                break
    finally:
        timer.cancel()
        proc.kill()
        proc.wait()
    return verdict, others


def skill_roots(harness):
    home = Path.home()
    if harness == "claude":
        return [Path(os.environ.get("CLAUDE_CONFIG_DIR", home / ".claude")) / "skills", home / ".agents" / "skills"]
    if harness == "codex":
        return [Path(os.environ.get("CODEX_HOME", home / ".codex")) / "skills", home / ".agents" / "skills"]
    # Pi's settings exclude the ~/.agents collection, so its own root is the whole catalog.
    return [Path(os.environ.get("PI_CODING_AGENT_DIR", home / ".pi" / "agent")) / "skills"]


def installed_catalog(harness):
    """Names and descriptions of the model-invoked skills the harness lists globally.

    Plugin and built-in skills are not included, which is one reason the proxy
    is an estimate.
    """
    catalog = {}
    for root in skill_roots(harness):
        for skill_dir in sorted(root.glob("*/")):
            parsed = read_skill(skill_dir)
            if not parsed:
                continue
            meta = parsed[0]
            name, description = meta.get("name"), meta.get("description")
            if name and description and name not in catalog and model_invoked(skill_dir, meta):
                catalog[name] = " ".join(str(description).split())
    return catalog


def proxy_prompt(catalog, requests):
    skills = "\n".join(f"- {name}: {description}" for name, description in sorted(catalog.items()))
    numbered = "\n".join(f"{i}. {query}" for i, query in enumerate(requests, 1))
    return (
        "You are the skill router for a coding agent. Before and during a task, the agent loads the skills "
        "whose descriptions fit it, judged only from the list below. It may load several, or none.\n\n"
        f"Skills:\n{skills}\n\n"
        "For each numbered request, list the skills the agent would load while doing it. Reply with only a "
        'JSON object mapping each number to a list of skill names, like {"1": [], "2": ["some-skill"]}.\n\n'
        f"Requests:\n{numbered}"
    )


def proxy_choices(harness, prompt, model, timeout):
    """Ask the harness's model once and return {request number: [skill names]}."""
    with tempfile.TemporaryDirectory(prefix="trigger-proxy-") as tmp:
        out = Path(tmp) / "answer.txt"
        if harness == "claude":
            cmd = ["claude", "-p", prompt, "--tools", "", "--output-format", "text"]
            if model:
                cmd += ["--model", model]
        elif harness == "codex":
            cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "read-only", "-C", tmp, "-o", str(out)]
            if model:
                cmd += ["-m", model]
            cmd.append(prompt)
        else:
            cmd = ["pi", "-p", "--no-tools", "--no-session"]
            if model:
                cmd += ["--model", model]
            cmd.append(prompt)
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        result = subprocess.run(cmd, cwd=tmp, env=env, stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=timeout)
        answer = out.read_text() if out.exists() else result.stdout
    match = re.search(r"\{.*\}", answer, re.DOTALL)
    if not match:
        sys.exit(f"proxy reply had no JSON object:\n{answer[:500]}")
    return {int(k): v if isinstance(v, list) else [v] for k, v in json.loads(match.group(0)).items()}


def report(harness, name, queries, rates, original_hits, label, other_skills=None):
    results, passed = [], 0
    other_skills = other_skills or [set()] * len(queries)
    for q, rate, originals, others in zip(queries, rates, original_hits, other_skills):
        ok = (rate >= 0.5) == bool(q["should_trigger"])
        passed += ok
        results.append({
            "query": q["query"], "should_trigger": q["should_trigger"], "trigger_rate": rate,
            "original_hits": originals, "other_skills": sorted(others), "pass": ok,
        })
        print(f"{'PASS' if ok else 'FAIL'} {rate:.2f} {'+' if q['should_trigger'] else '-'} "
              f"{'(original fired) ' if originals else ''}"
              f"{'(loaded ' + ', '.join(sorted(others)) + ') ' if others else ''}{q['query'][:90]}")
    print(f"\n{name}: {passed}/{len(queries)} passed on {harness}{label}\n")
    return {"skill": name, "harness": harness, "proxy": bool(label), "passed": passed,
            "total": len(queries), "results": results}


def run_real(args, skill_dir, queries):
    with tempfile.TemporaryDirectory(prefix="trigger-test-") as tmp:
        project, target, original, candidate = install_candidate(args.harness, skill_dir, args.description, Path(tmp))
        majority = args.runs // 2 + 1

        def is_hit(verdict):
            return verdict == "candidate" or (verdict == "original" and not args.description)

        def decide(query):
            """Run the fewest sessions that settle the majority outcome."""
            def once(_):
                return run_once(args.harness, query, project, target, original, candidate,
                                args.timeout, args.model, args.give_up_after)
            with ThreadPoolExecutor(max_workers=majority) as inner:
                verdicts = list(inner.map(once, range(majority)))
            while len(verdicts) < args.runs:
                hits = sum(is_hit(v) for v, _ in verdicts)
                if hits >= majority or len(verdicts) - hits >= majority:
                    break
                verdicts.append(once(None))
            return verdicts

        with ThreadPoolExecutor(max_workers=max(1, args.workers // majority)) as pool:
            per_query = list(pool.map(decide, [q["query"] for q in queries]))
    rates, originals, others = [], [], []
    for mine in per_query:
        rates.append(sum(is_hit(v) for v, _ in mine) / len(mine))
        originals.append(sum(v == "original" for v, _ in mine))
        others.append(set().union(*(o for _, o in mine)))
    return report(args.harness, original, queries, rates, originals, "", others)


def run_proxy(args, tests):
    catalog = installed_catalog(args.harness)
    for meta, _ in tests:
        catalog[meta["name"]] = " ".join(str(args.description or meta["description"]).split())
    requests = [q["query"] for _, queries in tests for q in queries]
    choices = proxy_choices(args.harness, proxy_prompt(catalog, requests), args.model, max(args.timeout, 180))
    summaries, n = [], 1
    for meta, queries in tests:
        rates = []
        for _ in queries:
            rates.append(1.0 if meta["name"] in choices.get(n, []) else 0.0)
            n += 1
        summaries.append(report(args.harness, meta["name"], queries, rates, [0] * len(queries), " (proxy)"))
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--harness", required=True, choices=["claude", "codex", "pi"])
    parser.add_argument("--skill", required=True, type=Path, nargs="+")
    parser.add_argument("--queries", type=Path, help="default: <skill-dir>/evals/triggers.json")
    parser.add_argument("--description", help="test this description instead of the one in SKILL.md")
    parser.add_argument("--proxy", action="store_true", help="one model call estimates routing instead of sessions")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--give-up-after", type=int, default=8,
                        help="tool calls without a load before a session counts as no load; 0 waits for the timeout")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--model")
    args = parser.parse_args()

    if len(args.skill) > 1 and (args.queries or args.description):
        sys.exit("--queries and --description apply to one skill; name a single --skill")
    if shutil.which({"claude": "claude", "codex": "codex", "pi": "pi"}[args.harness]) is None:
        sys.exit(f"{args.harness} CLI not found on PATH")

    tests = []
    for skill_dir in (s.resolve() for s in args.skill):
        parsed = read_skill(skill_dir)
        if not parsed:
            sys.exit(f"{skill_dir}/SKILL.md has no parseable frontmatter")
        meta = parsed[0]
        if not model_invoked(skill_dir, meta):
            sys.exit(f"{meta['name']} is user-invoked, so nothing can trigger it; there is no description to test")
        queries_path = args.queries or skill_dir / "evals" / "triggers.json"
        if not queries_path.exists():
            sys.exit(f"no queries at {queries_path}; write them there or pass --queries")
        tests.append((meta, json.loads(queries_path.read_text())))

    if args.proxy:
        summaries = run_proxy(args, tests)
    else:
        summaries = [run_real(args, Path(skill_dir).resolve(), queries)
                     for skill_dir, (_, queries) in zip(args.skill, tests)]
    print(json.dumps(summaries))
    return 0 if all(s["passed"] == s["total"] for s in summaries) else 1


if __name__ == "__main__":
    sys.exit(main())
