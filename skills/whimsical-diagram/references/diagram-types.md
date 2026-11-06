# Choosing the diagram

Pick by the question the reader is asking. A request with two questions gets two diagrams on one board, each with its own title.

| The reader asks | Diagram | How to build it in Whimsical |
| --- | --- | --- |
| What parts exist, and what talks to what? | Architecture (box and arrow) | `references/parts-board.md` and its script |
| In one scenario, who calls whom, in what order, and who waits? Timeouts, retries, races, callbacks. | Sequence | `add_board_content` `type: "sequence_diagram"` |
| What statuses does one record move through, and what moves it? | State | Flowchart, one `pill` per status |
| What tables or entities exist, and how do they relate? | Entity-relationship (ER) | Flowchart, one `rect` per table, crow's-foot ends |
| What steps and decisions make up one process? | Process flowchart | Flowchart, `diamond` for each decision |
| Where does each part run, in one environment? | Deployment | Flowchart, one group per network or environment, cloud icons |
| How does one topic break down? | Mind map | `add_board_content` `type: "mindmap"`, `data.markdown` |
| How do options compare across the same attributes? | Table | `add_board_content` `type: "table"` |

## Sequence

- A journey across stages ("how does a chat get from Composer to a Product Expert and back") is one overview diagram on one board, at the systems level: one or two messages per stage, each message's label starting with its stage name, 12 messages at most. A participant that only passes calls through, such as a gateway that forwards to the service behind it, is left out, and the call is drawn straight to the service. Detail inside a stage is its own question and its own board, drawn only when asked. If the overview won't fit in 12 messages, it is still at too fine a level: merge steps until it does. Merge steps, never events: each message is one thing happening, and a person's action (a Product Expert replying, ending the session) is a message from that person. The subtitle names the stages the labels start with ("Steps are tagged by the design's five stages: Ask, Connect, ...").
- A detail question names mechanisms ("who waits, timeouts, idempotency"). Each one gets its own visible step where it acts: the call carrying its timeout, the timeout firing as a self-message, the duplicate being caught ("skip, ID already posted"). A retry gets its own diagram after the failure it follows, not a tail on it. Keep every participant that handles the call, gateways included; folding relays away is for overviews only.
- One question stays on one board, with at most 4 diagrams. When it needs more, it is at too fine a level: merge diagrams rather than split the board.
- One scenario per diagram, at most 6 participants and 12 messages. A self-message is for a decision or a rule the question asks about, never routine work; split a longer scenario into two diagrams.
- A name that stands for a value, such as a message M or a key K, is defined in the first label that uses it ("send message M, key K"). Draw a failure path as a second diagram; the syntax has no alt or loop blocks.
- Declare participants first and give each its type: `actor`, `database`, `queue`, `boundary`, `control`, or `collections`. Order them so most calls run left to right: the initiator leftmost, our code next, datastores after it, outside vendors rightmost.
- Keep that order in every diagram on the board; a participant that appears in two parts sits in the same relative place in both. Leave out a participant that sends and receives nothing in that diagram, except in a failure diagram, which keeps its parent's participants so the columns line up.
- Every participant sends at least one message; one that only receives is either missing its action or doesn't belong.
- Number every message in every diagram ("1 send message M, key K"), so a reviewer can name a step.
- When the source gives a timeout for a call, put it on that call's label ("deliver, waits 20s"), and show the timeout firing as a self-message on the waiting participant.
- Before adding, check every message: none may pass over another participant's lifeline. Reorder to fix it. When no order works, as with two paths that both touch the same vendor and datastore (a webhook and a poller), split the scenario into one diagram per path.
- `->>` for a call, `-->>` for a reply or an asynchronous callback. Draw the reply to every call whose answer decides the next step. Message labels are 6 words or fewer.
- Show a timed gap ("30s later") as a self-message on the participant that waits. A self-message is for work a participant does. A note like "auth service not called" goes in a text item beside the diagram.
- Every scenario ends with the reply that reaches its initiator, including failure scenarios ("401, account locked"), so the reader sees each outcome.
- Give every diagram on the board a numbered title naming its scenario and outcome, in the order a reader should take them ("1 Login succeeds", "2 Later requests", "3 Fifth failed login"). A failure of step N is numbered Nb and placed right after it, with a title saying where it splits off ("1b After step 5, Zendesk never confirms"). It starts at that point rather than replaying the steps before it. Every step it branches from also appears in the success diagram. A diagram that starts from a webhook, timer, or poll names that trigger in its title ("2 Webhook: Product Expert replies").
- The risk is a red line under the diagram's title naming the step (SKILL.md step 6), and that message's label turns red (`sd_update` with `text_color` set to the risk red). Space the diagrams evenly with the `arrange` template in SKILL.md.
- Give each datastore its own color, even when two share the `database` type: violet `#5B4B8A` for the first and teal `#3F6E78` for the second. The legend names each one's role ("Postgres: accounts", "Redis: sessions and failure counts").
- State each piece of data's home once, in the legend or the subtitle, and keep every panel consistent with it. Don't let a lock that lives in Postgres sit beside a counter that lives in Redis without saying so.

## State

- One record per diagram. The starting status comes first in the node list and the end statuses last.
- Color by outcome: in progress `yellow`, succeeded `green`, failed `red`, waiting on someone else `blue`.
- Label each arrow with its trigger: the event, job, or call that moves the record ("webhook: completed"). Solid for a move our code makes directly, dotted for one an outside event or a scheduled job causes.
- A retry is the one allowed backward arrow. Label it with its limit ("retry, max 3").

## ER

- One `rect` per table, labeled with the table name on the first line and only the columns the question needs below it, keys marked `PK` and `FK`.
- Use `from_endpoint` and `to_endpoint` crow's feet (`one-one`, `zero-many`, `one-many`, `zero-one`), and label each edge with the relationship verb ("has many attempts").
- At most 8 tables. Parent tables come before child tables, left to right.

## Process flowchart

- One start and clear end nodes. Each `diamond` has exactly one arrow per answer, labeled with that answer ("yes", "timeout").
- `top-down` for a process with no icons, `left-right` otherwise.

## Deployment

- One environment per diagram, alone on its board, so it can use groups. Group by network boundary (cloud account, VPC, subnet), outermost first.
- Use the provider's icons from the icon lookup, since readers recognize them faster than labels.

## Mind map

- At most 3 levels and 7 children per node. Each node is a noun phrase of 4 words or fewer.
