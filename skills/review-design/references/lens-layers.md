# Lens: layers and service shape

Does each layer of a service do only its own job, and can a reader find code where the layer map says it lives?

Use the layer map the scope gives you: for each domain, which files are entry points (handlers, views, controllers, consumers, tasks), which coordinate (services, use cases), which decide (domain models, rules), and which talk to storage or other systems (repositories, clients). Judge each layer by the repo's own convention, read from how most of its domains are laid out, not by an ideal one.

## Look for

- **Decisions at the edges.** An entry point or a repository decides a business rule (eligibility, state transitions, pricing, dedupe) that the service or domain layer decides for its siblings. Quote the rule and the sibling that keeps it in the right layer.
- **Layer skipping.** An entry point reads or writes storage directly, or calls another domain's internals, while its siblings go through the service layer.
- **Edge formats leaking inward.** A service or domain function takes or returns a request, response, ORM row, queue message, or status code, so it can't be called from a second entry point without faking the first.
- **Inconsistent layout.** Sibling domains organize the same layers differently (one has a service module, another puts the same kind of logic in its views), so a reader and an agent can't predict where code lives. Count how many domains follow each layout.
- **Overgrown files.** One file holds several concerns that share little: sections with mostly disjoint imports and disjoint callers. Name each concern, its lines, and its callers. Size alone is not a finding.
- **Missing layer.** Two or more entry points repeat the same coordination (load, check, write, notify) because no service owns it.

## A finding needs

The layer map entry for each file involved, the quoted lines that sit in the wrong layer, and a sibling or convention showing where the repo puts that kind of code. For layout, the domains on each side with their file paths. For an overgrown file, each concern's line range and its imports and callers, with the search you ran.

## Don't flag

- A small service where the layers collapse into one or two files and nothing else in the repo splits them.
- A layout a framework requires, or one the repo documents. Cite it.
- Validation an entry point does to reject malformed input. That is the entry point's job.
- Thin glue code whose only job is to wire layers together.
- A large file whose sections all serve one concern and share callers.

## Usual verdicts

move, split, relocate
