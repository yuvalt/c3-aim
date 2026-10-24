# Look up GM fastener sizes → data/fasteners/<pn>.json

Your part numbers: ranks given in your task, from data/review/fasteners_queue.csv (pn, AIM name, where it's used on a 1970 Corvette).

For each pn, skip it if data/fasteners/<pn>.json already exists. Otherwise find its size with WebSearch / WebFetch:
- Try: the bare number, "GM <pn>", "<pn> screw/bolt/nut", plus where it's used ("<pn> door hinge corvette").
- Good sources: GM standard-parts tables (often only visible as search snippets), NCRS / CorvetteForum / camaros.org / Chevelle/Nova restoration forums, Corvette vendors (Zip, Corvette Central, Paragon, Ecklers, Corvette America, Lectric Limited), AMK Products, Dr. Rebuild, NOS listings, old Chevrolet master parts catalog scans (chevy.oldcarmanualproject.com).
- **If a site returns 403 or a bot check, move on. Never retry with other user agents, headers or tricks.** Search-result snippets are fine to use as a source.
- Two independent sources agreeing = "high". One clear source = "medium". Vague or conflicting = "low" or "conflict". Nothing = "not_found". **Never guess a size**; don't infer from hole sizes or similar numbers.
- Supersessions count (GM number → newer number with a known size), but say so in notes.

Write data/fasteners/<pn>.json:
{"pn": "9431792", "kind": "screw", "thread": "10-32", "length": "3/8", "head": "flat cross-recess", "drive": "phillips",
 "finish": "phosphate", "notes": "", "confidence": "high|medium|low|conflict|not_found",
 "sources": [{"url": "...", "title": "...", "quote": "exact supporting text", "accessed": "2026-10-24"}]}
Unknown fields are null. Every non-null size field must be backed by a quote in sources.
