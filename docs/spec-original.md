# corvette-aim — Spec

An LLM-queryable knowledge base of the **1970 Corvette Assembly Instruction Manual (AIM, GM 3965172)**, shipped as a **single-file Rust MCP server** that any restorer can download and plug into Claude (or any MCP client) to ask questions like *"What's the screw that holds the door outer reveal molding?"*

This document is the brief for Claude Code. Read it fully before writing code. Work in milestones (§10), stop at each checkpoint for review, and keep `STATUS.md` current so any session can resume.

---

## 1. Goals and non-goals

**Goals**
1. Extract every sheet of the AIM into structured, verifiable data: sheets, every part (not just fasteners), callouts, torques, applied materials, notes, revisions/superseded parts, and **which fastener attaches which part**.
2. Add **fastener sizes** (thread, length, head, finish) for GM part numbers via external lookup, with source URL and confidence for every value. The manual itself mostly gives only GM numbers.
3. Map **restorer vocabulary** to GM vocabulary (glossary): "halo", "birdcage", "T-tops", "eyebrows", "reveal molding" → GM names and sheets.
4. Ship a **Rust MCP server** with the database embedded: one binary per OS, no runtime dependencies, plus an `.mcpb` bundle for one-click install in Claude Desktop.
5. Generate **original diagrams from facts** (fastening chains) as Mermaid/SVG.

**Non-goals**
- No web UI. The interface is an LLM through MCP.
- No redistribution of copyrighted images (GM scans, vendor catalog art). See §9.

**Working principles (important)**
- **Methodical and resumable.** Every step reads inputs from disk, writes outputs to disk, and skips work already done. No step depends on chat memory.
- **Don't burn tokens.** Model-based steps run a **pilot** first (≈10 pages), stop for human review, and only then run in full. Print a cost or volume estimate before any paid batch.
- **Never guess.** An unreadable digit becomes `?` and is flagged. An unknown size stays `null`. Every external fact carries its source.

---

## 2. Source material — what we know

- Input: user's scanned PDF, **435 pages**, letter size, landscape sheets (some pages rotated 90°). Path is configured in `config.toml` (`manual_pdf = "..."`). **Never commit the PDF or rendered images** (add them to `.gitignore`).
- Scans are 1-bit CCITT images at ~250 dpi. The embedded ABBYY OCR text layer is **poor**: unusable for part numbers, OK for coarse keyword hints.
- Reprint by Dave Graham Auto Literature (©2008/2009), licensed from GM.
- PDF page 4 = sheet **A2 General Index**; PDF page 5 = sheet **A3 symbols legend**.

### Sheet anatomy (every assembly sheet)
- **Title block** (bottom right): `1970 CORVETTE SERIES 3965172`, sheet TITLE, **UPC** group (big digit 0–14), **SHEET** id (e.g. `A17`, `D2`, `K7`), model `19000` (= all models), drafting/check dates, optional `Ref.` to related sheets.
- **Callout list** (usually top-left): boxed item number `[n]`, GM part number (usually 7 digits, sometimes 6; LH/RH pairs written `3942747-8`), and abbreviated name (`BOLT`, `SCREW ASM.`, `NUT`, `RIVET`, `CLAMP`, `MLDG`…). The column order varies: `part# [n] NAME` or `[n] part# NAME`.
- **Torque**: a triangle with a number inside (e.g. △2), with a legend at lower left: `△1 45-65 LBS IN`. In the drawing, `[9]△2` means item 9 takes torque #2.
- **Applied materials**: tag like `18a◇`, legend `GREASE – .0066 LBS`. The number is the material and the letter is the usage, both itemized in UPC 0 (sheets D1–D9).
- **Symbols** (sheet A3): `[1]` cross-reference; △ torque; ① revision; ◑ RPO part installed the same as regular production; half-filled square = existing item / part of an assembly; dashed box = related sheets.
- **NOTE** boxes, dimensions (e.g. `.192/.199 DIA (3) HOLES`), VIEW A/B/C detail views.
- **Revision record** (bottom left): date, symbol, text such as `WAS 3972625 BRKT & DWG REVISED`. **These give superseded part numbers; capture them.**
- RPO/option codes (L46, LS5, LT1, ZR1, M21, M22, C60, N40, …).

