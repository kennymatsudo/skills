# Discovery prompt

Spawn one read-only subagent on a mid-tier model with this prompt. Fill in the repo path.

---

Read the repo at `<repo path>` and answer each question below from its code, scripts, and docs. Do not run the app, its tests, or a build. Do not edit files.

For every answer, cite `path:line`. If the repo does not answer a question, write "Unknown" and name the places you looked.

1. **Surface.** What does a user touch: web UI, CLI or TUI, desktop app, HTTP API, mobile app, library? List each, and say which one most users meet first.
2. **Start.** The repo's own command to run it locally (Makefile, package scripts, README quickstart, compose file). Ports, environment variables, seed data, and auth it needs.
3. **Ready.** The signal that it is up: a health route, a log line, a port answering, a prompt.
4. **Who can start it.** Anything that needs a human: a cloud login, a VPN, a secret from a password manager, a hardware device. Say whether an agent with only this checkout could start it.
5. **Isolation.** Can two copies run side by side? Look for configurable ports, data directories, browser profiles, and shared external resources (one sandbox account, one webhook URL).
6. **Drive.** Existing ways to act like a user: end-to-end specs (Playwright, Cypress), API clients, CLI entry points, debug ports, seed or fixture scripts. Prefer what exists over anything new.
7. **Observe.** Where results can be read back: databases and how the code connects to them, logs, response bodies, files written, outbound messages.
8. **Shared I/O.** The modules that already own database and external API access, which new tools should reuse instead of opening their own connections.
9. **Real side effects.** Anything a run would do outside this machine: send email or messages, charge money, create records in a shared sandbox, spend a quota.
10. **Features.** The top five user-facing features, from routes, commands, menus, or docs, each with its entry point.
11. **Verification workflow.** Where the repo keeps acceptance or launch requirements, their mapping to checks, current results, known failures, and evidence. Name the owner of each and how to tell when a source changed. Record any workflow the user has declared.

Return the eleven answers in order, then a short list of anything that looked broken (a start command that references a missing file, a stale README step).
