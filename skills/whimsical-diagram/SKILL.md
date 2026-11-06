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
- **Kind.** Read `references/diagram-types.md` and pick the diagram that answers the question. One board answers one question. A request with two questions, such as "what are the parts" and "how does one request move through them", gets one board each, and each board's subtitle names the other.
- **Level.** One zoom level: systems and how they talk, or the parts inside one system. Never both.
- **Contents.** Every box with its type from the table in step 4, and every arrow with its source, target, sync or async, and what it carries.

Take these from the conversation and the code. Ask the user only when the audience or the question is unclear.

Done when the kind is chosen and every box has a type and every arrow a direction and a mode.

## 2. Plan the layout

Whimsical lays out each diagram itself, so the shape of what you hand it decides how clean it looks. For a box-and-arrow diagram (architecture, deployment, process), plan on paper first. For the other kinds, follow their section in `references/diagram-types.md` instead.

- **Parts board.** When the question is what the parts are and what talks to what, follow `references/parts-board.md` and draw it with its script, so each part appears once. Skip steps 3 to 6 and resume at step 7.
- **Branch board.** When a request comes in, one component branches it by type into parallel paths, and the paths write to one shared store, follow `references/branch-board.md` and draw it with its script. That layout scored highest of any tried. Skip steps 3 to 6 and resume at step 7.
- **Shared boxes.** When the same box would appear in several lanes in any other shape, never draw it again with a marker such as a dashed border; hand-place the board instead, following `references/freeform.md`, so it appears once. Steps 3 to 7 still apply. Skip flowchart lanes and `arrange`.
- **Lanes.** Split the picture into lanes: one for the shared start, then one per branch (such as one per payment method), each its own flowchart. Each lane holds at most 6 boxes and 7 arrows. A lane that needs more splits again, and a board that needs more than 6 lanes is answering more than one question: split it into two boards.
- **Continuity.** Start each branch lane with the box the shared lane ends on, so the reader sees where it picks up.
- **Order.** List each lane's boxes in the order a reader meets them, and pass them to Whimsical in that order. Each box appears once per lane.
- **Arrows start at the actor.** Every arrow starts at the box that does the thing. When our code calls a vendor and saves the result, draw both arrows from our code; an arrow from a vendor into our datastore says the vendor writes to it.
- **Forward only.** Every arrow goes from an earlier box to a later one. A synchronous call's reply is implied by its solid arrow, so never draw it. A callback, such as a webhook, arrives at its own receiver box placed after the sender.
- **Fan-in.** At most 2 arrows end at any box. Draw a shared datastore once per lane, as that lane's last box, and fold extra writes into one arrow.
- **Own trigger, own lane.** A path that starts on its own, such as a poller, a cron job, or an incoming webhook, gets its own lane with the trigger as the first box: "Poller → Venmo API → Payouts DB". Never splice it into the middle of another lane.
- **Side paths.** Alerts and retries go last in the lane's order so they sit off the main line.
- **Say what a reviewer would ask.**
  - Number the steps whenever position alone doesn't give their order, such as two arrows leaving one box.
  - Label each branch arrow with its condition ("type = card").
  - Use one verb for one kind of action across all paths and diagrams ("update", not "record", "save" and "update"; "dedupe", not "once per key", "unless seen" and "dedupe").
  - Title each record box with the state it leaves the row in, so several boxes read as one row moving through states.
  - Finish every story. Each request ends at a visible reply or end state, and every call that can fail shows its failed state on the board. A subtitle line like "failures not shown" doesn't count unless it names where they are shown. Each state that isn't final shows what moves it on (a callback, a reader, a job), or the subtitle says where that's shown. Reviewers mark a diagram down first for a path that just stops.
- **Behavior is a second line.** Retries and alerts go on the box's second line, not in boxes of their own. Sibling boxes get parallel second lines ("retries 3, then alerts", "retries with same key", "no external call").
- **One risk callout.** Put the design's known gap in one red outlined box right next to the arrow or box it's about (on a sequence diagram, a red line under its title; see step 6), and add a Risk key to the legend. It names something drawn on the board; a gap in a part the board doesn't show belongs on that part's board. Red means nothing else on the board.
- **Cover every stage.** When the source names the stages of what the question covers ("five moments", "three phases"), every one of them is drawn, and the diagram titles use the source's stage names in its order. Pointing at the source is only for detail below a stage, never for a whole stage.
- **Subtitle.** Under the title, one `l0` line giving scope, status, and where anything left out is shown ("Proposed design, draft for review. Retries and refunds are in the error-handling doc."). If nothing in scope is left out, say so ("Shows every path in scope."). Saying something is "not drawn" without saying where it is fails review. Write any reference to another board last, once every board exists, using its exact title. Keep it to one sentence of plain words: no list of code identifiers or status codes, and no behavior, which belongs in a diagram.
- **Short text.** Box labels are 3 words or fewer. Arrow labels are a verb and what it carries, 5 words or fewer ("submit payout, idempotency key"). Detail that doesn't fit goes in your reply, not on the board.
- **Gloss outside names.** A name that appears only in a label or callout, not as a box or participant, carries a two-word gloss the first time ("Ada, the old bot").
- **Rules go in the diagram.** A rule that changes what happens next (a retry, a block, a dedupe, a timeout) is a box line, arrow label, or message, never only a footnote. A note under a diagram holds at most two lines at the default label size.

