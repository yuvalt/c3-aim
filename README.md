# c3-aim

Ask ChatGPT or Claude about your C3 Corvette's Assembly Instruction Manual (AIM): part numbers, torques, sealers, and what bolts to what. Starting with the 1970 AIM.

> **Q: Found part 9431792 in a bag. What is it?**
> Sheet F18, item 3. Screw that holds the rear roof upper molding (3972307-8) to the roof panel, 2 per side, 20–30 in-lb. It goes up from under the panel through washer 3966796.

## Status

Pilot: the doors section (K1–K15), the rear window molding sheet (F18), the lubricant/sealer code charts (D1–D10) and a few others, about 35 of 435 pages. See [STATUS.md](STATUS.md).

Fastener sizes are mostly missing. The AIM gives only GM part numbers. If you have the GM Standard Parts Catalog, please open an issue.

## Use it

Build the pack, then load it into your chat app:

```
python3 -m venv .venv && .venv/bin/pip install pymupdf
.venv/bin/python build.py      # writes dist/
```

- **ChatGPT**: create a GPT (or Project), paste `dist/instructions.md` as instructions, upload `dist/aim_sheets.md` and `dist/aim_parts.csv`, enable Code Interpreter.
- **Claude**: create a Project, paste `dist/instructions.md` as project instructions, add the two files.
- **Gemini Gems / NotebookLM**: add the two files as sources.

## How it's made

1. `ocr.py`: renders each page of your own AIM PDF and OCRs it locally (Apple Vision, macOS).
2. Claude reads each page image and writes `data/pages/NNN.json` per [prompts/extract.md](prompts/extract.md): callouts, torques, materials, notes, revisions, and what fastens to what.
3. `check.py`: cross-checks part numbers against the OCR and the [1970 Corvette Registry AIM index](http://1970corvetteregistry.org/aim/aimstatic.html); `--fill` recovers digits hidden by binder holes when the registry has exactly one match.
4. `build.py`: turns `data/` into the pack in `dist/`.

Design and decisions: [docs/spec.md](docs/spec.md).

## Notes

- Facts only, in our own words: part numbers, names, torques, materials, sheet references. No scans, drawings or copied pages. You need your own AIM for the pictures; every answer cites the sheet so you can check it.
- Unofficial. Not affiliated with GM, Chevrolet or NCRS. Verify everything against your manual.
- Thanks to the 1970 Corvette Registry for their AIM index.
