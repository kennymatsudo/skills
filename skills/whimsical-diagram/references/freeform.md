# Hand-placed boards

Reach for this when a box-and-arrow board should show a shared element once, such as one datastore every path writes to or one job every path branches from. Lanes of flowcharts can't share a box, so each lane would repeat it. Build the board from individual shapes and connectors with `edit` add ops instead, at coordinates you choose.

## How connectors behave

- A connector attaches to a shape's center or the middle of one of its sides, and you can't choose which. A `straight` connector between two shapes is only horizontal or vertical when their centers line up exactly, so place shapes on a grid where every connected pair shares a center x or center y.
- An `elbow` connector picks its own sides from where the shapes sit. When the target is mostly above or below, it enters from the top or bottom, and it will route through whatever is in the way.
- Moving a shape does not re-route connectors that already touch it. Place every shape first, then add the connectors. To move a shape later, delete its connectors and add them again.

## Patterns

- **Shared datastore as a band.** Draw one wide `rect` with `deco: "dashes"` in the datastore color behind a row of cylinders, with a text label such as "Payouts DB" inside its left end. Give each path its own cylinder in the band, directly below the box that writes to it, labeled with what that path writes ("Attempt and result"). The writes stay straight and vertical, and the band reads as one table.
- **Branching tree.** For one box branching into several, add tiny junction shapes (`rect`, 4×4, `color: "white"`, `deco: "outline"`, `text: " "`): one directly below the source and one directly above each target, all on the same y. Connect source to the middle junction, the middle junction to the outer ones, and each junction to its target, all `straight`. Only the last segments get `to_endpoint: "arrow"`, and only they carry labels ("card", "Venmo", "ACH").
- **Behavior is not a box.** Retries and alerts are what a box does, not components. Put them on the box's second line ("Card executor\nretries 3, then alerts") rather than drawing a retry box with its own arrow.

## Layout grid

Run the main path left to right across the top row. Branch downward from it, put each target's outside vendor to its right on the same center y, and lay the shared datastore band along the bottom. Leave at least 120px between connected shapes so labels fit. Put the legend under the band as a strip as wide as the band: a table with one column per key, the colored key cells in the first row and their meanings in the second. A table added through `edit` ignores your `x`/`y` and its `head_style: "hide"`, so after adding it, move it with an `update` on `x` and `y`, set `widths` to fill the band, and drop the placeholder header with `remove_rows` `[0]`.
