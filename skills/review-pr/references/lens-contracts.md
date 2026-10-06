# Lens: contracts with callers and consumers

Does the change still fit what flows into it and what reads from it? The diff never shows the code that breaks here, so work from `map.md`.

For each changed symbol, list what it now accepts, returns, raises, writes, and emits, and compare each with the base version. Then open its upstream and downstream locations and check each against the difference.

## Look for

- **Upstream:** a caller that passes a value the changed code now rejects, mishandles, or treats differently: a newly required argument, a narrowed type, a changed default, a different meaning for an existing value.
- **Downstream:** a consumer that relies on something the change altered: a field removed, renamed, or made nullable; an error type or status code changed; ordering, uniqueness, or pagination changed; a return value that used to be checked now ignored.
- **Stored data:** a schema or migration that existing rows violate, a column the old code still writes or reads during deploy, a backfill that can't finish on a large table, or a serialized format old readers can't parse.
- **Deploy order:** the new code and the old code running side by side during a rollout, such as a producer emitting a field the old consumer rejects, or a reader needing a migration that ships later.
- **Across services:** routes, events, queue messages, and table names other repos use. If `map.md` marks other repos unsearched, a change to one of these is a finding only when its own repo shows a consumer.

## Don't flag

- A contract change whose every caller and consumer in the repo the PR updated in the same diff.
