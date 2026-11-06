# Choosing the diagram

Pick by the question the reader is asking. A request with two questions gets two diagrams on one board, each with its own title.

| The reader asks | Diagram | How to build it in Whimsical |
| --- | --- | --- |
| What parts exist, and what talks to what? | Architecture (box and arrow) | Flowchart, lanes, as in SKILL.md |
| In one scenario, who calls whom, in what order, and who waits? Timeouts, retries, races, callbacks. | Sequence | `add_board_content` `type: "sequence_diagram"` |
| What statuses does one record move through, and what moves it? | State | Flowchart, one `pill` per status |
| What tables or entities exist, and how do they relate? | Entity-relationship (ER) | Flowchart, one `rect` per table, crow's-foot ends |
| What steps and decisions make up one process? | Process flowchart | Flowchart, `diamond` for each decision |
| Where does each part run, in one environment? | Deployment | Flowchart, one group per network or environment, cloud icons |
| How does one topic break down? | Mind map | `add_board_content` `type: "mindmap"`, `data.markdown` |
| How do options compare across the same attributes? | Table | `add_board_content` `type: "table"` |

## Sequence

- One scenario per diagram, at most 6 participants. Draw a failure path as a second diagram; the syntax has no alt or loop blocks.
- Declare participants first and give each its type: `actor`, `database`, `queue`, `boundary`, `control`, or `collections`. Order them so most calls run left to right: the initiator leftmost, our code next, datastores after it, outside vendors rightmost.
- Keep that order in every diagram on the board; a participant that appears in two parts sits in the same relative place in both.
- Before adding, check every message: none may pass over another participant's lifeline. Reorder to fix it. When no order works, as with two paths that both touch the same vendor and datastore (a webhook and a poller), split the scenario into one diagram per path.
- `->>` for a call, `-->>` for a reply or an asynchronous callback. Draw the reply to every call whose answer decides the next step. Message labels are 6 words or fewer.
- Show a timed gap ("30s later") as a self-message on the participant that waits. A self-message is for work a participant does. A note like "auth service not called" goes in a text item beside the diagram.
- Every scenario ends with the reply that reaches its initiator, including failure scenarios ("401, account locked"), so the reader sees each outcome.
- Give every diagram on the board a numbered title naming its scenario, in the order a reader should take them ("1 Login succeeds", "2 Later requests", "3 Fifth failed login"). Space the diagrams evenly with the `arrange` template in SKILL.md.
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
