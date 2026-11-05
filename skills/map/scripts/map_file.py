#!/usr/bin/env python3
"""Check, stamp, and diff a map file against the repo it describes.

<repo-root> is the folder citations are relative to: the repo, or for a map of one feature
across several repos, the folder that holds them all. stamp records it in the map relative to
the folder holding .map/, and every later command reads it from there.

Usage:
  map_file.py check <repo-root> <map.json>   validate structure and every citation
  map_file.py stamp <repo-root> <map.json>   record the root, the commit, and a hash of each cited file
  map_file.py stale <repo-root> <map.json>   list nodes whose cited files changed since the stamp
  map_file.py merge <repo-root> <map.json> <fragment.json>
      replace one node's children with the fragment's, check the result, and stamp it,
      under a lock so parallel writers never overwrite each other
  map_file.py queue <repo-root> <map.json>   list the boxes to build next, most useful first,
      and the small leaf components not worth a build

stamp and merge also rewrite map.html beside the map with render_html.py.

Exit codes: 0 ok (or nothing stale), 1 problems found (or something stale), 2 usage error.
"""

import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

CITE = re.compile(r"^([\w./-]+):(\d+)(?:-(\d+))?$")
KINDS = {"service", "datastore", "queue", "external", "group", "component"}
EVIDENCE = {"config", "client-call", "route", "topic", "inferred"}
SEVERITY = {"bug", "risk", "gap"}
MAX_CHILDREN = 20
# Level 2 is the handful of parts a reader keeps in mind, not one box per file.
MAX_COMPONENTS = 12
# A box shows its summary in two short lines; longer text gets cut off mid-thought.
MAX_SUMMARY = 70
# An arrow's label names what crosses it in a few words; the call itself belongs in a path.
MAX_LABEL = 24
# An unknown is a question the repo cannot answer. "I did not read it" is unfinished work.
UNREAD = re.compile(
    r"\b(not (yet )?(read|traced|checked|examined|followed|verified|searched|confirmed)"
    r"|did not (read|trace|check|examine|follow|verify)|wasn't (read|traced|checked))\b",
    re.IGNORECASE,
)
# A role says what a box is for. A file path in it describes where the code is, which the
# citation already shows.
FILE_IN_ROLE = re.compile(r"(?<![\w.])[a-z_][\w/-]*\.(py|tsx?|jsx?|rb|go|java|kt|rs|php|cs|swift|scala)\b")
# Code nothing calls is a finding about dead code, not a part of the system, and not an unknown
# either: whether anything calls it is a question the repo answers.
DEAD_ROLE = re.compile(
    r"\bno (non-test )?(caller|callers|writer|reader|service code|code (reads|calls|uses))"
    r"|\bno (non-test )?code\b[^.;]{0,30}\b(reads|writes|calls|uses)"
    r"|\b(have|has) no (writer|reader|caller)|\bnothing (reads|calls|uses|writes)",
    re.IGNORECASE,
)
# A leaf component this small with nothing it calls is read faster than a call path is built.
SMALL_COMPONENT_LINES = 40
STOPWORDS = set(
    "a an and are as at be but by for from has have in into is it its no not of on or so that the "
    "their then there this to was when which with without".split()
)


def load(map_path: Path) -> dict:
    return json.loads(map_path.read_text())


def cites_in(data: dict) -> list[tuple[str, str]]:
    """Every (owner node id, citation) pair in the map, in file order."""
    found = []
    for node in data.get("nodes", []):
        for cite in node.get("cites", []):
            found.append((node.get("id", "?"), cite))
    for edge in data.get("edges", []):
        for cite in edge.get("cites", []):
            found.append((edge.get("from", "?"), cite))
    for item in data.get("findings", []):
        for cite in item.get("cites", []):
            found.append((item.get("node", "?"), cite))
    for path in data.get("paths", []):
        for step in path.get("steps", []):
            for cite in step.get("cites", []):
                found.append((path.get("node", "?"), cite))
    return found


def cite_file(cite: str) -> str | None:
    match = CITE.match(cite)
    return match.group(1) if match else None


def check_cite(repo: Path, cite: str, line_counts: dict[str, int]) -> str | None:
    match = CITE.match(cite)
    if not match:
        return "not in path:LINE or path:START-END form"
    path_text, start_text, end_text = match.groups()
    path = repo / path_text
    if not path.is_file():
        return "file not found"
    if path_text not in line_counts:
        line_counts[path_text] = len(path.read_text(errors="replace").splitlines())
    start = int(start_text)
    end = int(end_text) if end_text else start
    if start < 1 or end < start or end > line_counts[path_text]:
        return f"out of range, file has {line_counts[path_text]} lines"
    # A one-line citation is a claim about that exact line, so a blank one points at nothing.
    if not end_text and not path.read_text(errors="replace").splitlines()[start - 1].strip():
        return "is a blank line; cite the line that defines the thing or makes the call"
    return None