Done when you have listed every lane with its boxes in order and its arrows, and checked each lane against each rule above: no backward arrow, no box with more than 2 incoming, no label over its limit.

## 3. Look up every icon

Pass every component's name to the icon lookup (`how_to` with `domain: {type: "icon", queries: [...]}`), at most 10 names per call. Take a result only when its name plainly is that thing; otherwise use the type's fallback shape from step 4.

Done when every component has a looked-up icon or a fallback shape.

## 4. Build the board

Create the board with `create_file` (`type: "board"`, `title`: the question); `add_board_content` takes no title for flowcharts or sequence diagrams. Add each lane as its own diagram (`add_board_content` with `board_id`; flowcharts with `direction: "left-right"` and nodes in your planned order). Add one text item per lane naming it, such as "Venmo: answer arrives later" (`edit` with the board as `id`, an `operations` entry `{"op": "add", "type": "text", "text": ..., "font_size": "l2", "width": 700, "text_align": "left"}`).

| Type | Color | Fallback shape |
| --- | --- | --- |
| Person or client app | charcoal `#374151` | `ellipse` |
| Our service, API, or on-demand job | pine `#1F6F5C` | `rect` |
| Datastore or file store | violet `#5B4B8A` | `cylinder` |
| Queue, event bus, or anything that runs on a timer (poller, cron job) | ochre `#B7791F` | `pill` |
| Outside vendor or system | steel blue `#2F6FAB` | `cloud` |
| Security or auth | plum `#7C3A5E` | `hexagon` |

- **One palette for every board.** Use exactly these colors, the same ones the scripts use, so boards shown side by side color each part the same way. Risk red `#B42318` is for the risk callout only. Give a part the same name on every board of a set ("Amplify Support" everywhere, never "Support" on one).
- **Outline, not fill.** Give every flowchart node `deco: "outline"`. Solid fills make datastores and vendors the heaviest shapes on the board and drown the labels; outlines keep the color coding and match the legend's pale cells.
- **One bold element.** Fill only the single box the diagram is about, such as the one job every lane branches from, and give it its own legend row with a filled cell that says why it stands out. Everything else stays outlined.
- **Even sizes.** After step 6's `arrange`, resize clouds and hexagons to 192×120 (`edit` update `width`, `height`) so every lane's center line runs straight. Resizing before `arrange` makes it refuse to move that lane.
- **Type scale.** One board heading as a text item at `l3`, lane titles at `l2`, and labels at the default size. Sentence case throughout; no "Step 1" prefixes on lanes that are parallel paths rather than a sequence.
- **Line style.** Solid `arrow` for a synchronous call (the caller waits). `dotted-arrow` for anything asynchronous: a webhook, a queued job, a poll, a scheduled run.
- **Boundaries.** Leave flowchart `groups` out of any board with more than one diagram: `arrange` refuses to move a flowchart that has them. Color and lane titles carry ownership instead. A single-diagram board may use one `silver` `outline` group for a boundary the reader must see.
- **Sequence diagrams.** Whimsical colors participants on its own. Recolor each to its type's color with an `edit` update op on the participant's id (`{"op": "update", "id": ..., "color": ...}`); ids come from `fetch` with `select_kinds: ["sd-actor"]` and `expand_groups: true`. Change anything else in a sequence diagram with `sd_update`, never `x`/`y`.
- **Non-technical audience.** Number the main-path arrows within each lane, starting from 1 ("1 picks Venmo"), and leave side paths unnumbered. Use plain words over class and protocol names.

Done when every lane is on the board with its title text, every box or participant colored by type, and every arrow labeled.

## 5. Add the legend

The legend is a one-row strip under the board heading, so it stays in view however tall the board runs. Write a legend spec with one key per type actually used, in that type's exact hex color with `deco: "outline"` (the one filled element gets `"fill"`), then one key per line style actually used, written as words ("Solid line", "Dashed line"), and a Risk key if the board has one. Give each key its meaning by role, never by shape or icon name. Arrow characters render as emoji, so leave them out. Set `width` to the widest diagram's width.

