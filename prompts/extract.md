# Extract one AIM page → data/pages/NNN.json

Inputs: `work/renders/NNN.png` (full page, 300 dpi), `work/ocr/NNN.json` (Apple Vision boxes, a second opinion only). Zoom into the callout list, legends, revision block and each view:

```
.venv/bin/python -W ignore -c "import pymupdf; d=pymupdf.open('docs/1970 CORVETTE ASSEMBLY MANUAL_compressed.pdf'); pg=d[N-1]; r=pg.rect; pg.get_pixmap(dpi=300, clip=pymupdf.Rect(x0*r.width, y0*r.height, x1*r.width, y1*r.height), colorspace=pymupdf.csGRAY).save('work/crops/NNN_name.png')"
```
(fractions 0–1). For a sideways drawing add `matrix=pymupdf.Matrix(1, 1).prerotate(-90)` to `get_pixmap`. Crops go in `work/crops/` named by page; skip a crop that exists. Any helper scripts go in `work/agents/<your pages>/`, never shared paths.

Schema: `docs/spec.md` §6; `data/pages/112.json` is a reviewed example. Rules:

1. **Copy text exactly.** A digit you can't read is `?`; set `uncertain: true`. Never infer a digit, not even from the registry, OCR or another sheet. `check.py` fills hole-punched digits later.
2. `group` = UPC number from the title block, or the RPO code for option pages (`"OPTION INDEX"` for the option list). `sheet` from the title block; if smudged, use the `C/O` box or neighbours, and say so in `notes_internal`. `status`: `active`, `canceled` (stamped or "sheet canceled" revision) or `preliminary`.
3. One `parts` entry per callout line. LH/RH pairs stay as written (`3966685-6`). A line that only adds a model code (`3966641-2  19437`) is its own part: repeat the item's name from the line above and put the code in `models`. Page-level `models` is the title block's model box (`19000` = all).
4. `torque_ref` from the triangle next to the item in the drawing. `torques` from the legend at lower left, units exact. Unreadable value → `"?"` and `"uncertain": true` on that torque.
5. `materials` from the legend (`[A] 51n◇ ADHESIVE 1.02 OZ`) plus where the tag appears in the drawing. On the D-sheet code charts leave `materials` empty and use `tables`.
6. **`fastening` is the important part.** Users never see the drawing, so write what it shows: which fastener goes through what, into what, from which side, how many, which view. `from: "drawing"` or `"note"`. `how` is `holds` (default), `seals` or `glues` (for adhesive/sealer give `"material": "51n"` and empty `fastener_items`). Procedure pages that name fasteners by letter: put the letter in `fastener_items`. Every part that isn't itself a fastener needs a fastening entry or a `notes_internal` line saying why not (not shown, ambiguous).
7. `revisions` as printed (they're short); fill `was` (the old or removed pn) and `item` (the callout, or the code letter on chart sheets) when the text says so. A circled symbol next to a callout = that revision.
8. `summary`: 1–3 sentences a restorer would understand: what is installed, where on the car, how it's fastened. Add common names restorers use ("rear roof upper molding = the chrome strip above the rear window", "door glass rear seal", "T-top = roof panel"), so people can find it in their own words.
9. `notes`: short NOTE boxes and dimension callouts verbatim. **Procedures and any text longer than ~2 lines: rewrite in your own words as short steps** (facts kept: fasteners, values, order, dimensions). Never copy long passages; they're the manual's expression, and we only ship facts.
10. `tables` (charts, contents, wiring lists, codes): `{"title", "columns", "rows"}`, rows as arrays of strings. Cells printed once per block (a part number covering several code rows) are filled down into every row. Two stacked values in one cell are written `"1 / C07"`.
11. Wiring diagrams: list what fits (components, connectors, wire colors/gauges) in `tables`; don't trace routes you can't read.
