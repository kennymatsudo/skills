# Branch board

Use this layout when a request comes in, one component branches it by type into parallel paths, and the paths write to one shared store. Payout execution, order fulfillment by carrier, and notifications by channel all have this shape. `scripts/branch_board.py` turns a short spec into every position, so the board comes out the same way each time:

- a top row running left to right into one filled branch point
- a seamless branch bar dropping into evenly spaced columns
- each column's outside call to its right
- one dashed band for the shared store, with one record box under each writer
- a full-width legend strip

## Write the spec

Save it to a scratch file. Every label follows SKILL.md's rules: boxes 3 words or fewer, plus an optional second-line `note`, and arrows 5 words or fewer.

```json
{
  "title": "How a payout gets executed",
  "subtitle": "Proposed design, draft for review. ACH completion at 8am ET is on the next board.",
  "start": [
    {"id": "rec", "label": "Recipient", "kind": "person"},
    {"id": "api", "label": "Redemption API", "kind": "service"}
  ],
  "start_edges": [{"from": "rec", "to": "api", "label": "redeem, pick product"}],
  "start_write": {"from": "api", "label": "create, idempotency key",
                  "record_title": "pending", "record_state": "new payouts row"},
  "hub": {"label": "ExecutePayoutJob", "from": "api", "edge_label": "enqueue payout", "async": true},
  "hub_meaning": "The one place that branches by payout type",
  "branches": [
    {"condition": "type = card", "label": "Card executor", "note": "retries 3, then alerts",
     "call": {"label": "Card vendor", "edge": "purchase card"},
     "risk": "No idempotency key:\na retry can pay twice",
     "write": {"edge": "log attempt, then update", "record_title": "completed or failed",
               "record_state": "+ payout_attempts row"}},
    {"condition": "type = venmo", "label": "Venmo executor", "note": "retries with same key",
     "call": {"label": "Venmo API", "edge": "submit, idempotency key",
              "callback": "webhook",
              "end_state": {"title": "completed or failed", "state": "set by the webhook"}},
     "write": {"edge": "update", "record_title": "submitted", "record_state": "request_id"}},
    {"condition": "type = ach", "label": "ACH executor", "note": "no external call",
     "write": {"edge": "update, encrypted", "record_title": "submitted", "record_state": "bank details, due time"}}
  ],
  "store": {"name": "Payouts DB", "caption": "One row per payout; boxes show its state",
            "lifecycle": "pending, then submitted, then completed or failed"},
  "readers": [{"branch": 2, "label": "ACH batch system", "edge": "reads new rows at 6pm ET"}]
}
```

- **`kind`** is one of `person`, `service`, `timer` or `vendor`, and sets the color and shape.
- **`start_write`** is the first write, made before the branch. When it's present, every main-path arrow is numbered, through the branch, the call and the write. Parallel branches share numbers, because a create and an enqueue leaving the same box need an order and the reader should be able to follow it to the end.
- **Record boxes** sit in the shared store. Title each with every state that path can leave the row in, failures included ("shipped or failed", "submitted, then delivered or failed"), and put what it writes on the second line. Three boxes all titled "payouts row" read as three records, while states read as one row moving through them. A path drawn with only its success state looks unfinished to a reviewer.
- **`call.callback`** is optional. For a vendor that answers later, such as by webhook, give the label ("webhook: delivered or failed"). It draws the vendor calling our receiver box (`call.receiver`, default "Webhook endpoint") straight below it, and the receiver writing a second record box below that for the end state (`call.end_state`, a `title` and a `state`). Every line is straight, and "submitted" visibly leads to an outcome. Leave out any async completion you can't draw this way, and say in the subtitle where it is shown.
- **`risk`** is optional. It turns that branch's outside call red, puts a red box with the consequence under it, and adds a Risk row to the legend. Red is used for nothing else.
- **`readers`** are outside systems that read a branch's record. Their arrow starts at the reader, because the reader is the actor, and its label is an active verb ("reads new rows at 6pm ET").
- **`store.lifecycle`** writes the row's whole lifecycle along the bottom of the band ("pending, then submitted, then completed or failed"), so separate state boxes read as one row.

## Draw it

1. Run `python3 <skill dir>/scripts/branch_board.py spec.json > ops.json`.
2. Create the board with `create_file`, then send `step1` as one `edit` call's `operations`.
3. Fetch the board with `detail: "detailed"` and `limit: 1`, and save the line that starts `Palette:` to a scratch file. Table cells refuse hex colors and take these `custom-` keys instead.
4. Run the script again with `--palette <that file>`. Send `step2` as one `edit` call.
5. Fetch the board with `select_kinds: ["table"]` for the legend's id. Replace `<TABLE_ID>` in `step3` and send it as a third `edit` call. Whimsical ignores a new table's position and its hidden header, and this step fixes both.
6. Go on to SKILL.md step 7.

To change the board, edit the spec and redraw it on a fresh board. Never edit `ops.json` or the drawn labels afterward, not even when a reviewer misreads something. Step numbers like 4a, 4b and 4c mark parallel branches, and stripping them is what made earlier test boards read as unfinished. When a reviewer misreads the board, fix it through the spec's wording. Connectors don't follow shapes that move, so nudging pieces by hand undoes the layout.
