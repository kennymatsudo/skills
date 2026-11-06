---
name: whimsical-diagram
description: >-
  Draw a software diagram on a Whimsical board: picks the right kind (architecture,
  sequence, state, ER, and more), lays it out to read in one direction with no
  crossing arrows, and has fresh reviewers check it before handing back.
disable-model-invocation: true
---

# Whimsical diagram

You own a board a reader follows in one pass: left to right, top to bottom, no arrow crossing another or doubling back, and every color and line style explained on the board itself. Clear layout outranks completeness; drop a detail before you let it tangle the picture.

Before the first call, load the Whimsical MCP's guide for each kind of diagram you'll add (`how_to` topic `flowchart` or `sequence-diagram`). Prefer its current field names over any written here.

## 1. Settle what to draw

Write down:

- **Question.** The one thing the diagram answers, such as "how does a payout reach the recipient". It becomes the board title.
- **Audience.** Technical, or not.
- **Kind.** Read `references/diagram-types.md` and pick the diagram that answers the question. A request with two questions gets two diagrams on one board.
- **Level.** One zoom level: systems and how they talk, or the parts inside one system. Never both.
- **Contents.** Every box with its type from the table in step 4, and every arrow with its source, target, sync or async, and what it carries.

Take these from the conversation and the code. Ask the user only when the audience or the question is unclear.

Done when the kind is chosen and every box has a type and every arrow a direction and a mode.

## 2. Plan the layout

Whimsical lays out each diagram itself, so the shape of what you hand it decides how clean it looks. For a box-and-arrow diagram (architecture, deployment, process), plan on paper first. For the other kinds, follow their section in `references/diagram-types.md` instead.

- **Shared boxes.** When the same box would appear in several lanes, such as one datastore every path writes to or one job every path branches from, hand-place the board instead, following `references/freeform.md`, so it appears once. Steps 3 to 7 still apply. Skip flowchart lanes and `arrange`.
- **Lanes.** Split the picture into lanes: one for the shared start, then one per branch (such as one per payment method), each its own flowchart. Each lane holds at most 6 boxes and 7 arrows. A lane that needs more splits again, and a board that needs more than 6 lanes is answering more than one question: split it into two boards.
- **Continuity.** Start each branch lane with the box the shared lane ends on, so the reader sees where it picks up.
- **Order.** List each lane's boxes in the order a reader meets them, and pass them to Whimsical in that order. Each box appears once per lane.
- **Arrows start at the actor.** Every arrow starts at the box that does the thing. When our code calls a vendor and saves the result, draw both arrows from our code; an arrow from a vendor into our datastore says the vendor writes to it.
- **Forward only.** Every arrow goes from an earlier box to a later one. A synchronous call's reply is implied by its solid arrow, so never draw it. A callback, such as a webhook, arrives at its own receiver box placed after the sender.
- **Fan-in.** At most 2 arrows end at any box. Draw a shared datastore once per lane, as that lane's last box, and fold extra writes into one arrow.
- **Own trigger, own lane.** A path that starts on its own, such as a poller, a cron job, or an incoming webhook, gets its own lane with the trigger as the first box: "Poller → Venmo API → Payouts DB". Never splice it into the middle of another lane.
- **Side paths.** Alerts and retries go last in the lane's order so they sit off the main line.
- **Short text.** Box labels are 3 words or fewer. Arrow labels are a verb and what it carries, 5 words or fewer ("submit payout, idempotency key"). Detail that doesn't fit goes in your reply, not on the board.

Done when you have listed every lane with its boxes in order and its arrows, and checked each lane against each rule above: no backward arrow, no box with more than 2 incoming, no label over its limit.

## 3. Look up every icon

Pass every component's name to the icon lookup (`how_to` with `domain: {type: "icon", queries: [...]}`), at most 10 names per call. Take a result only when its name plainly is that thing; otherwise use the type's fallback shape from step 4.

Done when every component has a looked-up icon or a fallback shape.

## 4. Build the board

Create the board with `create_file` (`type: "board"`, `title`: the question); `add_board_content` takes no title for flowcharts or sequence diagrams. Add each lane as its own diagram (`add_board_content` with `board_id`; flowcharts with `direction: "left-right"` and nodes in your planned order). Add one text item per lane naming it, such as "Venmo: answer arrives later" (`edit` with the board as `id`, an `operations` entry `{"op": "add", "type": "text", "text": ..., "font_size": "l2", "width": 700, "text_align": "left"}`).

| Type | Color | Fallback shape |
| --- | --- | --- |
| Person or client app | `blue` | `ellipse` |
| Our service, API, or on-demand job | `green` | `rect` |
| Datastore or file store | `purple` | `cylinder` |
| Queue, event bus, or anything that runs on a timer (poller, cron job) | `yellow` | `pill` |
| Outside vendor or system | `orange` | `cloud` |
| Security or auth | `red` | `hexagon` |

