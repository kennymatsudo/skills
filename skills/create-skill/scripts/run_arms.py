#!/usr/bin/env python3
"""Run one prompt in several headless Claude Code sessions in parallel, one per arm.

Usage: run_arms.py --prompt-file FILE --arm NAME=DIR [--arm NAME=DIR ...]
                   [--preamble NAME=TEXT ...] [--model ID] [--out DIR]
                   [--timeout 1200] [--max-budget-usd N]

Each arm runs in its own directory, normally a scratch clone, with the prompt
prefixed by that arm's preamble if it has one (e.g. "Read /x/SKILL.md and
follow it."). Permission checks are skipped so the run can edit and execute,
which is why every arm directory must be a scratch copy.

For each arm it saves <out>/<name>.jsonl (the full transcript) and
<out>/<name>.diff (git diff against HEAD, untracked files included), then
prints one JSON line per arm: cost in USD, wall time, turns, whether the
session errored, its final message, and the saved paths. Exit 1 if any arm
errored or produced no result.
"""

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def pairs(values, flag):
    parsed = {}
    for value in values or []:
        name, sep, rest = value.partition("=")
        if not sep or not name:
            sys.exit(f"{flag} takes NAME=VALUE, got {value!r}")
        parsed[name] = rest
    return parsed


def run_arm(name, directory, prompt, args):
    out = Path(args.out)
    transcript = out / f"{name}.jsonl"
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
           "--dangerously-skip-permissions", "--no-session-persistence"]
    if args.model:
        cmd += ["--model", args.model]
    if args.max_budget_usd:
        cmd += ["--max-budget-usd", str(args.max_budget_usd)]
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    result = None
    with transcript.open("w") as log:
        try:
            proc = subprocess.run(cmd, cwd=directory, env=env, stdin=subprocess.DEVNULL,
                                  capture_output=True, text=True, timeout=args.timeout)
            stdout = proc.stdout
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        log.write(stdout)
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result":
            result = event

    diff_path = out / f"{name}.diff"
    # Intent-to-add makes new files show in the diff without staging their content.
    subprocess.run(["git", "add", "-N", "."], cwd=directory, capture_output=True)
    diff = subprocess.run(["git", "diff", "HEAD"], cwd=directory, capture_output=True, text=True).stdout
    diff_path.write_text(diff)

    summary = {"arm": name, "transcript": str(transcript), "diff": str(diff_path),
               "diff_lines": diff.count("\n")}
    if result is None:
        summary.update({"error": "no result event; timed out or crashed"})
    else:
        summary.update({
            "cost_usd": round(result.get("total_cost_usd") or 0, 4),
            "seconds": round((result.get("duration_ms") or 0) / 1000, 1),
            "turns": result.get("num_turns"),
            "is_error": result.get("is_error"),
            "result": (result.get("result") or "")[:500],
        })
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--arm", action="append", required=True, help="NAME=DIR, repeatable")
    parser.add_argument("--preamble", action="append", help="NAME=TEXT prepended to that arm's prompt")
    parser.add_argument("--model")
    parser.add_argument("--out", default="runs")
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("--max-budget-usd", type=float)
    args = parser.parse_args()

    arms = pairs(args.arm, "--arm")
    preambles = pairs(args.preamble, "--preamble")
    if unknown := set(preambles) - set(arms):
        sys.exit(f"--preamble names unknown arm(s): {', '.join(sorted(unknown))}")
    for name, directory in arms.items():
        if not (Path(directory) / ".git").exists():
            sys.exit(f"arm {name}: {directory} is not a git checkout; use a scratch clone")
    prompt = args.prompt_file.read_text().strip()
    Path(args.out).mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=len(arms)) as pool:
        summaries = list(pool.map(
            lambda item: run_arm(item[0], item[1], f"{preambles[item[0]]}\n\n{prompt}"
                                 if item[0] in preambles else prompt, args),
            arms.items(),
        ))
    for summary in summaries:
        print(json.dumps(summary))
    return 1 if any(s.get("error") or s.get("is_error") for s in summaries) else 0


if __name__ == "__main__":
    sys.exit(main())