### Section index (from sheet A2)
- **UPC 0 General:** A1 Introduction, A2 General Index, A3–A4 General Info, A5–A7 General Instructions, A8 Bonding, A9 Stapling, A10–A11 Cowl & dash panel hole piercing (A11 = A/C), A12 Spring Chart, A13 Trim Heights; B1 Labels & Stickers, B2 VIN plate, B3 Protect-O-Plate; C1 Misc. Shipping List, C2 Shipping Protection; D1–D4 Lubrication, D5–D9 Cements & Sealers, D10 Fill items, gasoline & misc.; E1 Paint & Trim (charts 3966750 color & paint, 3966751 color & trim); F1–F2 Water & vacuum water test; G1 Export.
- **UPC 1 Body:** Bolting & welding: A Cowl/dash/door frame, B Underbody/roof/sides, C Final & checking. Assembly: D Dash panel area, E Instrument panel area, F Body complete, G Mounting, H Sealing, J Seats, K Doors, M Heater.
- **UPC 2** Frame. **3** Front suspension. **4** Rear suspension. **5** Brakes (A cylinder mounting & lever, B pipes, C parking). **6** Engine (A belt trains, B cooling/electrical/mounting, C carburetion & exhaust, D controls). **7** Transmission (B floor-mounted controls, C clutch). **8** Fuel & exhaust (A exhaust, B fuel). **9** Steering. **10** Wheels & tires. **11–13** Sheet metal, radiator, grille (A outer panels, B inner panels). **12** Electrical (A engine, B instrument panel, C body, D diagrams). **14** Bumpers & misc. (A front, B rear, C misc.). Then the **Option Index**.

---

## 3. Repository layout

```
corvette-aim/
  SPEC.md                this file
  CLAUDE.md              short: how to run, conventions, pointer to STATUS.md
  STATUS.md              per-step progress, open issues, next action (always current)
  config.toml            manual_pdf path, model ids, batch sizes
  pipeline/              Python 3.11+, uv-managed
    01_render.py
    02_ocr.py
    03_extract.py
    04_validate.py
    05_relations.py
    06_fasteners.py
    07_build_db.py
    08_diagrams.py
    lib/                 shared helpers (paths, schema, json io)
    prompts/extract_page.md
    schema/page.schema.json
  work/                  gitignored: renders/, ocr/, crops/
  data/                  committed (facts only)
    pages/NNN.json       one per PDF page (step 3 output, edited by step 4 review)
    review/              validation reports, human review queue
    fasteners/<pn>.json  one per fastener part number (step 6)
    glossary.csv         restorer term → GM term(s) → sheet(s)
    vendors.csv          part number → vendor page URLs (links only)
    aim.db               built SQLite (step 7)
  server/                Rust MCP server (embeds data/aim.db)
  tests/
    questions.yaml       acceptance questions + expected facts
    golden/              hand-verified pages for extraction accuracy
  .github/workflows/release.yml
```

---

## 4. Pipeline (Python, resumable)

Every script:
- takes `--pages 1-435` (default all), `--force` to redo, and `--dry-run` that prints what would be done;
- skips outputs that already exist and are valid;
- appends a line to `STATUS.md` when it finishes.

### 01_render
`pdftoppm` → `work/renders/NNN.png` at 200 dpi grayscale, plus on-demand 300–400 dpi crops (`work/crops/`) for the callout list and the torque legend. Detect rotated pages (OSD via `tesseract --psm 0`) and save upright.

### 02_ocr
Tesseract `--psm 11` on the 300 dpi render → `work/ocr/NNN.txt`, plus `NNN.tsv` (word boxes). Used only as a **second opinion** for digits.

### 03_extract (model-based, the expensive step)
One page in, one `data/pages/NNN.json` out, validated against `schema/page.schema.json` (§5). Two interchangeable backends:
- `--backend api`: Anthropic Messages API with the page image(s) and `prompts/extract_page.md`. Supports `--batch` (Message Batches API, cheaper, async) and prints a token/cost estimate first. Needs `ANTHROPIC_API_KEY`.
- `--backend manual`: prints the next N unprocessed pages so **Claude Code itself** reads each image and writes the JSON. No API key; uses the Claude plan.