def cite_range(cite: str) -> tuple[str, int, int] | None:
    match = CITE.match(cite)
    if not match:
        return None
    start = int(match.group(2))
    return match.group(1), start, int(match.group(3) or start)


def cites_overlap(first: list[str], second: list[str]) -> bool:
    """True when any citation in one list shares a file line with any in the other."""
    for a in filter(None, map(cite_range, first)):
        for b in filter(None, map(cite_range, second)):
            if a[0] == b[0] and a[1] <= b[2] and b[1] <= a[2]:
                return True
    return False


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9_]+", text.lower()) if len(w) > 2 and w not in STOPWORDS}


def similar(first: str, second: str) -> bool:
    a, b = words(first), words(second)
    return bool(a and b) and len(a & b) / min(len(a), len(b)) >= 0.4


def ancestors_of(data: dict, node_id: str) -> set[str]:
    parent = {n.get("id"): n.get("parent") for n in data.get("nodes", [])}
    chain, current = set(), parent.get(node_id)
    while current and current not in chain:
        chain.add(current)
        current = parent.get(current)
    return chain


def lineage(nodes: list[dict]) -> dict[str, set[str]]:
    """Each node id mapped to itself, its ancestors, and its descendants."""
    parent = {n.get("id"): n.get("parent") for n in nodes}
    ancestors = {}
    for node_id in parent:
        chain, current = set(), parent.get(node_id)
        while current and current not in chain:
            chain.add(current)
            current = parent.get(current)
        ancestors[node_id] = chain
    related = {node_id: {node_id} | chain for node_id, chain in ancestors.items()}
    for node_id, chain in ancestors.items():
        for ancestor in chain:
            related.setdefault(ancestor, {ancestor}).add(node_id)
    return related


def restated(data: dict) -> list[str]:
    """Findings and unknowns that repeat an earlier one on the same box, a box above or below it,
    or, for findings, a box beside it under the same parent."""
    problems = []
    related = lineage(data.get("nodes", []))
    parent_of = {n.get("id"): n.get("parent") for n in data.get("nodes", [])}
    kept: list[dict] = []
    for item in data.get("findings", []):
        node = item.get("node")
        siblings = {i for i, p in parent_of.items() if node in parent_of and p == parent_of[node]}
        family = related.get(node, {node}) | siblings
        for earlier in kept:
            if earlier.get("node") in family and cites_overlap(item.get("cites", []), earlier.get("cites", [])) \
                    and similar(item.get("text", ""), earlier.get("text", "")):
                problems.append(
                    f"finding on {item.get('node')} restates the one on {earlier.get('node')} "
                    f"(\"{earlier.get('text', '')[:60]}…\"): drop it, or fold what it adds into that one"
                )
                break
        else:
            kept.append(item)
    kept = []
    for item in data.get("unknowns", []):
        family = related.get(item.get("node"), {item.get("node")})
        twin = next((u for u in kept if u.get("node") in family and similar(item.get("text", ""), u.get("text", ""))), None)
        if twin:
            problems.append(f"unknown on {item.get('node')} restates the one on {twin.get('node')}: drop it")
        else:
            kept.append(item)
    return problems


def shared_code(nodes: list[dict]) -> list[str]:
    """Components of different services that are the same code. A queue's topic or a table may
    cite the code that declares it, so only boxes inside services and groups are compared."""
    problems = []
    kinds = {n.get("id"): n.get("kind") for n in nodes}
    components = [n for n in nodes if n.get("kind") == "component" and n.get("cites")
                  and kinds.get(n.get("parent")) in {"service", "group"}]
    for i, a in enumerate(components):
        for b in components[i + 1:]:
            if a.get("parent") != b.get("parent") and cites_overlap(a["cites"][:1], b["cites"][:1]):
                problems.append(
                    f"node {b.get('id')}: same code as {a.get('id')} ({a['cites'][0]}); map it once, "
                    "under the box that holds it, and draw an edge from the other"
                )
    return problems


