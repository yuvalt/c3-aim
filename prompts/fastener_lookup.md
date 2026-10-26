# Look up GM fastener sizes → data/fasteners/<pn>.json

Your part numbers: ranks given in your task, from data/review/fasteners_queue.csv (pn, AIM name, where it's used on a 1970 Corvette).

For each pn, skip it if data/fasteners/<pn>.json already exists (unless your task says to retry it). Find its size with **`.venv/bin/python search.py "<query>"`** (Bash; Brave Search API, cached, shared cap of paid calls). Do NOT use the WebSearch tool. Use at most 4 search.py queries per part; repeated queries are free (cached). Good first queries: "GM <pn>", "<pn> AMK", "<pn> camaros". You may WebFetch a result page if it isn't blocked.
- Try: the bare number, "GM <pn>", "<pn> screw/bolt/nut", plus where it's used ("<pn> door hinge corvette").
- Good sources: GM standard-parts tables (often only visible as search snippets), NCRS / CorvetteForum / camaros.org / Chevelle/Nova restoration forums, Corvette vendors (Zip, Corvette Central, Paragon, Ecklers, Corvette America, Lectric Limited), AMK Products, Dr. Rebuild, NOS listings, old Chevrolet master parts catalog scans (chevy.oldcarmanualproject.com).
- **If a site returns 403 or a bot check, move on. Never retry with other user agents, headers or tricks.** Search-result snippets are fine to use as a source.
- Two independent sources agreeing = "high". One clear source = "medium". Vague or conflicting = "low" or "conflict". Nothing = "not_found". **Never guess a size**; don't infer from hole sizes or similar numbers.
- Supersessions count (GM number → newer number with a known size), but say so in notes.

What works best (from round 2): WebSearch in **extended** mode with "GM <pn>" and AMK wording ("<pn> AMK", "AMK B-1xxxx <pn>"); AMK's GM cross-reference and the camaros.net hardware lists show up in search snippets even though the sites return 403. Then vendor kits that say "replaces GM #<pn>" (Paragon, Corvette Pacifica, MAM, Zip, Corvette Central, Ecklers, Classic Industries). If data/fasteners/<pn>.json exists from an earlier failed pass, read it, don't repeat its searches, and update it (keep its sources). If sources disagree on one dimension (e.g. length), record that dimension as a range and say so in notes.

Write data/fasteners/<pn>.json:
{"pn": "9431792", "kind": "screw", "thread": "10-32", "length": "3/8", "head": "flat cross-recess", "drive": "phillips",
 "finish": "phosphate", "notes": "", "confidence": "high|medium|low|conflict|not_found",
 "sources": [{"url": "...", "title": "...", "quote": "exact supporting text", "accessed": "2026-10-24"}]}
Unknown fields are null. For washers, spacers and other unthreaded parts put the size in "dims" (e.g. ".39 ID x .74 OD x .06 thick"). Every non-null size field must be backed by a quote in sources.
