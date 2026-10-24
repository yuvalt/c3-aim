# c3parts — Spec

Turn the **1970 Corvette Assembly Instruction Manual (AIM, GM 3965172)** into a small knowledge pack that any restorer can load into ChatGPT, Claude, Gemini or NotebookLM and ask: *"What's 9431792, what does it hold, how many, what torque, what size?"*

Previous, larger version: `spec-original.md` (Rust MCP server, hosted service). Cut for v1; see §10.

---

## 1. What we ship (v1)

A **pack** of two files, plus instructions:

| file | purpose |
|---|---|
| `dist/aim_sheets.md` | one self-contained section per sheet: header, callouts, torques, materials, notes, revisions, **fastening** (what holds what), summary, glossary aliases. Each section must make sense on its own, since file search returns fragments. |
| `dist/aim_parts.csv` | one row per callout, for exact lookups via the chat app's code tool ("which sheets use 9419000"). |
| `dist/instructions.md` | system prompt for the Custom GPT / Project (§8). |

Published as:
- a **public Custom GPT** (free ChatGPT users can use GPTs; MCP connectors need paid plans + Developer Mode), and
- a downloadable zip for Claude Projects, Gemini Gems, NotebookLM.

Users never get page images (copyright). So everything a reader would get from the drawing must be written into the text during extraction.

---

## 2. Source facts (verified 2026-10-24)

- `docs/1970 CORVETTE ASSEMBLY MANUAL_compressed.pdf`: 435 pages, each one 1-bit CCITT scan, ~300 dpi, landscape. Never commit it or renders.
- **Text layer is junk** (ABBYY: `3972624` → `3172124`). Ignore it. Fresh OCR at 300 dpi is good: Apple Vision got every number on K3 right; tesseract missed model codes.
- **Layout:** p1–284 base manual, UPC 0–14. p285–435 **Option section**, grouped by RPO code (C07, C08, C50, CD2, N14, N37, N40, NA9, UA6, U69, U79…), each restarting at A1. p285 = alphabetical option list.
- **Sheet ids are not unique.** Key = `(group, sheet)` where group is the UPC (`0`–`14`) or RPO code (`N40`). E.g. `A2` exists in UPC 0, 12, 14, C07, NA9, N40.
- PDF bookmarks give UPC → first page. Most groups start with a CONTENTS sheet listing their sheets.
- **Per-part model codes:** the same item number can appear twice, one per body (`19437` coupe, `19467` convertible). Item numbers are not unique within a sheet.
- LH/RH pairs written `3954589-90` = 3954589 + 3954590.
- **Hole punches** wipe out digits in the top-left callout list, often item 1 (D2 item 1, K3 item 1).
- Some sheets are stamped CANCELED or PRELIMINARY; one page (p430) has a sideways drawing.
- Torque legend units vary (`LBS IN`, `LBS FT`). Applied-material tags: `18a◇` → legend at bottom.
- **The AIM never gives fastener sizes.** Only GM numbers.
- Sheet ids shift between years: the 1971 AIM's F20 is the 1970 AIM's **F18** (same parts). The pack is **1970 only**.

## 3. External sources

- **1970 Corvette Registry AIM index**, http://1970corvetteregistry.org/aim/aimstatic.html: 2,111 rows (pn, name, upc, sheet, title, page), 200 sheets, UPC 0–13. Missing UPC 11, 14 and the option section. No items, torques or notes. Transcribed from a cleaner copy: **has the hole-punched digits** (D2 item 1 = 3990560, K3 item 1 = 3954525/6). Registry page = our PDF page − 2. Use as a **cross-check and gap filler**, not a source of truth. Credit them.
- **GMPartsWiki** (gmpartswiki.com): OCR of GM Standard Parts Catalog 24 (1971/74) and Chassis & Body catalogs; "8.900" tables give sizes for 94xxxxx numbers (e.g. 9431792 = 10-32 × 3/8, phosphate, in 3 catalogs). **Blocks bots, so no scraping.** Ask the owner for the tables; meanwhile hand-lookup a pilot set.
- Per-part web search: 5–10 min/part, ~50% reach two sources. Last resort.
- Dead end: corvettebergen.com `c3_repair.pdf` is a Chilton guide, no part numbers.

