# Lens: change locality

When one decision changes, how many places have to change with it?

## Look for

- **Information leakage.** One design decision (a format, a table or column name, a status string, a magic number, a URL shape) spelled out in three or more files, so changing it means a hunt.
- **Shotgun surgery.** History shows the same set of files changing together, again and again, for one kind of change. Check with `git log --name-only` on the files in question.
- **Divergent change.** One module changes for several unrelated reasons, visible as unrelated commits touching different halves of it.

Weigh coupling by three things: how much one side must know about the other, how far apart they sit (same function, same module, other module, other service, other team), and how often the shared part changes. Strong coupling at short distance or on code that never changes is fine. Strong coupling across a module or service boundary on code that changes is the finding.

## A finding needs

Every location that spells out the decision, quoted, or the commits that show files changing together. Name the one place the decision should live.

## Don't flag

- Duplication of code that looks alike but changes for different reasons. Merging it creates the wrong abstraction.
- Tight coupling inside one module or file.
- A shared constant or schema that is already the single source, with everything else derived from it.
- Fluent builders and plain data access that only look like long call chains.

## Usual verdicts

move, merge