Rules for the extractor prompt:
- Send the full page **plus** a high-res crop of the callout list (part numbers are small).
- Copy text exactly. Unreadable characters become `?` with `uncertain: true`. Never infer digits.
- Record `attaches` relations stated or clearly drawn (see §5). If the relation is ambiguous, leave it out and add a note.
- Expand nothing in `name` (keep GM text verbatim). Put the expansion in `name_expanded` (e.g. `MLDG-DR OTR RVL` → `Molding – door outer reveal`).

**Pilot gate:** run the pilot set first (`tests/golden/` pages plus a mix: A2 index, a chart page such as A12, an engine sheet, a body/door sheet, a wiring diagram). Then stop for human review.

### 04_validate
- Compare each part number with OCR digit strings found near the callout region (TSV boxes). On disagreement, add to `data/review/queue.csv` with a crop path.
- Sanity checks: 6–8 digits, item numbers continuous, torque refs exist in the legend, sheet id matches the title-block pattern, UPC 0–14.
- Cross-sheet consistency: the same part number with conflicting names gets flagged.
- Output `data/review/report.md` (counts, % uncertain, worst pages).
- Review loop: a human (or Claude Code viewing the crop) resolves queue rows by editing `data/pages/NNN.json`. Record `verified_by` and `verified_at` per part.

### 05_relations
Normalize fastening relations into edges: `(sheet, fastener_item → part_item, qty, torque_ref, materials, note)`. Infer **only** the safe patterns: a part's callout listed with its fasteners in the same view with an explicit leader line or note. Everything else stays as extracted. Output goes into the page JSON (`relations` array) with `source: extracted|inferred`.