---

## 4. Layout

```
c3parts/
  docs/            spec.md, the PDF (gitignored)
  STATUS.md        milestone, counts, review-queue size, exact next step
  ocr.py           render + OCR one page or a range
  vision_ocr.swift Apple Vision OCR helper (compiled once to bin/vision_ocr)
  check.py         cross-check extraction vs OCR vs registry → review queue
  build.py         data/ → dist/
  prompts/extract.md
  work/            gitignored: renders/NNN.png, ocr/NNN.json, registry.csv
  data/
    pages/NNN.json   one per PDF page (extraction output, hand-corrected)
    review/queue.csv
    glossary.csv     term, aliases, gm_terms, sheets, note
    fasteners.csv    pn, kind, thread, length, head, finish, source, url, confidence
  dist/            the pack
```

Python 3.11+, one dependency (`pymupdf`). Every script skips outputs that exist; `--force` redoes; `--pages 1-435` limits.

## 5. Pipeline (all local)

1. **`ocr.py`**: render each page at 300 dpi grayscale → `work/renders/NNN.png`; run Apple Vision (`bin/vision_ocr`) → `work/ocr/NNN.json` (text + boxes). Free, about a few seconds per page.
2. **Extract (Claude Code, on the user's plan, no API key):** for each page, Claude Code views the render (plus a zoomed crop of the callout list when small), reads the OCR JSON as a second opinion, and writes `data/pages/NNN.json` per `prompts/extract.md`. Batches of ~20 pages; subagents may run batches in parallel. Rules:
   - copy text exactly; unreadable digit → `?` + `uncertain: true`; never infer digits;
   - write **fastening** from what the drawing shows (leader lines, views, dimension notes such as "(2) places ea. side");
   - `name` verbatim, `name_expanded` in plain English (`MLDG-RR ROOF UPPER` → "Molding – rear roof upper").
3. **`check.py`**: for each part number, compare against (a) OCR tokens on that page and (b) registry rows for the same (group, sheet). Disagreements, `?` digits and registry numbers missing from our page → `data/review/queue.csv`. Sanity: 6–7 digits, torque refs exist in legend, sheet id matches title-block pattern. Also prints counts.
4. **Review:** Claude Code or the user resolves queue rows by looking at the page and editing the JSON. Hole-punch gaps may take the registry digit only if the visible digits match it; set `source: "registry"` on that part.
5. **`build.py`**: pages + glossary + fasteners → `dist/aim_sheets.md`, `dist/aim_parts.csv`, `dist/instructions.md`. Deterministic.

## 6. Page JSON

```json
{
  "page": 200, "group": "6", "sheet": "D2", "title": "ACCELERATOR CONTROL CABLE",
  "page_type": "assembly|chart|index|text|diagram|cover|blank",
  "status": "active|canceled|preliminary",
  "summary": "1–3 plain-English sentences: what is installed, where, how fastened.",
  "parts": [
    {"item": "9", "pn": "9419000", "name": "BOLT", "name_expanded": "Bolt",
     "models": [], "qty": null, "torque_ref": "2", "uncertain": false, "source": "page"}
  ],
  "torques":   [{"ref": "2", "value": "75-95", "unit": "LBS IN"}],
  "materials": [{"code": "18a", "description": "GREASE", "amount": ".0066 LBS"}],
  "fastening": [{"fastener_items": ["9"], "holds": ["2"], "to": "carburetor bracket", "qty": null,
                 "torque_ref": "2", "note": "View C", "from": "drawing"}],
  "notes": ["Position flange of cable [1] to edge of bracket [2] & clamp [8]."],
  "revisions": [{"date": "5-19-70", "sym": "2", "text": "WAS 3972625 BRKT & DWG REVISED", "was": "3972625", "item": "2"}],
  "options": ["L46"],
  "tables": [],
  "extracted": {"by": "claude-code", "at": "2026-10-24"}
}
```

`models` empty = all models. `from`: `drawing` (read from the picture) or `note` (stated in text).

## 7. Fastener sizes

`data/fasteners.csv`, one row per fastener pn. Filled from catalog tables (GMPartsWiki with permission, or catalog scans run through the same OCR). **Never guessed.** Every row has a source and URL; two agreeing catalogs = `high`. Unknown stays empty. Not needed for M1–M3.

## 8. Pack instructions (GPT system prompt, summarized)

Full text: `prompts/gpt_instructions.md`, copied to `dist/instructions.md` by `build.py`.

- When the user's term isn't the AIM's (halo, birdcage, eyebrow…), name the AIM part and say it's an assumption.
- Facts come from the 1970 AIM; always cite group, sheet and item ("1970 AIM UPC 1 sheet F18, item 3").
- The AIM gives no fastener sizes. Sizes come only from `fasteners.csv` with a source; otherwise say unknown.
- The AIM rarely gives quantities and never an installation order. Say so; any order offered is general knowledge.
- `3972307-8` is a LH/RH pair (3972307 + 3972308); the AIM doesn't say which is which.
- Drawing revision dates are not production dates. 1970 Corvette production began about January 1970.
- Separate "from the manual" from "general knowledge".
- 1970 only; sheet ids and part numbers can differ for 1971–72.
- Tell users to verify against their own manual.

## 9. Acceptance questions

Run in a ChatGPT GPT and a Claude Project with the pack loaded; also assert the facts directly against `aim_parts.csv`.

1. *"What's 9431792 and how is it installed?"* → UPC 1 sheet F18 (p112, coupe 19437) item 3 screw; up through washer 3966796 from under the rear roof panel (View C); holds rear roof upper molding 3972307-8; 2 per side (5/32 holes, use molding as template); △1 20–30 LBS IN. Size (10-32 × 3/8, phosphate) only once fasteners.csv has it. Hard page: item 1 is hole-punched (`?307-8`, registry fills 3972307) and the title-block sheet id is smudged.
2. *"What bolts hold the accelerator cable bracket and what torque?"* → UPC 6 D2: 9419000 bolt item 9, △2 = 75–95 LBS IN.
3. *"What replaced 3972625?"* → D2 revision 5-19-70: bracket item 2, now 3992386.
4. *"What's the door outer molding part number and what holds it?"* → UPC 1 K3 item 1, 3954525-6 (registry fills the punched digits); screws and torque from the drawing.
5. *"Which sheets use 9419000?"* → every sheet, exact (via CSV).
6. *"List torque specs for the front suspension."* → UPC 3.
7. *"What's the halo held on with?"* → via glossary.

Extraction target, on ≥15 hand-verified pages: ≥99% part-number exact match; every miss already flagged `uncertain`.

## 10. Not in v1

MCP server (stdio or hosted), SQLite, Rust, `.mcpb`, diagrams, page images, 1971–72 manuals, vendor links. Revisit a server only if the pack fails real questions.

## 11. Copyright

Ship facts only: numbers, names, quantities, torques, materials, short paraphrased notes, sheet references. No page images, crops or redrawn art. Credit the 1970 Corvette Registry and any catalog source. README disclaimer: unofficial, not affiliated with GM; verify against your manual.

## 12. Milestones (✋ = stop for review)

- **M0 Setup:** git init, `.gitignore`, venv, compile `vision_ocr`, fetch registry to `work/registry.csv`, run `ocr.py` on all pages.
- **M1 Pilot:** extract p4 (A2 index), p14 (A12 chart), p112 (F18), p142 (K3), p148 (K9 faint), p200 (D2), p254 (wiring D1), p285 (option list), p296 (text procedure), p404 (canceled option sheet), p430 (sideways). Run `check.py`, hand-verify into golden set. ✋
- **M2 Full extraction** in batches of ~20; clear review queue. ✋
- **M3 Pack:** glossary seed, `build.py`, test §9 in ChatGPT + Claude, publish GPT + zip. ✋
- **M4 Fasteners** once a catalog source is available.

`STATUS.md` always states the milestone, counts, queue size and the exact next step.
