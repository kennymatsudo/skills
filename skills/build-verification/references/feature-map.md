# Feature map format

The map lives in `features/` inside the kit: one `README.md` index and one file per user-facing feature. `scripts/check.py` parses both, so keep the headings exact.

## Index: `features/README.md`

```markdown
# <App> feature map

Open the file for the feature you changed. Follow `../rules.md` for every proof.

## Baseline

- Start: `<start command>`. Ready when `<doctor command>` exits 0.
- Data: <seed data, test accounts, and where they come from>.
- Isolation: <how two runs avoid sharing state, or "one instance per machine; never drive one you did not start">.

## Features

- [Checkout](checkout.md): pay, saved cards, failed payment retry.
```

Group the list under H3 area headings once it passes about ten entries. A journey that crosses several features gets its own file that links to the per-feature files rather than repeating them.

## Feature file: `features/<slug>.md`

```markdown
# Checkout

A signed-in shopper pays for the items in their cart and sees a confirmation.

## Sub-features

- checkout.pay: paying with a new card creates a paid order.
- checkout.saved-card: a returning shopper can pay with a saved card.
- checkout.retry: a declined card shows an error and lets the shopper retry.

## How a user reaches it

- Cart page, "Checkout" button.
- `POST /api/checkout` from the mobile app.

## How to prove it

- checkout.pay: `bin/verify check checkout-pay`. Reads the order row and payment record (state). Break-tested 2026-10-03: payment capture skipped.
- checkout.saved-card: No check yet.
- checkout.retry: Unreachable: the sandbox processor has no declining test card. Tried the "4000 0000 0000 0002" card.

## Gotchas

- The payment webhook arrives up to 30 seconds after the redirect. Wait on the probe, not a sleep.
```

Rules the script enforces:

- Sub-feature lines are `- <id>: <behavior>`. IDs are lowercase, dotted or dashed, and unique across the map.
- Every sub-feature has exactly one line under "How to prove it", in one of three forms: a command in backticks, `No check yet.`, or `Unreachable: <blocker>. Tried <route>.`
- A command line says `Break-tested <date>: <what was broken>.` or `Not break-tested: <reason>.`
- Every path or command named in backticks under "How to prove it" exists in the repo.

An optional `## Request flow` section may sit before "How to prove it" when the code path is not obvious. Keep the rest of the file about what the user does and sees.
