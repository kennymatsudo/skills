#!/usr/bin/env python3
"""Lay out a "pipeline that branches into a shared store" board for Whimsical.

Reads a JSON spec (see references/branch-board.md) and prints JSON with two
operation lists for the Whimsical MCP `edit` tool:

  step1: every shape, text, connector and the legend table, at fixed positions
  step2: legend fixes that need the table's id (replace <TABLE_ID> after a fetch)

Usage: python3 branch_board.py spec.json > ops.json
"""
import json
import sys

PALETTE = {
    "person": "#374151",
    "service": "#1F6F5C",
    "hub": "#B7791F",
    "timer": "#B7791F",
    "vendor": "#2F6FAB",
    "store": "#5B4B8A",
    "risk": "#B42318",
}
LEGEND_TEXT = {
    "person": ("Person", "Someone using the product"),
    "service": ("Our service", "Code we run"),
    "store": ("Datastore", "Dashed band: one table; boxes show its row's states"),
    "hub": ("Branch point", "The one place that branches"),
    "timer": ("Job or timer", "Runs on a schedule"),
    "vendor": ("Outside vendor", "A system we don't own"),
}

TOP_Y = 222            # center y of the top row
BAR_Y = 329            # y of the branch bar
EXEC_Y = 520           # center y of the executor row
BAND_Y, BAND_H = 720, 190
REC_Y, REC_H = 775, 80
BOX_W, BOX_H = 192, 96
CLOUD_W, CLOUD_H = 192, 120
TOP_GAP = 186          # gap between top-row boxes, room for a label
VENDOR_GAP = 248       # exec to vendor, room for a label and a risk box
COL_STEP = 700         # center-to-center distance between branch columns


def shape(tid, kind, text, x, y, w, h, shape_type="rect", deco="outline"):
    return {"op": "add", "type": "shape", "shape_type": shape_type, "text": text,
            "color": PALETTE[kind], "deco": deco, "x": round(x), "y": round(y),
            "width": w, "height": h, "temp_id": tid}


def conn(a, b, label=None, dashed=False, arrow=True):
    op = {"op": "add", "type": "conn", "from_id": a, "to_id": b, "connector_type": "straight"}
    if arrow:
        op["to_endpoint"] = "arrow"
    if label:
        op["text"] = label
    if dashed:
        op["deco"] = "dashes"
    return op


def text(t, x, y, w, size, tid=None):
    op = {"op": "add", "type": "text", "text": t, "font_size": size, "text_align": "left",
          "x": x, "y": y, "width": w}
    if tid:
        op["temp_id"] = tid
    return op


