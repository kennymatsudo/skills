# Lens: security and data

Can someone get, change, or destroy something they shouldn't, through what this PR changed?

Trace each new or changed entry point (endpoint, handler, consumer, job, CLI command) from where input arrives to where it's used.

## Look for

- **Access:** a new path that skips the auth or permission check its siblings run; a lookup by ID that doesn't scope to the caller's account or tenant; a role check that trusts a value the caller sends.
- **Injection:** input reaching SQL, a shell, a template, a file path, a URL fetched by the server, or a deserializer without the escaping or allowlist the repo uses elsewhere.
- **Secrets and personal data:** credentials, tokens, or personal data written to logs, errors, analytics, responses, or a less protected store.
- **Data integrity:** deletes or updates without a scope, writes that can half-complete without a transaction, retries or reruns that duplicate side effects (charges, emails, messages) without an idempotency key.
- **Limits:** a new loop, query, or fetch whose size a caller controls with no cap.

## Don't flag

- Internal-only code whose every caller is already authenticated and authorized, shown by citation.
- Hardening the repo applies nowhere else, unless this PR's change makes the gap reachable.
