# Extract one AIM page → data/pages/NNN.json

Inputs: `work/renders/NNN.png` (full page, 300 dpi), `work/ocr/NNN.json` (Apple Vision boxes, a second opinion only). If the callout list or legends are small, crop them at 300 dpi and look again.

Schema: `docs/spec.md` §6. Rules:

1. **Copy text exactly.** A digit you can't read is `?`; set `uncertain: true`. Never infer a digit, not even from the registry or OCR. `check.py` handles that.
2. `group` = UPC number from the title block, or the RPO code for option pages. `sheet` from the title block; if smudged, use the `C/O` box or neighbours, and say so in `notes_internal`.
3. One `parts` entry per callout line. LH/RH pairs stay as written (`3966685-6`). Model codes printed next to a callout (`19437`, `19467`) go in `models` of the part they qualify, not as a part name.
4. `torque_ref` from the triangle next to the item in the drawing. `torques` from the legend at lower left, units exact.
5. `materials` from the legend (`[A] 51n◇ ADHESIVE 1.02 OZ`) plus where the tag appears in the drawing.
6. **`fastening` is the important part.** Users never see the drawing, so write down what it shows: which fastener goes through what, into what, from which side, how many, which view. `from: "drawing"` or `"note"`. `how` is `holds` (default), `seals` or `glues`. Every part that isn't itself a fastener needs a fastening entry or a `notes_internal` line saying why not (not shown, ambiguous). If a leader line is ambiguous, leave it out and say so.
7. `revisions` verbatim; fill `was` (old pn) and `item` when the text says so (circled symbol next to a callout = that revision).
8. `summary`: 1–3 sentences a restorer would understand. Use common names too ("rear roof upper molding = the chrome strip above the rear window").
9. `notes`: short NOTE boxes and dimension callouts verbatim. **Procedures and any text longer than ~2 lines: rewrite in your own words as short steps** (facts kept: fasteners, values, order, dimensions). Never copy long passages; they're the manual's expression, and we only ship facts.
