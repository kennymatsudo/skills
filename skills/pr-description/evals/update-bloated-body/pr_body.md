## Description

Part of https://linear.app/example/issue/ING-412

The webhook ingester decided what each event meant in the same code that wrote to the database and called the notifier, so every routing rule could only be tested through a service built from mocks, and its availability hung on settings only outbound sync uses. This separates the decision from the I/O, gives ingestion its own settings and a tested wiring, closes a race that could lose a cancellation, and closes a counting gap in how orders end.

- `parse_delivery` returns one typed event per kind (created, updated, cancelled, failed, unhandled), each with only its own fields; an `EventSource` value replaces three overlapping source booleans.
- New pure `decide()` maps an event and the order's state to one action plus any external id to backfill; `apply_event` performs that action and matches it exhaustively, so an unhandled action fails mypy.
- The split leaves routing unchanged: the existing service tests pass as-is and still cover commit and publish ordering, and new parametrized tests call `decide()` directly with plain values.
- An event for a `pending` order now re-reads the row with `SELECT ... FOR UPDATE`, which waits for the creator's commit, so a cancellation between reserving stock and committing `confirmed` is no longer ignored and acknowledged.
- `IngestSettings.webhook_config()` and `sync_ids()` return typed config or `None`, replacing the handler's hand-kept name list and duck-typed check; env var names are unchanged.
- Behavior change: the handler is disabled only when the webhook secret is missing. Without sync IDs it still ingests webhooks (previously 503) but refuses outbound syncs.
- `LiveIngester.build_webhook_service` wires a request's webhook service, covered by a test that posts an update through `deliver_webhook`; the two sync paths share one builder.
- Orders ended from the sync path now record `order_ended.cancelled_upstream`, so the counter covers both ways an order ends.
- `OrderEndReason` moves next to the `Order` model, and `mark_ended` requires it instead of any string.
- The two end paths keep their deliberately different commit/publish order, and the sync path still does not release reserved stock.

## Manual Test Plan

1. [ ] POST a signed `order.cancelled` webhook for a pending order; confirm the order ends once and redelivery adds nothing.
2. [ ] Start the service with sync IDs unset; confirm a webhook returns 200 and an outbound sync is refused.
