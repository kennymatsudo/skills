#!/usr/bin/env python3
"""Lay out a "what are the parts and what talks to what" board for Whimsical.

Reads a JSON spec (see references/parts-board.md) and prints JSON with two
operation lists for the Whimsical MCP `edit` tool:

  step1: every shape, text and connector, at fixed positions

Run it again with --palette once step1 is on the board, to get the legend:

  step2: the legend table, its key cells in the board's own color keys
  step3: legend fixes that need the table's id (replace <TABLE_ID> after a fetch)

Every part is drawn once, in one row, in the order a request meets them. Between
two neighbors, a call to the right runs on an upper track and a call back to the
left (a webhook, an event) on a lower track, so the two never share a line.
Datastores sit in a row below, each under the part that owns it.

Usage: python3 parts_board.py spec.json > ops.json
       python3 parts_board.py spec.json --palette palette.txt > legend.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from legend import legend_ops  # noqa: E402

PALETTE = {
    "person": "#374151",
    "service": "#1F6F5C",
    "timer": "#B7791F",
    "vendor": "#2F6FAB",
    "store": "#5B4B8A",
    "risk": "#B42318",
}
LEGEND_TEXT = {
    "person": ("Person", "Someone using the product"),
    "service": ("Our service", "Code we run"),
    "timer": ("Job or timer", "Runs on a schedule"),
    "vendor": ("Outside system", "A system we don't own"),
    "store": ("Datastore", "Where data is kept"),
}

RISK_GAP = 48          # space between the risk callout and what it sits above
LEGEND_Y = 160         # top of the legend strip, under the subtitle
ROW_Y = 520            # center y of the parts row
TRACK = 30             # offset of the upper and lower tracks from the row's center line
BOX_W, BOX_H = 200, 120
PERSON_D = 144
STORE_Y = 780          # center y of the store row
STORE_W, STORE_H = 200, 110
MIN_GAP = 230          # gap between neighbors, grown to fit the longest label


def shape(tid, kind, text, x, y, w, h, shape_type="rect", deco="outline"):
    return {"op": "add", "type": "shape", "shape_type": shape_type, "text": text,
            "color": PALETTE[kind], "deco": deco, "x": round(x), "y": round(y),
            "width": round(w), "height": round(h), "temp_id": tid}


def dot(tid, cx, cy):
    """A 3x3 junction in the line color, so a branching line has no seams."""
    return {"op": "add", "type": "shape", "shape_type": "rect", "text": " ", "color": "default",
            "deco": "fill", "x": round(cx - 1), "y": round(cy - 1), "width": 3, "height": 3,
            "temp_id": tid}


def conn(a, b, label=None, dashed=False, arrow=True, color=None):
    op = {"op": "add", "type": "conn", "from_id": a, "to_id": b, "connector_type": "straight"}
    if arrow:
        op["to_endpoint"] = "arrow"
    if label:
        op["text"] = label
    if dashed:
        op["deco"] = "dashes"
    if color:
        op["color"] = op["text_color"] = color
    return op


def text(t, x, y, w, size):
    return {"op": "add", "type": "text", "text": t, "font_size": size, "text_align": "left",
            "x": x, "y": y, "width": w}


def fit_height(t, width, base):
    """Grow a box to fit its wrapped text (about 8 px per character at the default size)."""
    per_line = max(1, int((width - 24) / 8))
    lines = sum(max(1, -(-len(line.replace("*", "")) // per_line)) for line in t.split("\n"))
    return max(base, 22 * lines + 30)


def body(p):
    return f"**{p['label']}**\n{p['role']}" if p.get("role") else f"**{p['label']}**"


def check(spec):
    problems = [f"top level needs '{k}'" for k in ("title", "parts") if k not in spec]
    ids = [p.get("id") for p in spec.get("parts", [])]
    store_ids = [s.get("id") for s in spec.get("stores", [])]
    for i, p in enumerate(spec.get("parts", [])):
        problems += [f"parts[{i}] needs '{k}'" for k in ("id", "label") if k not in p]
        if len(p.get("label", "").split()) > 3:
            problems.append(f"parts[{i}] label '{p['label']}' is over 3 words")
        if p.get("kind", "service") not in ("person", "service", "timer", "vendor"):
            problems.append(f"parts[{i}] kind must be person, service, timer or vendor")
    if sum(1 for p in spec.get("parts", []) if p.get("focus")) > 1:
        problems.append("only one part may set focus")
    if len(ids) > 7:
        problems.append("more than 7 parts in the row: split the board or zoom out a level")
    pairs = set()
    for i, ln in enumerate(spec.get("links", [])):
        problems += [f"links[{i}] needs '{k}'" for k in ("from", "to", "label") if k not in ln]
        a, b = ln.get("from"), ln.get("to")
        if a not in ids or b not in ids:
            problems.append(f"links[{i}] must join two parts (stores go in store_links)")
            continue
        if abs(ids.index(a) - ids.index(b)) != 1:
            problems.append(f"links[{i}] {a} -> {b} skips a part; reorder the row so they are "
                            "neighbors, or route it through the part between them")
        if (a, b) in pairs:
            problems.append(f"links[{i}] repeats {a} -> {b}; fold both into one label")
        pairs.add((a, b))
        if len(ln.get("label", "").split()) > 5:
            problems.append(f"links[{i}] label '{ln['label']}' is over 5 words")
    owners = {}
    for i, s in enumerate(spec.get("stores", [])):
        problems += [f"stores[{i}] needs '{k}'" for k in ("id", "label", "under") if k not in s]
        if s.get("under") not in ids:
            problems.append(f"stores[{i}] under '{s.get('under')}' is not a part")
        owners.setdefault(s.get("under"), []).append(s.get("id"))
    for o, group in owners.items():
        if len(group) > 3:
            problems.append(f"more than 3 stores under '{o}'")
    touched = {sid: set() for sid in store_ids}
    for i, sl in enumerate(spec.get("store_links", [])):
        problems += [f"store_links[{i}] needs '{k}'" for k in ("from", "to", "label") if k not in sl]
        a, sid = sl.get("from"), sl.get("to")
        if sid not in store_ids or a not in ids:
            problems.append(f"store_links[{i}] must run from a part to a store")
            continue
        under = next(s["under"] for s in spec["stores"] if s["id"] == sid)
        if a != under:
            group = owners[under]
            nearest = group[0] if ids.index(a) < ids.index(under) else group[-1]
            if abs(ids.index(a) - ids.index(under)) != 1:
                problems.append(f"store_links[{i}] {a} is not above or beside {sid}: drop this "
                                "arrow and name the reader in the store's role line")
            elif a in owners:
                problems.append(f"store_links[{i}] {a} has its own store below it, so its line "
                                f"to {sid} would cross it")
            elif sid != nearest:
                problems.append(f"store_links[{i}] {sid} must be the store nearest {a} in "
                                f"'{under}''s list, or the line crosses its neighbor")
        touched[sid].add(a)
    for sid, who in touched.items():
        if not who:
            problems.append(f"store '{sid}' has no store_links: draw who writes it and who reads it")
    r = spec.get("risk")
    if r:
        if r.get("part") not in ids:
            problems.append("risk.part must be a part id")
        if r.get("link") and tuple(r["link"]) not in pairs:
            problems.append("risk.link must name a [from, to] pair in links")
    return problems


def build(spec):
    parts, links = spec["parts"], spec.get("links", [])
    ids = [p["id"] for p in parts]
    ops, conns, used, dashed_used = [], [], set(), False
    ops.append(text(spec["title"], 0, 0, 1800, "l3"))
    if spec.get("subtitle"):
        ops.append(text(spec["subtitle"], 0, 82, 1800, "l0"))

    longest = max([len(ln["label"]) for ln in links] + [0])
    gap = max(MIN_GAP, 8 * longest + 60)

    # Parts row, left to right.
    box, x = {}, 0
    for p in parts:
        kind = p.get("kind", "service")
        used.add(kind)
        deco = "fill" if p.get("focus") else "outline"
        if kind == "person":
            w = h = PERSON_D
            ops.append(shape(p["id"], kind, body(p), x, ROW_Y - h / 2, w, h, "ellipse", deco))
        else:
            w = BOX_W
            h = fit_height(body(p), w, BOX_H)
            st = "pill" if kind == "timer" else "rect"
            ops.append(shape(p["id"], kind, body(p), x, ROW_Y - h / 2, w, h, st, deco))
        box[p["id"]] = (x, w, h)
        x += w + gap
    row_right = x - gap

    # Links between neighbors: one direction uses the center line, two use upper and lower tracks.
    risk = spec.get("risk") or {}
    risk_link = tuple(risk.get("link") or ())
    pair_dirs = {}
    for ln in links:
        key = tuple(sorted((ids.index(ln["from"]), ids.index(ln["to"]))))
        pair_dirs.setdefault(key, []).append(ln)
    for (i, j), lns in pair_dirs.items():
        left, right = ids[i], ids[j]
        for ln in lns:
            rightward = ln["from"] == left
            if len(lns) == 1:
                y = ROW_Y
            else:
                y = ROW_Y - TRACK if rightward else ROW_Y + TRACK
            # Anchor each end on the box's side at the track's height, as a fraction of the box.
            ry_left = (y - (ROW_Y - box[left][2] / 2)) / box[left][2]
            ry_right = (y - (ROW_Y - box[right][2] / 2)) / box[right][2]
            red = PALETTE["risk"] if (ln["from"], ln["to"]) == risk_link else None
            c = conn(ln["from"], ln["to"], ln["label"], ln.get("async", False), color=red)
            left_end = {"rx": 1, "ry": round(ry_left, 3), "a": "x"}
            right_end = {"rx": 0, "ry": round(ry_right, 3), "a": "x"}
            c["from_rel"], c["to_rel"] = (left_end, right_end) if rightward else (right_end, left_end)
            conns.append(c)
            dashed_used |= ln.get("async", False)

    # Store row: each store under its owner, joined by a vertical line; a neighbor's line drops
    # from its own center and turns into the store's side.
    stores = spec.get("stores", [])
    store_center, groups = {}, {}
    for s in stores:
        groups.setdefault(s["under"], []).append(s)
    bar_y = (ROW_Y + BOX_H / 2 + STORE_Y - STORE_H / 2) / 2 - 10
    # Every store gets the height of the tallest, on one top line, so the row reads as one row.
    store_h = max([fit_height(body(s), STORE_W, STORE_H) for s in stores] + [STORE_H])
    store_top = STORE_Y - STORE_H / 2
    for owner, group in groups.items():
        ox, ow, _ = box[owner]
        ocx = ox + ow / 2
        step = STORE_W + 60
        first = ocx - step * (len(group) - 1) / 2
        for n, s in enumerate(group):
            used.add("store")
            cx = first + n * step
            ops.append(shape(s["id"], "store", body(s), cx - STORE_W / 2, store_top, STORE_W, store_h,
                             "cylinder"))
            store_center[s["id"]] = (cx, owner)
        if len(group) > 1:  # a small tree: one drop from the owner, a bar, one drop per store
            ops.append(dot(f"bar_{owner}", ocx, bar_y))
            ops.append({"op": "add", "type": "shape", "shape_type": "rect", "text": " ",
                        "color": "default", "deco": "fill", "x": round(first - 1), "y": round(bar_y - 1),
                        "width": round(step * (len(group) - 1) + 3), "height": 2})
            conns.append(conn(owner, f"bar_{owner}", arrow=False))
            for n, s in enumerate(group):
                ops.append(dot(f"bar_{owner}_{n}", first + n * step, bar_y))
    for k, sl in enumerate(spec.get("store_links", [])):
        cx, under = store_center[sl["to"]]
        dashed = sl.get("async", False)
        dashed_used |= dashed
        if sl["from"] == under:
            group = groups[under]
            if len(group) == 1:
                conns.append(conn(sl["from"], sl["to"], sl["label"], dashed))
            else:
                n = [s["id"] for s in group].index(sl["to"])
                conns.append(conn(f"bar_{under}_{n}", sl["to"], sl["label"], dashed))
        else:
            px, pw, _ = box[sl["from"]]
            pcx = px + pw / 2
            side = cx - STORE_W / 2 - 2 if pcx < cx else cx + STORE_W / 2 + 2
            mid = store_top + store_h / 2
            ops.append(dot(f"sl{k}_turn", pcx, mid))
            ops.append(dot(f"sl{k}_end", side, mid))
            conns.append(conn(sl["from"], f"sl{k}_turn", sl["label"], dashed, arrow=False))
            conns.append(conn(f"sl{k}_turn", f"sl{k}_end", None, dashed))

    # One risk callout, straight above the part it is about, joined to it.
    # When it names an arrow, the callout sits centered over that arrow, which turns red with it.
    if risk:
        rw = 260
        rh = fit_height(risk["text"], rw, 60)
        if risk_link:
            a, b = sorted(risk_link, key=ids.index)
            cx = (box[a][0] + box[a][1] + box[b][0]) / 2
            top = ROW_Y - BOX_H / 2
        else:
            ox, ow, oh = box[risk["part"]]
            cx = ox + ow / 2
            top = ROW_Y - oh / 2
        ops.append({"op": "add", "type": "shape", "shape_type": "rect", "text": risk["text"],
                    "temp_id": "risk", "color": PALETTE["risk"], "deco": "outline",
                    "x": round(cx - rw / 2), "y": round(top - RISK_GAP - rh), "width": rw,
                    "height": round(rh)})
        if not risk_link:
            conns.append(conn("risk", risk["part"], None, True, arrow=False, color=PALETTE["risk"]))

    ops += conns  # after every shape, so each temp_id exists before a connector names it

    # Legend strip under the board: one column per key, colored key cells in row 1, meanings in row 2.
    keys, meanings = [], []
    focus = next((p for p in parts if p.get("focus")), None)
    if focus:
        k = focus.get("kind", "service")
        keys.append({"text": focus["label"], "color": PALETTE[k], "deco": "fill", "bold": True})
        meanings.append(spec.get("focus_meaning", "What this design is about"))
    for kind in ["person", "service", "timer", "vendor", "store"]:
        if kind in used:
            name, meaning = LEGEND_TEXT[kind]
            keys.append({"text": name, "color": PALETTE[kind], "deco": "outline", "bold": True})
            meanings.append(meaning)
    keys.append({"text": "Solid line", "bold": True})
    meanings.append("Caller waits for the answer")
    if dashed_used:
        keys.append({"text": "Dashed line", "bold": True})
        meanings.append("No wait: webhook, event, or later")
    if risk:
        keys.append({"text": "Risk", "color": PALETTE["risk"], "deco": "outline", "bold": True})
        meanings.append("Known gap to discuss in review")
    legend = {"keys": keys, "meanings": meanings, "y": LEGEND_Y,
              "width": max(row_right, 180 * len(keys))}
    return ops, legend


def main():
    with open(sys.argv[1]) as f:
        spec = json.load(f)
    problems = check(spec)
    if problems:
        sys.exit("spec problems (see references/parts-board.md):\n  " + "\n  ".join(problems))
    ops, legend = build(spec)
    if "--palette" in sys.argv:
        with open(sys.argv[sys.argv.index("--palette") + 1]) as f:
            json.dump(legend_ops(legend, f.read()), sys.stdout, indent=1)
    else:
        json.dump({"step1": ops}, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
