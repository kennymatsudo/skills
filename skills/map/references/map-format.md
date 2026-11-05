# Map file format

`.map/map.json` at the repo root holds every level built so far. `map.html` beside it draws from this file, so keep the field names exact.

## Fields

- **`repo`:** the repo's name.
- **`summary`:** two sentences on what the system does and its main request path, shown when the map opens.
- **`built_at_commit`, `files`:** written by `map_file.py stamp`. Never edit them by hand.
- **`nodes`:** one per box.
  - `id`: short, stable, kebab-case, unique across the file.
  - `name`: what the box says.
  - `kind`: `service`, `datastore`, `queue`, `external`, `group`, or `component`.
  - `level`: 1 for services and their peers, 2 for components inside one service.
  - `parent`: `null` at level 1, else the id of the service or group it sits inside.
  - `summary`: its role in 70 characters or fewer, in plain words, such as "Rails API for carts and orders". Say what it is for, not how it works, and don't repeat its name or its parent's.
  - `tech`: optional, the framework or product, such as `Rails 8` or `Postgres 16`. Leave it out when it only repeats the parent's, such as `Rails controller` inside a Rails service.
  - `cites`: `path:LINE` or `path:START-END` from the repo root, for where it is defined or deployed. An `external` node may have none.
  - `loaded`: `true` once its children have been mapped.
  - `verified`: `false` while a background build's node waits for the verifier; absent or `true` once checked.
- **`edges`:** one per arrow, between nodes at the same level.
  - `from`, `to`: node ids.
  - `label`: what crosses, in 24 characters or fewer, such as `HTTP /api`, `SQL`, `publishes order.created`. Not the code that makes the call; that belongs in a path.
  - `evidence`: how the connection was confirmed: `config`, `client-call`, `route`, `topic`, or `inferred`.
  - `cites`: the wiring that proves it. `inferred` edges may have none.
- **`findings`:** `{ node, severity, text, cites }`, defects a reader would act on. Each is stated once in the whole map, on the box whose code shows it; a box above it counts it without repeating it. `check` rejects a finding that restates one on the same box or a box above or below it.
  - `severity`: `bug` (wrong today), `risk` (breaks under failure, retries, or concurrency), or `gap` (a piece the design needs is missing).
  - A description of how the code works today is not a finding, however unusual.
- **`unknowns`:** `{ node, text }`, a question the repo cannot answer, such as a host set by an env var nothing in the repo sets, and the file where tracing stopped. Code nobody read yet is not an unknown: read it. A problem the code shows is a finding. A gap that holds for the whole repo, such as no production deploy config, is one unknown with `node: null`, not one per box.
- **`paths`:** level 3 call chains, `{ node, title, steps: [{ call, cites }] }`, where `node` is the component the path starts in.

## What counts as what

- **Service:** something deployed or run on its own: its own container, process type, function, or app. A folder is not a service until a deploy file, Procfile entry, or build target says so.
- **Group:** a box standing in for related services when a level would pass 20 boxes. Its members are its children.
- **Component:** a module or class inside one service with behavior others depend on, such as a controller, a service object, or a client. Not every file: fold plain data models into one `Models` box, and helpers into the component that uses them.
- **External:** a system the repo calls but does not deploy, such as a payment provider or an email API. It calls nothing on the map. A stub or client for it in the repo is a component of the service that holds the code.
- **One box per piece of code.** A worker that runs another service's code maps only what is its own, such as its entrypoint and job list; the shared code stays under the service whose folder holds it. `check` rejects the same code under two services.

## Worked example

A small shop: a web app, an API, a background worker, Postgres, Redis as a job queue, and Stripe.

```json
{
  "repo": "shop",
  "summary": "An online shop: a Next.js storefront calls a Rails API that charges cards through Stripe and stores orders in Postgres. A Sidekiq worker sends receipts and refunds from a Redis queue.",
  "built_at_commit": "4e1c2a9",
  "files": { "docker-compose.yml": "…", "api/app/clients/stripe_client.rb": "…" },
  "nodes": [
    { "id": "web", "name": "Web app", "kind": "service", "level": 1, "parent": null,
      "summary": "Storefront customers browse and check out in", "tech": "Next.js", "cites": ["docker-compose.yml:4-12"], "loaded": false },
    { "id": "api", "name": "API", "kind": "service", "level": 1, "parent": null,
      "summary": "Carts, checkout, and orders", "tech": "Rails 7", "cites": ["docker-compose.yml:14-25"], "loaded": false },
    { "id": "worker", "name": "Worker", "kind": "service", "level": 1, "parent": null,
      "summary": "Sends receipts and runs refunds", "tech": "Sidekiq", "cites": ["Procfile:2"], "loaded": false },
    { "id": "postgres", "name": "Postgres", "kind": "datastore", "level": 1, "parent": null,
      "summary": "Orders, carts, and users", "cites": ["docker-compose.yml:27-33"], "loaded": false },
    { "id": "redis", "name": "Redis", "kind": "queue", "level": 1, "parent": null,
      "summary": "Job queue between the API and the worker", "cites": ["docker-compose.yml:35-38"], "loaded": false },
    { "id": "stripe", "name": "Stripe", "kind": "external", "level": 1, "parent": null,
      "summary": "Card payments", "cites": [], "loaded": false }
  ],
  "edges": [
    { "from": "web", "to": "api", "label": "HTTP /api", "evidence": "config",
      "cites": ["web/next.config.js:8-12"] },
    { "from": "api", "to": "postgres", "label": "SQL", "evidence": "config",
      "cites": ["api/config/database.yml:1-9"] },
    { "from": "api", "to": "redis", "label": "enqueues ReceiptJob", "evidence": "client-call",
      "cites": ["api/app/services/checkout.rb:41"] },
    { "from": "worker", "to": "redis", "label": "consumes jobs", "evidence": "config",
      "cites": ["api/config/sidekiq.yml:1-6"] },
    { "from": "api", "to": "stripe", "label": "charges cards", "evidence": "client-call",
      "cites": ["api/app/clients/stripe_client.rb:12-20"] }
  ],
  "findings": [
    { "node": "api", "severity": "bug", "text": "Stripe is charged before the order row is saved; a failed save leaves a charge with no order",
      "cites": ["api/app/services/checkout.rb:30-44"] }
  ],
  "unknowns": [
    { "node": "worker", "text": "Refund jobs read a STRIPE_WEBHOOK_URL env var; nothing in the repo sets it" }
  ],
  "paths": []
}
```

The chat answer for that level:

```
Web app ──HTTP /api──▶ API ──SQL──▶ Postgres
                        │  └──charges cards──▶ Stripe (external)
                        ▼
                      Redis ◀──consumes jobs── Worker
```