### 06_fasteners (web lookup)
- Build the queue: every part number whose name matches BOLT, SCREW, NUT, WASHER, STUD, RIVET, CLIP, RETAINER, PIN, SPRING NUT, etc. Output `data/review/fasteners_queue.csv`, sorted by number of sheets that use it.
- For each, Claude Code (WebSearch/WebFetch) or a script finds size facts and writes `data/fasteners/<pn>.json`:
```json
{
  "part_number": "9419000",
  "kind": "bolt",
  "thread": "5/16-18", "length": "3/4", "head": "hex washer", "drive": null,
  "finish": "phosphate", "grade": null, "notes": "",
  "sources": [{"url": "...", "title": "...", "quote": "exact text supporting the size", "accessed": "2026-10-24"}],
  "confidence": "high|medium|low",
  "status": "found|conflict|not_found"
}
```
- Source priority: (1) GM parts catalogs / standard-hardware listings; (2) NCRS technical forums and judging guides; (3) Corvette vendors (Zip Corvette, Corvette Central, Paragon, Eckler's, Lectric Limited, Classic Industries) whose listings quote the GM number; (4) other forums. **Two independent sources = high confidence.** Conflicts are stored, not resolved silently.
- While searching, record vendor page URLs per part in `data/vendors.csv` (links only, no images or descriptions copied).
- Pilot the top 20 fasteners first and stop for review.

### 07_build_db
Build `data/aim.db` (SQLite, FTS5) from `data/`. Deterministic: same inputs produce the same file. Schema:
```
sheets(sheet PK, page, upc, title, section, models, summary, page_type)
parts(id PK, sheet, item, part_number, name, name_expanded, size_printed, qty, notes, torque_ref, uncertain, verified)
torques(sheet, ref, value, unit, items_json)
materials(sheet, code, description, amount, where_text)
notes(sheet, text)
revisions(sheet, date, sym, text, superseded_part, item)
relations(sheet, fastener_item, target_item, qty, torque_ref, materials, note, source)
fasteners(part_number PK, kind, thread, length, head, drive, finish, grade, confidence, status, sources_json)
glossary(term, gm_terms, sheets, note)
vendors(part_number, vendor, url)
fts_parts  (FTS5 over name, name_expanded, part_number, sheet title, summary, notes, glossary terms)
meta(key, value)  -- build date, source manual id, counts, data version
```
Also emit `data/parts.csv` and `data/sheets.json` for people who want raw data.

### 08_diagrams
For each part that has relations, generate a **fastening chain** diagram (Mermaid text, optional SVG via `mmdc`) from facts only: part → fasteners (with size, qty, torque) → mounting surface, with the sheet reference. These are stored in the DB so the MCP server can return them.

---

## 5. Page JSON schema (step 3 output)

```json
{
  "page": 200,
  "sheet": "D2",
  "upc": "6",
  "title": "ACCELERATOR CONTROL CABLE",
  "section": "Engine – Controls",
  "models": "19000",
  "ref_sheets": [],
  "page_type": "assembly|chart|index|text|diagram|blank|cover",
  "summary": "Plain-English 1–3 sentences: what is installed, where, and how it's fastened.",
  "parts": [
    {"item": "9", "part_number": "9419000", "name": "BOLT", "name_expanded": "Bolt",
     "size_printed": null, "qty": null, "notes": "", "torque_ref": "2",
     "uncertain": false, "lr_pair": false}
  ],
  "torques":   [{"ref": "1", "value": "45-65", "unit": "LBS IN", "items": ["7"]}],
  "materials": [{"code": "18a", "description": "GREASE", "amount": ".0066 LBS", "where": "View B"}],
  "relations": [{"fastener_item": "9", "target_item": "2", "qty": null, "note": "", "source": "extracted"}],
  "notes": ["Position flange of cable [1] to edge of bracket [2] & clamp [8]."],
  "dimensions": [],
  "options": [{"code": "L46", "text": ""}],
  "revisions": [{"date": "5-19-70", "sym": "2", "text": "WAS 3972625 BRKT & DWG REVISED", "superseded_part": "3972625", "item": "2"}],
  "tables": [{"title": "", "columns": [], "rows": []}],
  "extraction": {"backend": "api|manual", "model": "", "at": "", "version": 1}
}
```

---

## 6. Glossary

`data/glossary.csv` columns: `term, aliases, gm_terms, sheets, note, source`. Seed it with common C3 restorer terms (halo, birdcage, T-tops / roof panels, eyebrows, rocker molding, reveal molding, kick panel, headlight buckets, rear window, luggage area / storage compartments, etc.), each mapped to the GM names actually found in the extracted data. The user and community add entries over time. The build merges it into FTS so colloquial searches hit GM-named parts.

---

## 7. MCP server (Rust)

- Crate `server/`, using **`rmcp`** (the official Rust MCP SDK) and `rusqlite` with `bundled` + FTS5.
- `aim.db` is embedded with `include_bytes!` and opened in memory (deserialized) at startup. Optional `--data <path>` loads a newer DB instead.
- Transports: **stdio** (default) and **streamable HTTP** (`--http 0.0.0.0:8080`) for hosted use.
- Optional `--manual <path-to-your-own-AIM.pdf>` enables `get_sheet_image`, which renders that sheet's page from **the user's own copy** (pdfium via `pdfium-render`, or extract the CCITT image directly). Nothing copyrighted ships in the binary.

### Tools
All tools return compact JSON plus a short `cite` string (`"1970 AIM sheet K7, item 5"`).

| tool | input | returns |
|---|---|---|
| `search` | `query`, `limit?` | ranked hits across parts, sheets, notes and glossary, each with sheet and why it matched |
| `lookup_part` | `part_number` | every occurrence (sheet, item, name, torque, notes), supersessions (was/now), fastener size record with sources, vendor links |
| `get_sheet` | `sheet` | the full sheet record: parts, torques, materials, notes, relations, revisions, summary |
| `how_attached` | `part_number` or `query` | fastening chain: fasteners with GM number, size, qty, torque, materials, notes, sheet, plus a Mermaid diagram |
| `fastener_size` | `part_number` | size record with confidence and sources (or `not_found`) |
| `torque_specs` | `query?`, `sheet?` | torque values with the items they apply to |
| `list_sheets` | `upc?`, `section?` | sheet index |
| `glossary` | `term` | GM terms and sheets for a restorer term |
| `get_sheet_image` | `sheet` | PNG of that page from the user's own PDF (only when `--manual` is set) |

Server `instructions` text tells the model: always cite sheet and item; separate "from the manual" and "from external lookup"; say when something isn't in the data instead of guessing; suggest `get_sheet_image` when the drawing matters.

### Hosted service
The same binary runs as a public service with `--http`:
- Package as a tiny Docker image (scratch/distroless + static binary). Deploy to Fly.io, Railway, Render or any VPS behind HTTPS. The DB is read-only and in memory, so it needs no database server or volume and runs on the smallest instance.
- Users add the URL (`https://<host>/mcp`) as a custom connector in claude.ai / Claude Desktop, or in any client that supports remote MCP servers. Nothing to install.
- Public read-only data, so **no auth** is needed at first. Add per-IP rate limiting and request logging (tool name and query only, for improving the glossary). Optional API keys later if abuse appears.
- **LLM cost is zero for the host**: the model runs in each user's own Claude or other client; the server only answers lookups.
- `get_sheet_image` is **disabled** in hosted mode (the server never holds the manual).
- `/health` endpoint, and a `/version` endpoint reporting the data version.

### Distribution
- `cargo-dist` + GitHub Actions: on tag, build binaries for macOS arm64/x86_64, Linux x86_64/arm64 and Windows x86_64, and attach them to the GitHub Release with checksums.
- **`.mcpb` bundle** (MCP Bundle, binary server type) per platform for one-click install in Claude Desktop, with `manual_pdf` as an optional user-config field.
- README install snippets for Claude Desktop, Claude Code (`claude mcp add corvette-aim -- /path/to/corvette-aim`), Cursor, and other MCP clients.

---

## 8. Acceptance tests

`tests/questions.yaml` holds natural-language questions with expected facts (sheet, part numbers, size, torque). A test runner (`pipeline/eval.py`) calls the server tools directly and checks the facts; an optional LLM-in-the-loop mode runs the questions through Claude with the MCP server attached. Seed questions:

1. *"What's the screw that connects the door outer reveal molding?"* → screw GM number, size (with source), sheet and item.
2. *"What's the name of the chrome part that sits on the halo and how is it connected to the body?"* → GM part name via the glossary, fasteners/clips and method, sheet. Flag that "chrome" comes from general knowledge unless the sheet states the finish.
3. *"What bolts hold the accelerator cable bracket and what's the torque?"* → sheet D2: 9419000 BOLT (item 9) and its torque from the D2 legend (fill in exact ref/value during M1 verification).
4. *"What does part 3942747 go on?"* → pillar-body hinge, sheet A17.
5. *"What part number replaced 3972625?"* → from the revision records.
6. *"List all torque specs for the front suspension."*
7. *"Which sheets use 9419000?"*

Extraction accuracy target, measured on `tests/golden/` (≥15 hand-verified pages): **≥99% part-number exact match, 0 silent guesses** (every mismatch must already carry `uncertain: true`).

---

## 9. Copyright policy (enforced in code review)

- Commit and ship **facts only**: part numbers, names, quantities, torques, materials, relations, notes paraphrased or short, sheet references.
- **Never** commit or embed GM page images, crops, traced or redrawn GM illustrations, or vendor catalog images and text. Vendor content is **linked** (`vendors.csv`), never copied.
- Diagrams are generated from facts only (§4, step 08).
- Page images are shown only from the **user's own PDF** at runtime (`--manual`).
- README states: unofficial index, not affiliated with GM or any vendor; verify against your manual. (Not legal advice. Consider a permission request to vendors whose catalogs are linked heavily.)

---

## 10. Milestones (stop at each ✋ for review)

1. **M0 – Scaffold.** Repo, config, schema, `STATUS.md`, `.gitignore`, `uv` env. Steps 01–02 run on all pages (cheap, local).
2. **M1 – Extraction pilot.** Step 03 on the ~10-page pilot set, plus step 04. Hand-verify into `tests/golden/`. ✋
3. **M2 – Full extraction.** Remaining pages (batch API or manual backend, in chunks of ≤25 pages, committing after each chunk). Run 04 and clear the review queue. ✋
4. **M3 – Relations + glossary.** Steps 05 and the glossary seed. ✋
5. **M4 – Fasteners pilot (top 20),** then full step 06. ✋
6. **M5 – DB + Rust server (stdio).** Steps 07–08 and all tools. Acceptance tests pass. ✋
7. **M6 – Distribution.** HTTP transport, `--manual` images, cargo-dist release, `.mcpb`, README. ✋
8. **M7 – Hosted service.** Dockerfile, deploy config (Fly.io first), rate limiting, health/version endpoints, connector instructions in README. ✋

`STATUS.md` must always say: the current milestone, what's done (counts), the review queue size, and the exact next command to run.