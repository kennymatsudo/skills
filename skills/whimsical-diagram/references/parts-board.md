# Parts board

Use this layout when the question is what the parts of a system are and what talks to what. `scripts/parts_board.py` places every part once, so no box repeats and no line crosses another:

- one row of parts, left to right in the order a request meets them
- between two neighbors, the call to the right on an upper track and the answer coming back (a webhook, an event) on a lower track
- datastores in a row below, each under the part that owns it
- one red risk callout above the part or arrow it's about
- a legend strip under the subtitle, where it is the first thing read

It shows structure, not order: no step numbers, no failure paths. Put one request step by step on its own sequence board, and name that board in this one's subtitle.

## Write the spec

Save it to a scratch file. Part labels are 3 words or fewer, with a short `role` for the second line. Link labels are 5 words or fewer.

```json
{
  "title": "What are the parts of order fulfillment?",
  "subtitle": "Proposed design, for review. One order step by step is on the board \"How an order ships\".",
  "parts": [
    {"id": "web", "label": "Storefront", "role": "customer checks out", "kind": "person"},
    {"id": "orders", "label": "Orders API", "role": "owns orders", "focus": true},
    {"id": "carrier", "label": "Carrier API", "role": "labels, tracking", "kind": "vendor"}
  ],
  "focus_meaning": "The service this design adds",
  "links": [
    {"from": "web", "to": "orders", "label": "place order"},
    {"from": "orders", "to": "carrier", "label": "buy label"},
    {"from": "carrier", "to": "orders", "label": "webhook: delivered", "async": true}
  ],
  "stores": [{"id": "db", "label": "Orders DB", "role": "orders, shipments", "under": "orders"}],
  "store_links": [{"from": "orders", "to": "db", "label": "create, update"}],
  "risk": {"part": "carrier", "text": "No retry on a missed webhook: an order can stay shipped forever",
           "link": ["carrier", "orders"]}
}
```

- **`kind`** is one of `person`, `service`, `timer` or `vendor`. `focus` fills the one part the design is about and gives it its own legend row.
- **`links`** join neighbors only. When two parts that talk aren't neighbors, reorder the row; when no order works, the board is answering more than one question.
- **`stores`** may be up to 3 per part. `store_links` start at the actor: the part that writes or reads. A neighbor may also read a store, if it has no store of its own and the store is the one nearest it. Any other reader goes on the store's `role` line ("App writes, Support reads").
- **`risk`** names the part it is about. Its optional `link` names an arrow instead: the arrow turns red and the callout sits centered above it.

The script refuses a spec that breaks these rules and says how to fix it.

## Draw it

1. Run `python3 <skill dir>/scripts/parts_board.py spec.json > ops.json`.
2. Create the board with `create_file`, then send `step1` as one `edit` call's `operations`.
3. Fetch the board with `detail: "detailed"` and `limit: 1`, and save the line that starts `Palette:` to a scratch file. Table cells refuse hex colors and take these `custom-` keys instead.
4. Run the script again with `--palette <that file>`. Send `step2` as one `edit` call.
5. Fetch the board with `select_kinds: ["table"]` for the legend's id. Replace `<TABLE_ID>` in `step3` and send it as a third `edit` call. Whimsical ignores a new table's position and its hidden header, and this step fixes both.
6. Go on to SKILL.md step 7.

To change the board, edit the spec and redraw it on a fresh board. Connectors are anchored to the sides of shapes at fixed heights, so moving a shape by hand bends them.
