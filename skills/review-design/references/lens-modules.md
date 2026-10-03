# Lens: module boundaries and placement

Does each file sit in, and carry the name of, the domain it serves, and does each domain reach others only through their public surface?

Use the domain map the scope gives you. If a file in scope sits outside every listed domain, say so in `checked_clean` rather than assigning it one.

## Look for

- **Misplaced file.** Most of a file's imports and callers sit in another domain. Count both: names imported from each domain, and caller files in each domain.
- **Reach-in.** Code imports another domain's internals (private or underscore names, deep paths, names missing from its declared exports) instead of its public surface.
- **Wrong direction.** A shared or lower-level module imports a feature domain, or two domains import each other, directly or through a third.
- **Hidden coupling.** Code reads another domain's tables, private fields, or internal format, or two domains must agree on an argument order, a call order, or an encoding with nothing checking that they do.
- **Grab bags.** A module named for no domain (`utils`, `common`, `helpers`, `misc`, `manager`, or a layer name such as `services`) holding code that several domains each use for their own purposes. Name the domain each piece serves.
- **Drifted names.** A module or file name that misleads about what most of it does, or uses a different word than the domain uses for the same thing in its models, API, or UI. Module and file names only, never identifiers.

## A finding needs

Facts a checker can recount with a search, not "belongs in". For placement: names imported per domain and caller files per domain, with the search you ran, such as "`x.py` imports 9 names from `billing` and 1 from `orders`; its 4 callers are all in `billing`". For reach-in: the import line and the target's public surface. For direction: the import chain. For a name: the name and the domain's word for the same thing, quoted where the domain uses it.

## Don't flag

- Imports a boundary config or exception list in the repo already allows. Cite it. Flag the list itself if history shows it growing.
- Shared infrastructure (logging, config, database access) that every domain uses and that imports no domain.
- A file several domains use about equally, when it imports none of them.
- Tests reaching into the domain they test.
- A rename for taste. The current name must mislead or clash with the domain's word.

## Usual verdicts

relocate, move, split
