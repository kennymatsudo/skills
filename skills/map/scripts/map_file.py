#!/usr/bin/env python3
"""Check, stamp, and diff a map file against the repo it describes.

Usage:
  map_file.py check <repo-root> <map.json>   validate structure and every citation
  map_file.py stamp <repo-root> <map.json>   record the commit and a hash of each cited file
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
import re
import subprocess
import sys
from pathlib import Path

CITE = re.compile(r"^([\w./-]+):(\d+)(?:-(\d+))?$")
KINDS = {"service", "datastore", "queue", "external", "group", "component"}
EVIDENCE = {"config", "client-call", "route", "topic", "inferred"}
SEVERITY = {"bug", "risk", "gap"}
MAX_CHILDREN = 20
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
    """Findings and unknowns that repeat an earlier one on the same box or a box above or below it."""
    problems = []
    related = lineage(data.get("nodes", []))
    kept: list[dict] = []
    for item in data.get("findings", []):
        family = related.get(item.get("node"), {item.get("node")})
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
    problems += shared_code(nodes)

    children: dict[str | None, int] = {}
    for node in nodes:
        children[node.get("parent")] = children.get(node.get("parent"), 0) + 1
    for parent, count in children.items():
        if count > MAX_CHILDREN:
            where = parent or "the top level"
            problems.append(f"{where}: {count} boxes, group them to {MAX_CHILDREN} or fewer")

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


def stamp(repo: Path, data: dict) -> dict:
    files = sorted({f for _, cite in cites_in(data) if (f := cite_file(cite))})
    data["built_at_commit"] = head_commit(repo)
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


def merge(repo: Path, data: dict, fragment: dict) -> dict:
    """Swap the fragment's parent's old children for the fragment's entries."""
    parent = fragment["parent"]
    # Everything below the parent goes, grandchildren too, so a rebuild leaves no orphans.
    family = lineage(data.get("nodes", [])).get(parent, {parent})
    old = {n["id"] for n in data.get("nodes", []) if n["id"] in family and n["id"] != parent
           and parent in ancestors_of(data, n["id"])}
    new = {n["id"] for n in fragment.get("nodes", [])}
    gone = old | new

    def keep(items: list, *fields: str) -> list:
        return [i for i in items if not any(i.get(f) in gone for f in fields)]

    data["nodes"] = keep(data.get("nodes", []), "id") + fragment.get("nodes", [])
    data["edges"] = keep(data.get("edges", []), "from", "to") + fragment.get("edges", [])
    data["findings"] = keep(data.get("findings", []), "node") + fragment.get("findings", [])
    data["unknowns"] = keep(data.get("unknowns", []), "node") + fragment.get("unknowns", [])
    paths = [p for p in data.get("paths", []) if p.get("node") not in gone]
    if fragment.get("paths"):
        paths = [p for p in paths if p.get("node") != parent]
    data["paths"] = paths + fragment.get("paths", [])
    # A rebuild may restate a note it already made about the parent itself.
    for field in ("findings", "unknowns"):
        unique = {}
        for item in data[field]:
            unique.setdefault((item.get("node"), item.get("text")), item)
        data[field] = list(unique.values())
    for node in data["nodes"]:
        if node.get("id") == parent:
            node["loaded"] = True
    return data


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

    if command == "merge":
        fragment = json.loads(Path(sys.argv[4]).read_text())
        with open(map_path.parent / ".lock", "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            data = load(map_path)
            if fragment.get("parent") not in {n.get("id") for n in data.get("nodes", [])}:
                print(f"parent {fragment.get('parent')} is not on the map")
                return 1
            merged = merge(repo, data, fragment)
            problems = check(repo, merged)
            for problem in problems:
                print(problem)
            if problems:
                print("Not merged; fix the fragment and run merge again")
                return 1
            temp = map_path.with_suffix(".tmp")
            temp.write_text(json.dumps(stamp(repo, merged), indent=2) + "\n")
            temp.replace(map_path)
            render_page(repo, map_path)
        print(f"Merged {len(fragment.get('nodes', []))} nodes under {fragment['parent']}")
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
        map_path.write_text(json.dumps(stamp(repo, data), indent=2) + "\n")
        render_page(repo, map_path)
        print(f"Stamped at {data['built_at_commit']}, {len(data['files'])} files")
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
        print(f"Fresh: no cited file changed since {data.get('built_at_commit')}")
        return 0
    for node, files in changed.items():
        print(f"{node}: {', '.join(files)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