- **A palette for the subject.** The named colors above are the fallback. When you can, pick one muted hex color per type that suits the subject (a payments system: pine `#1F6F5C`, ochre `#B7791F`, violet `#5B4B8A`, steel blue `#2F6FAB`, charcoal `#374151`, red `#B42318`) and use the same values on every board of a set.
- **Outline, not fill.** Give every flowchart node `deco: "outline"`. Solid fills make datastores and vendors the heaviest shapes on the board and drown the labels; outlines keep the color coding and match the legend's pale cells.
- **One bold element.** Fill only the single box the diagram is about, such as the one job every lane branches from, and give it its own legend row with a filled cell that says why it stands out. Everything else stays outlined.
- **Even sizes.** Resize clouds and hexagons to 192×120 (`edit` update `width`, `height`) so every lane's center line runs straight.
- **Type scale.** One board heading as a text item at `l3`, lane titles at `l2`, and labels at the default size. Sentence case throughout; no "Step 1" prefixes on lanes that are parallel paths rather than a sequence.
- **Line style.** Solid `arrow` for a synchronous call (the caller waits). `dotted-arrow` for anything asynchronous: a webhook, a queued job, a poll, a scheduled run.
- **Boundaries.** Leave flowchart `groups` out of any board with more than one diagram: `arrange` refuses to move a flowchart that has them. Color and lane titles carry ownership instead. A single-diagram board may use one `silver` `outline` group for a boundary the reader must see.
- **Sequence diagrams.** Whimsical colors participants on its own. Recolor each to its type's color with an `edit` update op on the participant's id (`{"op": "update", "id": ..., "color": ...}`); ids come from `fetch` with `select_kinds: ["sd-actor"]` and `expand_groups: true`. Change anything else in a sequence diagram with `sd_update`, never `x`/`y`.
- **Non-technical audience.** Number the main-path arrows within each lane, starting from 1 ("1 picks Venmo"), and leave side paths unnumbered. Use plain words over class and protocol names.

Done when every lane is on the board with its title text, every box or participant colored by type, and every arrow labeled.

## 5. Add the legend

Add a table (`add_board_content`, `type: "table"`, `data: {"columns": ["Key", "Meaning"], "rows": [...]}`): one row per type actually used, its Key cell an object `{"text": "Datastore", "color": "purple", "deco": "outline"}` in that type's exact color so the cell matches the boxes, then one row per line style actually used, written as words ("Solid line", "Dotted line"). Describe types by role, never by shape or icon name. Arrow characters render as emoji, so leave them out.

Done when every color and line style on the board has a row, and nothing else does.

## 6. Arrange the board

Fetch the board for the ids of each lane title, lane diagram, and the legend. Then place everything with one `arrange` call (`board_id`, `x: 0`, `y: 0`, and this `layout`), nesting each lane's title above its diagram. It works the same for flowcharts and sequence diagrams:

```json
["div", {"layout/style": {"flex-direction": "column", "gap": 48, "align-items": "flex-start"}},
  ["item", {"id": "<board heading>"}],
  ["div", {"layout/style": {"gap": 80, "align-items": "flex-start"}},
    ["div", {"layout/style": {"flex-direction": "column", "gap": 80, "align-items": "flex-start"}},
      ["div", {"layout/style": {"flex-direction": "column", "gap": 16, "align-items": "flex-start"}},
        ["item", {"id": "<lane 1 title>"}], ["item", {"id": "<lane 1 diagram>"}]],
      ["div", {"layout/style": {"flex-direction": "column", "gap": 16, "align-items": "flex-start"}},
        ["item", {"id": "<lane 2 title>"}], ["item", {"id": "<lane 2 diagram>"}]]],
    ["item", {"id": "<legend table>"}]]]
```

When the first lane is much wider than the rest, the legend would float far right of the short lanes. Put the wide lane on its own row, then a row with `width` equal to that lane's width and `justify-content: "space-between"` holding the short lanes' column and the legend.

If `arrange` refuses with a "stored parent" error, a flowchart on the board has groups: rebuild that lane without them.

Done when `arrange` succeeds and the lanes read top to bottom in your planned order.

## 7. Check the snapshot

Fetch the board as an image (`fetch` with `image: true`) and check each item:

- No arrow crosses a box, a label, or another arrow.
- No two arrows overlap or share a path.
- No arrow points backward against the reading direction.
- No label is clipped or covers a box.
- Lanes line up on the left, and the legend sits clear of them.

For each failing lane, go back to step 2 for that lane only: cut an arrow, shorten a label, or split the lane. Then delete its diagram: the id a board fetch lists for a flowchart is its first box, and deleting it removes only that box. Fetch with `scope` set to that id, and delete every shape it lists in one `edit` call (connectors go with their shapes). Add the new diagram and rerun step 6. Change a lane by rebuilding it, never by editing its connectors or labels one at a time. A rebuild gives new ids, so fetch the board again before any further edit.

Done when every item passes on the latest snapshot, or two rounds are spent and the failures are listed.

## 8. Review with fresh eyes

Every board gets this step, whatever its kind. Spawn the two reviewers in `references/review.md` in parallel, one for clarity and one for accuracy. List every finding and decide each: **fix** it when you can confirm it in the snapshot or the source, by going back to step 2 for that lane and rerunning steps 6 and 7; **skip** it only when it is wrong, and write down why. "It would need a backward arrow" is never a reason to skip; it means the path needs its own lane. After the fixes, rerun step 7 on a fresh snapshot. If you rebuilt any lane, also rerun the clarity reviewer on that snapshot; text-only edits need only step 7. Stop after two review rounds.

Done when every finding is marked fixed or skipped with its reason, and step 7 passed on a snapshot taken after your last change.

**Reply:** the board link, one line on what the diagram answers, any detail you left off the board to keep it clear, and each reviewer finding with fixed or skipped and the reason.
