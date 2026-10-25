# STATUS

**Milestone:** M1 pilot done (2026-10-24). Next: M2 full extraction.

## Done
- OCR (Apple Vision, 300 dpi): all 435 pages → `work/renders/`, `work/ocr/`. Preprocessing tested, no gain (87% baseline; see `work/ocr_experiment.py`).
- Extracted 36 pages → `data/pages/`: UPC 0 A2, A3, A12, D1–D10; UPC 1 F18, K1–K15 (full doors); UPC 6 D2; UPC 12 D1 wiring; option pages p285, p296, p404, p430.
- `check.py --fill`: 17 hole-punched part numbers recovered from the 1970 Corvette Registry index. Review queue: 8 rows (`data/review/queue.csv`).
- Pack: `dist/aim_sheets.md` (35 sheet sections + per-section fastener rollups), `dist/aim_parts.csv` (LH/RH pairs split).
- Tests: two blind Q&A rounds (17 questions, all correct); restorer test `tests/restorer_results.md`: 41 questions, 6 answered, 6 partial, 21 not extracted yet, 6 not in AIM, 2 wrong (F18 summary fixed since).
- Forum post draft: `docs/forum_post.md`.

## Open issues
- K3: coupe weatherstrip 3966561-2 missing its fastening link (only the convertible one has it). K8: 3856691 torque 25-35 vs remote control text 35-50. Review in M2.
- Copyright: long procedure text on p143, 146, 147, 151, 153, 296 rewritten in own words (originals in work/notes_backup/, not committed). New extractions follow prompt rule 9.
- p430 (U69 A6): two numbers unreadable, not in registry (option sheets aren't).
- Prompt updates from pilot agents not yet applied: chart part numbers as parts with `source: "table"`, fill-down rule for tables, `uncertain` on torques, rotated-crop command, per-agent crop folders.
- Glossary (`data/glossary.csv`) not started; "halo", "birdcage", "T-top" etc.
- Local model (Qwen-VL via Ollama, `local_read.py`): comparison run stopped before finishing; no results. Re-run if a free second reader is needed.
- Fastener sizes: GM Standard Parts catalog (1989, Section III English, user's PDF in docs/, not committed) parsed by `std_parts.py` from two Vision OCR passes (native + 2x) → `data/std_parts.csv`; 12 rows read by eye in `data/std_corrections.csv`. With the web lookups (`data/fasteners/`): 102 of 551 AIM fastener numbers sized = 27% of fastener callouts. Many 1970 numbers aren't in the 1989 edition; a 1971/74 edition would cover more.

## Next step
Apply the prompt updates, then extract remaining pages in batches of ~20 with parallel agents:
`.venv/bin/python check.py --fill && .venv/bin/python build.py` after each batch.
