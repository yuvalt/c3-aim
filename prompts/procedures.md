# Extract service procedures → data/procedures/NNN.json

Source: `docs/ilide.info-1968-chevrolet-chassis-service-manual-*.pdf` (GM 1968 Chevrolet Chassis Service Manual). It has a text layer (`page.get_text()`), but columns can come out jumbled: always look at the page image too (render with pymupdf at ~150 dpi into `work/svc/`, crop to zoom). One JSON per PDF page: `data/procedures/NNN.json` (NNN = PDF page, 3 digits). Skip pages that already exist.

```json
{
  "page": 98,
  "source": "1968 Chevrolet Chassis Service Manual, Corvette Body, p.1B-13",
  "procedures": [
    {
      "title": "Door window inner molding: remove and install",
      "topic": "doors",
      "parts": ["door window inner molding", "window seals"],
      "steps": ["Remove the window glass (see Window Glass).", "Remove the inner and outer window seals.", "Through the access holes in the inner door panel, remove the 5 screws along the face of the molding.", "Lift the molding up and out.", "Install in reverse order."],
      "specs": [{"what": "door striker bolt", "value": "46 lb-ft"}],
      "notes": ["Corvette coupe and convertible differ: …"],
      "continues": false
    }
  ]
}
```

Rules:
1. **Own words.** Rewrite every step as a short imperative sentence. Keep every fact (order, counts, fastener types, tools, values, cautions). Never copy runs of more than ~6 words.
2. **Only Corvette content** in this section; skip anything for other models.
3. Keep numbers exact. Unreadable → `?`. Never invent a step, count or value.
4. `specs`: torque values, clearances, adjustments with units exactly as printed.
5. A procedure that continues onto the next page: set `"continues": true` and put the rest on the next page's file under the same title.
6. `topic`: one of doors, windows, glass, moldings, weatherstrip, roof, hardtop, convertible-top, hood, body, interior, seats, trim, fiberglass-repair, lamps, other.
7. Figures: refer to them only as "see figure N in the manual"; describe what they show if it matters for a step.