def fit_height(t, width, base):
    """Grow a box to fit its wrapped text (about 8 px per character at the default size)."""
    per_line = max(1, int((width - 24) / 8))
    lines = sum(max(1, -(-len(line.replace("*", "")) // per_line)) for line in t.split("\n"))
    return max(base, 22 * lines + 30)


def record_text(r):
    return f"**{r['title']}**\n{r['state']}" if r.get("state") else f"**{r['title']}**"


def build(spec):
    ops, links, used, risky, dashed_used = [], [], set(), False, False
    # A webhook stack (vendor, receiver, write) needs more height above the store band, or its
    # dashed hop reads as solid and the write's label lands on the band's edge.
    shift = 120 if any(b.get("call", {}).get("callback") for b in spec.get("branches", [])) else 0
    band_y, rec_y, legend_y = BAND_Y + shift, REC_Y + shift, 960 + shift
    ops.append(text(spec["title"], 0, 0, 1800, "l3"))
    if spec.get("subtitle"):
        ops.append(text(spec["subtitle"], 0, 82, 1800, "l0"))

    # Top row: start nodes left to right, then the hub.
    start = spec["start"]
    edges = spec.get("start_edges", [])
    sw = spec.get("start_write")
    numbered = bool(sw)  # create and enqueue leave one box, so their order needs numbers
    step = 0
    # Leave the band's left end free for its name: the first record must start at x >= 300.
    x, offset = 0, 0
    if sw:
        probe = 0
        for node in start:
            w = 144 if node.get("kind") == "person" else BOX_W
            if node["id"] == sw["from"]:
                offset = max(0, 300 - probe - (w - BOX_W) / 2)
                break
            probe += w + TOP_GAP
    x, centers = offset, {}
    for node in start:
        kind = node.get("kind", "service")
        used.add(kind)
        if kind == "person":
            ops.append(shape(node["id"], kind, node["label"], x, TOP_Y - 72, 144, 144, "ellipse"))
            centers[node["id"]] = x + 72
            x += 144 + TOP_GAP
        else:
            ops.append(shape(node["id"], kind, node["label"], x, TOP_Y - BOX_H / 2, BOX_W, BOX_H))
            centers[node["id"]] = x + BOX_W / 2
            x += BOX_W + TOP_GAP
    last_right = x - TOP_GAP

    def label(t):
        nonlocal step
        if not numbered:
            return t
        step += 1
        return f"{step}  {t}"

    for e in edges:
        links.append(conn(e["from"], e["to"], label(e["label"]), e.get("async", False)))
        dashed_used |= e.get("async", False)

    hub = spec["hub"]
    branches = spec["branches"]
    first_rec_center = centers[sw["from"]] if sw else None
    cx0 = (first_rec_center + 230) if sw else last_right + 200
    cols = [cx0 + i * COL_STEP for i in range(len(branches))]
    hub_cx = sum(cols) / len(cols)
    if hub_cx - BOX_W / 2 < last_right + 300:  # keep room for the hub's incoming label
        shift = last_right + 300 - (hub_cx - BOX_W / 2)
        cols = [c + shift for c in cols]
        hub_cx += shift
    used.add("hub")

    if sw:
        links.append(conn(sw["from"], "rec_start", label(sw["label"])))
    links.append(conn(hub["from"], "hub", label(hub["edge_label"]), hub.get("async", True)))
    dashed_used |= hub.get("async", True)
    ops.append(shape("hub", "hub", hub["label"], hub_cx - BOX_W / 2, TOP_Y - BOX_H / 2,
                     BOX_W, BOX_H, "pill", "fill"))

    # Branch bar: a thin rect plus junction squares, so the tree has no seams.
    ops.append({"op": "add", "type": "shape", "shape_type": "rect", "text": " ", "color": "default",
                "deco": "fill", "x": round(cols[0] - 2), "y": BAR_Y, "width": round(cols[-1] - cols[0] + 4),
                "height": 3})
    for i, c in enumerate(cols):
        ops.append({"op": "add", "type": "shape", "shape_type": "rect", "text": " ", "color": "default",
                    "deco": "fill", "x": round(c - 1), "y": BAR_Y, "width": 3, "height": 3,
                    "temp_id": f"j{i}"})
    hub_j = next((f"j{i}" for i, c in enumerate(cols) if abs(c - hub_cx) < 1), None)
    if hub_j is None:
        ops.append({"op": "add", "type": "shape", "shape_type": "rect", "text": " ", "color": "default",
                    "deco": "fill", "x": round(hub_cx - 1), "y": BAR_Y, "width": 3, "height": 3,
                    "temp_id": "jhub"})
        hub_j = "jhub"
    links.append(conn("hub", hub_j, arrow=False))

    rec_centers = []
    if sw:
        rec_centers.append(("rec_start", first_rec_center, {"title": sw["record_title"], "state": sw.get("record_state", "")}))
    right_edge = 0
    for i, (b, c) in enumerate(zip(branches, cols)):
        eid = f"ex{i}"
        body = b["label"] + (f"\n{b['note']}" if b.get("note") else "")
        kind = b.get("kind", "service")
        used.add(kind)
        eh = fit_height(body, BOX_W, BOX_H)
        ops.append(shape(eid, kind, body, c - BOX_W / 2, EXEC_Y - eh / 2, BOX_W, eh))
        base = step  # each branch numbers its own steps from the same base
        tag = "abcdefgh"[i] if len(branches) > 1 else ""  # parallel branches: 4a, 4b, 4c
        num = (lambda k, t: f"{base + k}{tag}  {t}") if numbered else (lambda k, t: t)
        links.append(conn(f"j{i}", eid, num(1, b["condition"])))
        right_edge = max(right_edge, c + BOX_W / 2)
        call = b.get("call")
        if call:
            vx = c + BOX_W / 2 + VENDOR_GAP
            ops.append(shape(f"v{i}", "vendor", call["label"], vx, EXEC_Y - CLOUD_H / 2,
                             CLOUD_W, CLOUD_H, "cloud"))
            links.append(conn(eid, f"v{i}", num(2, call["edge"]), call.get("async", False)))
            dashed_used |= call.get("async", False)
            used.add("vendor")
            right_edge = max(right_edge, vx + CLOUD_W)
        if b.get("risk"):
            risky = True
            if call:  # the risky call itself turns red, matching the box under it
                for lk in links:
                    if lk.get("from_id") == eid and lk.get("to_id") == f"v{i}":
                        lk["color"] = lk["text_color"] = PALETTE["risk"]
            ops.append({"op": "add", "type": "shape", "shape_type": "rect", "text": b["risk"], "temp_id": f"risk{i}",
                        "color": PALETTE["risk"], "deco": "outline",
                        "x": round(c + BOX_W / 2 + 10), "y": EXEC_Y + 26, "width": 228,
                        "height": fit_height(b["risk"], 228, 60)})
        w = b.get("write")
        if w:
            rec_centers.append((f"r{i}", c, {"title": w["record_title"], "state": w.get("record_state", "")}))
            links.append(conn(eid, f"r{i}", num(3 if call else 2, w["edge"])))
            cb = call and call.get("callback")
            if cb:  # vendor -> our receiver -> end-state record, straight down the vendor column
                vcx = c + BOX_W / 2 + VENDOR_GAP + CLOUD_W / 2
                recv = call.get("receiver", "Webhook endpoint")
                # A short dashed hop into the receiver and a long solid write out of it, so the
                # two lines don't read as one dashed line.
                ops.append(shape(f"wr{i}", "service", recv, vcx - BOX_W / 2, EXEC_Y + CLOUD_H / 2 + 80,
                                 BOX_W, 52))
                end = call.get("end_state", {"title": "completed or failed", "state": "from the webhook"})
                rec_centers.append((f"re{i}", vcx, end))
                links.append({"op": "add", "type": "conn", "from_id": f"v{i}", "to_id": f"wr{i}",
                              "connector_type": "straight", "deco": "dashes", "to_endpoint": "arrow",
                              "text": num(4, cb)})
                links.append(conn(f"wr{i}", f"re{i}", num(5, "update")))
                dashed_used = True

    # Shared store band with one record box per writer, aligned under it.
    store = spec["store"]
    used.add("store")
    band_right = max(right_edge, max(c for _, c, _ in rec_centers) + 130) + 40
    ops.insert(0, {"op": "add", "type": "shape", "shape_type": "rect", "text": " ",
                   "color": PALETTE["store"], "deco": "dashes", "x": 0, "y": band_y,
                   "width": round(band_right), "height": BAND_H})
    ops.append(text(store["name"], 24, band_y + 75, 230, "l1"))
    if store.get("caption"):
        ops.append(text(store["caption"], 24, band_y + 116, 250, "m"))
    if store.get("lifecycle"):
        ops.append(text("Lifecycle: " + store["lifecycle"], 300, band_y + BAND_H - 40,
                        round(band_right - 340), "m"))
    for rid, c, r in rec_centers:
        t = record_text(r)
        w = 220 if max(len(line) for line in t.split("\n")) > 22 else BOX_W
        h = fit_height(t, w, REC_H)
        ops.append(shape(rid, "store", t, c - w / 2, rec_y + REC_H / 2 - h / 2, w, h))

    content_right = band_right
    for k, rd in enumerate(spec.get("readers", [])):
        rid = f"r{rd['branch']}"
        y = rec_y + REC_H / 2 - CLOUD_H / 2
        x = band_right + 340
        ops.append(shape(f"rd{k}", "vendor", rd["label"], x, y, CLOUD_W, CLOUD_H, "cloud"))
        links.append(conn(f"rd{k}", rid, rd["edge"], True))
        dashed_used = True
        used.add("vendor")
        content_right = max(content_right, x + CLOUD_W)

    ops += links  # after every shape, so each temp_id exists before a connector names it

    # Legend: one column per key, colored key cells in row 1, meanings in row 2.
    keys, meanings = [], []
    for kind in ["person", "service", "store", "hub", "timer", "vendor"]:
        if kind in used:
            name, meaning = LEGEND_TEXT[kind]
            if kind == "hub":
                meaning = spec.get("hub_meaning", meaning)
            keys.append({"text": name, "color": PALETTE[kind],
                         "deco": "fill" if kind == "hub" else "outline", "bold": True})
            meanings.append(meaning)
    keys.append({"text": "Solid line", "bold": True})
    meanings.append("Caller waits for the answer")
    if dashed_used:
        keys.append({"text": "Dashed line", "bold": True})
        meanings.append("No wait: queued, scheduled or later")
    if risky:
        keys.append({"text": "Risk", "color": PALETTE["risk"], "deco": "outline", "bold": True})
        meanings.append("Red: known gap to discuss in review")
    n = len(keys)
    ops.append({"op": "add", "type": "table", "x": 0, "y": legend_y, "head_style": "hide",
                "columns": [{"header": "-", "width": 200} for _ in range(n)],
                "rows": [keys, meanings]})
    widths = [int(content_right // n)] * n
    widths[-1] += int(content_right) - sum(widths)
    step2 = [
        {"op": "update", "id": "<TABLE_ID>", "type": "table", "widths": widths},
        {"op": "update", "id": "<TABLE_ID>", "x": 0, "y": legend_y},
        {"op": "remove_rows", "id": "<TABLE_ID>", "indices": [0]},
    ]
    return {"step1": ops, "step2": step2}


def main():
    with open(sys.argv[1]) as f:
        spec = json.load(f)
    problems = [f"top level needs '{k}'" for k in ("title", "start", "hub", "branches", "store")
                if k not in spec]
    for i, b in enumerate(spec.get("branches", [])):
        problems += [f"branches[{i}] needs '{k}'" for k in ("condition", "label") if k not in b]
        if "call" in b:
            problems += [f"branches[{i}].call needs '{k}'" for k in ("label", "edge") if k not in b["call"]]
        if "write" in b:
            problems += [f"branches[{i}].write needs '{k}'" for k in ("edge", "record_title")
                         if k not in b["write"]]
        if b.get("call", {}).get("callback") and "write" not in b:
            problems.append(f"branches[{i}] has a callback but no write for it to land in")
        if "call" in b:  # an outside call can fail, so its outcome boxes must say how
            outcomes = json.dumps([b.get("write", {}), b["call"].get("end_state", {})]).lower()
            if "fail" not in outcomes:
                problems.append(f"branches[{i}] calls {b['call'].get('label', 'a vendor')} but no record "
                                "names its failure state (e.g. record_title 'shipped or failed')")
    for k, rd in enumerate(spec.get("readers", [])):
        problems += [f"readers[{k}] needs '{f}'" for f in ("branch", "label", "edge") if f not in rd]
    if problems:
        sys.exit("spec problems (see references/branch-board.md):\n  " + "\n  ".join(problems))
    json.dump(build(spec), sys.stdout, indent=1)


if __name__ == "__main__":
    main()
