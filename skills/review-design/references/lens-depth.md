# Lens: depth and dead weight

Does each layer, module, and abstraction hide more than it costs to learn?

## Look for

- **Pass-through layers.** A wrapper, adapter, or service with one caller that repeats the methods and arguments of the layer below. Answering "where does X come from?" means opening more than three files.
- **Shallow modules.** The interface is nearly as complex as the implementation. Deletion test: imagine inlining the module into its callers. If its complexity vanishes or concentrates in one place, the module was shallow. If it spreads across every caller, the module earns its keep.
- **Speculative generality.** Config flags, parameters, extension points, generic types, or interfaces that no current caller uses or varies. One implementation behind an interface is a hypothetical seam; two is a real one.
- **Dead code.** Functions, branches, flags, or files nothing reaches. Confirm with a search for every reference, including dynamic dispatch, string lookups, and config. Also search the docs and agent instruction files that still describe it.
- **Two ways to do one thing.** An old and a new API, or two helpers or patterns for the same job, both alive with callers split across them. Agents copy whichever they find first. List each side's callers and the date the newest caller was added (`git log -S`).
- **Rebuilt existing code.** For every helper in scope, name the standard library, dependency, or repo function that already does its job, or write "none" in `checked_clean`. A helper that wraps or reimplements one is a finding.

## A finding needs

The callers you found (or their absence, with the search you ran), and the lines of the layer that show it adds nothing or hides little. For rebuilt code, the helper quoted and the existing function named.

## Don't flag

- A layer that hides a real decision: retries, caching, a vendor's quirks, a wire format.
- An interface with one implementation that exists for a test double the tests actually use, or that sits at a published API boundary.
- Short functions extracted to name a step, when the caller reads better for it.
- Code reached only through reflection, plugins, or a framework convention you confirmed.
- An old API kept for external users the repo can't migrate.
- A copy kept so two modules that change for different reasons don't share code.

## Usual verdicts

merge, delete