def check(repo: Path, data: dict) -> list[str]:
    problems = []
    nodes = data.get("nodes", [])
    ids = [node.get("id") for node in nodes]
    known = set(ids)
    kinds = {node.get("id"): node.get("kind") for node in nodes}

    for node_id in {i for i in ids if ids.count(i) > 1}:
        problems.append(f"node {node_id}: duplicate id")
    for node in nodes:
        node_id = node.get("id", "?")
        if node.get("kind") not in KINDS:
            problems.append(f"node {node_id}: kind must be one of {sorted(KINDS)}")
        parent = node.get("parent")
        if parent is not None and parent not in known:
            problems.append(f"node {node_id}: parent {parent} does not exist")
        if node.get("kind") != "external" and not node.get("cites"):
            problems.append(f"node {node_id}: no citation")
        if len(node.get("summary", "")) > MAX_SUMMARY:
            problems.append(f"node {node_id}: summary over {MAX_SUMMARY} characters; say its role, not how it works")
        if FILE_IN_ROLE.search(node.get("summary", "")):
            problems.append(f"node {node_id}: summary names a file; say what the box is for, and leave where it is to the citation")
        if re.search(r"\bbut\b", node.get("summary", ""), re.IGNORECASE):
            problems.append(f"node {node_id}: summary has a \"but\"; a caveat about what it does belongs in a finding, not its role")
        if DEAD_ROLE.search(node.get("summary", "")):
            problems.append(
                f"node {node_id}: summary says nothing uses it; dead code is not a box. "
                "Drop it, and if a reader should act on it, record one finding on the box that holds it"
            )
    problems += shared_code(nodes)

    children: dict[str | None, int] = {}
    for node in nodes:
        children[node.get("parent")] = children.get(node.get("parent"), 0) + 1
    for parent, count in children.items():
        if count > MAX_CHILDREN:
            where = parent or "the top level"
            problems.append(f"{where}: {count} boxes, group them to {MAX_CHILDREN} or fewer")
        elif kinds.get(parent) in {"service", "group"} and count > MAX_COMPONENTS:
            problems.append(
                f"{parent}: {count} components; merge related ones into {MAX_COMPONENTS} or fewer boxes "
                "by what they do together, each citing all its files"
            )
    names = {node.get("id"): node.get("name", "").strip().lower() for node in nodes}
    for node in nodes:
        parent = node.get("parent")
        if parent and names.get(node.get("id")) == names.get(parent):
            problems.append(
                f"node {node.get('id')}: same name as its parent {parent}; a box inside repeats nothing "
                "the parent shows. Map only what is inside it"
            )

    for edge in data.get("edges", []):
        label = f"edge {edge.get('from')} -> {edge.get('to')}"
        for end in ("from", "to"):
            if edge.get(end) not in known:
                problems.append(f"{label}: {end} node does not exist")
        if edge.get("evidence") not in EVIDENCE:
            problems.append(f"{label}: evidence must be one of {sorted(EVIDENCE)}")
        if edge.get("evidence") != "inferred" and not edge.get("cites"):
            problems.append(f"{label}: no citation")
        if len(edge.get("label", "")) > MAX_LABEL:
            problems.append(f"{label}: label over {MAX_LABEL} characters; name what crosses, such as \"SQL\" or \"enqueues receipts\"")
        if kinds.get(edge.get("from")) == "external":
            problems.append(
                f"{label}: an outside system calls nothing in the map; the code that does belongs to "
                "the service that runs it"
            )

    for item in data.get("findings", []) + data.get("unknowns", []):
        if item.get("node") is not None and item.get("node") not in known:
            problems.append(f"finding or unknown on missing node {item.get('node')}")
    for item in data.get("findings", []):
        if item.get("severity") not in SEVERITY:
            problems.append(f"finding on {item.get('node')}: severity must be one of {sorted(SEVERITY)}")
        if not item.get("cites"):
            problems.append(f"finding on {item.get('node')}: no citation; a finding shows a defect in the code")
    problems += restated(data)
    for item in data.get("unknowns", []):
        if UNREAD.search(item.get("text", "")):
            problems.append(
                f"unknown on {item.get('node')}: \"{item.get('text', '')[:60]}…\" is unread code, "
                "not an unknown; read it and record what it shows"
            )
        if DEAD_ROLE.search(item.get("text", "")):
            problems.append(
                f"unknown on {item.get('node')}: \"{item.get('text', '')[:60]}…\" says nothing uses some code; "
                "the repo answers that, so it is a finding if a reader should act on it, else leave it out"
            )
    for path in data.get("paths", []):
        if path.get("node") not in known:
            problems.append(f"path on missing node {path.get('node')}")
        if len(path.get("steps", [])) < 2:
            problems.append(f"path {path.get('title')!r} on {path.get('node')}: fewer than two steps")

    line_counts: dict[str, int] = {}
    for owner, cite in cites_in(data):
        failure = check_cite(repo, cite, line_counts)
        if failure:
            problems.append(f"{owner}: {cite}: {failure}")
    return problems


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def head_commit(repo: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else None


def commits(repo: Path, files: list[str]) -> str | dict[str, str] | None:
    """The root's commit, or, when the root holds several repos, each cited repo's commit."""
    whole = head_commit(repo)
    if whole or not files:
        return whole
    tops = sorted({f.split("/", 1)[0] for f in files if "/" in f})
    found = {top: c for top in tops if (repo / top / ".git").exists() and (c := head_commit(repo / top))}
    return found or None


def commit_text(built) -> str:
    if isinstance(built, dict):
        return ", ".join(f"{name} {commit}" for name, commit in built.items())
    return str(built)


def stamp(repo: Path, map_path: Path, data: dict) -> dict:
    files = sorted({f for _, cite in cites_in(data) if (f := cite_file(cite))})
    data["root"] = os.path.relpath(repo.resolve(), map_path.resolve().parent.parent)
    data["built_at_commit"] = commits(repo, files)
    data["files"] = {f: file_hash(repo / f) for f in files if (repo / f).is_file()}
    return data


def stale(repo: Path, data: dict) -> dict[str, list[str]]:
    """Map each node id to the cited files that changed or vanished since the stamp."""
    recorded = data.get("files", {})
    changed = {
        f for f, digest in recorded.items()
        if not (repo / f).is_file() or file_hash(repo / f) != digest
    }
    by_node: dict[str, list[str]] = {}
    for owner, cite in cites_in(data):
        f = cite_file(cite)
        if f in changed and f not in by_node.setdefault(owner, []):
            by_node[owner].append(f)
    return {node: files for node, files in by_node.items() if files}


def merge(repo: Path, data: dict, fragment: dict) -> tuple[dict, list[str]]:
    """Swap the fragment's parent's old children for the fragment's entries, and return notes
    on what the swap dropped that the fragment did not say to drop."""
    parent = fragment["parent"]
    nodes = data.get("nodes", [])
    old = {n["id"] for n in nodes if n["id"] != parent and parent in ancestors_of(data, n["id"])}
    new = {n["id"] for n in fragment.get("nodes", [])}
    # A child the fragment keeps keeps what was built inside it, so re-merging a verified
    # fragment never throws away deeper levels already built. A child the fragment drops
    # takes everything inside it along.
    kept = {n["id"] for n in nodes if n.get("parent") == parent and n["id"] in new}
    inside_kept = {n["id"] for n in nodes if kept & ancestors_of(data, n["id"])}
    gone = (old - inside_kept) | new

    def keep(items: list, *fields: str) -> list:
        return [i for i in items if not any(i.get(f) in gone for f in fields)]

    notes = []
    fragment_texts = {(f.get("node"), f.get("text")) for f in fragment.get("findings", [])}
    for item in data.get("findings", []):
        if item.get("node") in kept and (item.get("node"), item.get("text")) not in fragment_texts:
            notes.append(f"dropped finding on {item.get('node')} that the fragment lacks: "
                         f"\"{item.get('text', '')[:80]}\"; add it to the fragment if a deeper build found it")
    was_loaded = {n["id"] for n in nodes if n.get("loaded")}
    fresh = [dict(n, loaded=True) if n["id"] in kept & was_loaded and "loaded" not in n else n
             for n in fragment.get("nodes", [])]
    data["nodes"] = keep(nodes, "id") + fresh
    data["edges"] = keep(data.get("edges", []), "from", "to") + fragment.get("edges", [])
    data["findings"] = keep(data.get("findings", []), "node") + fragment.get("findings", [])
    data["unknowns"] = keep(data.get("unknowns", []), "node") + fragment.get("unknowns", [])
    paths = [p for p in data.get("paths", []) if p.get("node") not in gone or p.get("node") in kept]
    if fragment.get("paths"):
        paths = [p for p in paths if p.get("node") != parent]
    data["paths"] = paths + fragment.get("paths", [])
    kept_paths = sum(1 for p in paths if p.get("node") in kept | inside_kept)
    if inside_kept or kept_paths:
        notes.append(f"kept {len(inside_kept)} boxes and {kept_paths} paths already built inside the children it keeps")
    # A rebuild may restate a note it already made about the parent itself.
    for field in ("findings", "unknowns"):
        unique = {}
        for item in data[field]:
            unique.setdefault((item.get("node"), item.get("text")), item)
        data[field] = list(unique.values())
    for node in data["nodes"]:
        if node.get("id") == parent:
            node["loaded"] = True
    return data, notes


def cited_lines(node: dict) -> int:
    total = 0
    for found in filter(None, map(cite_range, node.get("cites", []))):
        total += found[2] - found[1] + 1
    return total


def queue(data: dict) -> tuple[list[str], list[str]]:
    """Boxes not built yet, those with the most findings and arrows first, and the small leaf
    components that would cost a build to say what their one citation already shows."""
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    findings = data.get("findings", [])
    related = lineage(nodes)
    build, skip = [], []
    for node in nodes:
        if node.get("loaded"):
            continue
        node_id = node.get("id")
        calls_out = any(e.get("from") == node_id for e in edges)
        # An outside system's client code is mapped under the service that holds it.
        small_leaf = node.get("kind") == "component" and not calls_out and cited_lines(node) < SMALL_COMPONENT_LINES
        if node.get("kind") == "external" or small_leaf:
            skip.append(node_id)
            continue
        issues = sum(1 for f in findings if f.get("node") in related.get(node_id, {node_id}))
        arrows = sum(1 for e in edges if node_id in (e.get("from"), e.get("to")))
        build.append((-issues, -arrows, node_id))
    return [node_id for *_, node_id in sorted(build)], skip


def recorded_root(given: Path, map_path: Path) -> Path:
    """The root a stamped map recorded, so a later run from another folder still finds the code."""
    try:
        root = json.loads(map_path.read_text()).get("root")
    except (OSError, ValueError):
        return given
    if not root:
        return given
    recorded = (map_path.resolve().parent.parent / root).resolve()
    if recorded != given.resolve():
        print(f"Using the root this map records, {recorded}, not {given}", file=sys.stderr)
    return recorded


def render_page(repo: Path, map_path: Path) -> None:
    """Rewrite map.html beside the map so a browser view never shows an old map."""
    script = Path(__file__).with_name("render_html.py")
    subprocess.run(
        [sys.executable, str(script), str(repo), str(map_path), str(map_path.with_name("map.html"))],
        capture_output=True,
    )


def main() -> int:
    commands = {"check": 4, "stamp": 4, "stale": 4, "merge": 5, "queue": 4}
    if len(sys.argv) < 2 or commands.get(sys.argv[1]) != len(sys.argv):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    command, repo, map_path = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    repo = recorded_root(repo, map_path)

    if command == "merge":
        fragment = json.loads(Path(sys.argv[4]).read_text())
        with open(map_path.parent / ".lock", "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            data = load(map_path)
            if fragment.get("parent") not in {n.get("id") for n in data.get("nodes", [])}:
                print(f"parent {fragment.get('parent')} is not on the map")
                return 1
            merged, notes = merge(repo, data, fragment)
            problems = check(repo, merged)
            for problem in problems:
                print(problem)
            if problems:
                print("Not merged; fix the fragment and run merge again")
                return 1
            temp = map_path.with_suffix(".tmp")
            temp.write_text(json.dumps(stamp(repo, map_path, merged), indent=2) + "\n")
            temp.replace(map_path)
            render_page(repo, map_path)
        print(f"Merged {len(fragment.get('nodes', []))} nodes under {fragment['parent']}")
        for note in notes:
            print(note)
        return 0

    data = load(map_path)

    if command == "check":
        problems = check(repo, data)
        for problem in problems:
            print(problem)
        if problems:
            return 1
        print(f"OK: {len(data.get('nodes', []))} nodes, {len(cites_in(data))} citations")
        return 0

    if command == "stamp":
        map_path.write_text(json.dumps(stamp(repo, map_path, data), indent=2) + "\n")
        render_page(repo, map_path)
        print(f"Stamped at {commit_text(data['built_at_commit'])}, {len(data['files'])} files")
        return 0

    if command == "queue":
        build, skip = queue(data)
        for node_id in build:
            print(f"build {node_id}")
        for node_id in skip:
            print(f"skip {node_id}")
        return 0

    changed = stale(repo, data)
    if not changed:
        print(f"Fresh: no cited file changed since {commit_text(data.get('built_at_commit'))}")
        return 0
    for node, files in changed.items():
        print(f"{node}: {', '.join(files)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