Then build it with `scripts/legend.py`, which `references/branch-board.md` and `references/parts-board.md` also use: fetch the board with `detail: "detailed"` and `limit: 1`, save its `Palette:` line, run `python3 <skill dir>/scripts/legend.py legend.json --palette palette.txt`, send `step2` as one `edit` call, then fetch with `select_kinds: ["table"]` for the table's id and send `step3` with `<TABLE_ID>` replaced.

Done when every color and line style on the board has a key, and nothing else does.

## 6. Arrange the board

Fetch the board for the ids of the heading, the legend, and each lane's title, risk line, and diagram. Then place everything with one `arrange` call (`board_id`, `x: 0`, `y: 0`, and this `layout`), nesting each lane's title above its diagram. It works the same for flowcharts and sequence diagrams:

```json
["div", {"layout/style": {"flex-direction": "column", "gap": 48, "align-items": "flex-start"}},
  ["item", {"id": "<board heading>"}],
  ["item", {"id": "<legend table>"}],
  ["div", {"layout/style": {"flex-direction": "column", "gap": 80, "align-items": "flex-start"}},
    ["div", {"layout/style": {"flex-direction": "column", "gap": 16, "align-items": "flex-start"}},
      ["item", {"id": "<lane 1 title>"}], ["item", {"id": "<lane 1 diagram>"}]],
    ["div", {"layout/style": {"flex-direction": "column", "gap": 16, "align-items": "flex-start"}},
      ["item", {"id": "<lane 2 title>"}], ["item", {"id": "<lane 2 risk line>"}], ["item", {"id": "<lane 2 diagram>"}]]]]
```

Stack diagrams in one column, never a grid. A board holds at most 4 diagrams; more means it is answering more than one question.

The risk sits with the diagram it's about. On a sequence diagram it is one red text line between that diagram's title and the diagram, naming the step ("Risk at step 7: other Zendesk content is dropped, so the customer never sees it"), and that step's label is red. On a flowchart lane it is the red outlined box: after `arrange`, move it level with the box it names, within 40px of the lane's right edge (`edit` update `x`, `y`; a `fetch` with `detail: "detailed"` gives positions).

If `arrange` refuses with a "stored parent" error, a flowchart on the board has groups: rebuild that lane without them.

Done when `arrange` succeeds and the lanes read top to bottom in your planned order.

## 7. Check the snapshot

Fetch the board as an image (`fetch` with `image: true`) and check each item:

- No arrow crosses a box, a label, or another arrow.
- No two arrows overlap or share a path.
- No arrow points backward against the reading direction.
- No label is clipped or covers a box.
- Lanes line up on the left, and the legend sits clear of them.
- Each risk callout sits level with what it names.
- The board ends near its last diagram. An empty area as big as a diagram means a stray item: find it with a board fetch and delete it.

For each failing lane, go back to step 2 for that lane only: cut an arrow, shorten a label, or split the lane. Then delete its diagram: the id a board fetch lists for a flowchart is its first box, and deleting it removes only that box. Fetch with `scope` set to that id, and delete every shape it lists in one `edit` call (connectors go with their shapes). Add the new diagram and rerun step 6. Change a lane by rebuilding it, never by editing its connectors or labels one at a time. A rebuild gives new ids, so fetch the board again before any further edit.

Done when every item passes on the latest snapshot, or two rounds are spent and the failures are listed.

## 8. Review with fresh eyes

Every board gets this step, whatever its kind. In parallel, spawn the clarity and accuracy reviewers in `references/review.md` and the checklist checker in `references/checklist.md`. List every finding and decide each: **fix** it when you can confirm it in the snapshot or the source, by going back to step 2 for that lane and rerunning steps 6 and 7; **skip** it only when it is wrong, and write down why. "It would need a backward arrow" is never a reason to skip; it means the path needs its own lane. For a branch or parts board, fix the spec and redraw it on a new board, then trash the old board with the `delete` tool. After the fixes, rerun step 7 on a fresh snapshot, then rerun the checklist checker as a new subagent every round, because its count is the bar for this step. If you rebuilt any lane, also rerun the clarity reviewer.

Wait for every reviewer's report before acting on any of them or replying. A reply sent while reviewers are still running ends the session with the loop unfinished. This loop applies to every kind of diagram. After each round, write a line such as "Round 2: checklist 10/12, failed 7 and 8, fixed both". A round below 11/12 is followed by another, up to round 3. Fix the failed checks first; act on other reviewer findings only when they don't undo a passing check.

Done when the latest checklist count is 11/12 or better, every finding is marked fixed or skipped with its reason, and step 7 passed on a snapshot taken after your last change. Below 11 after three rounds, hand back with the count and the failed checks.

**Reply:** the board link, one line on what the diagram answers, any detail you left off the board to keep it clear, each reviewer finding with fixed or skipped and the reason, and every round line in order.
