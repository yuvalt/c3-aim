"""Build the pack: data/pages/*.json → dist/aim_sheets.md + dist/aim_parts.csv.

    .venv/bin/python build.py
"""
import csv, json, pathlib, re
from check import expand

DIST = pathlib.Path("dist")
CODES = {}  # material code -> GM part, filled in main()
UNITS = {"LBS IN": "lb-in", "LBS FT": "lb-ft"}


def torque(t):
    unit = (t.get("unit") or "").rstrip(".")
    return f'{t["value"]} {UNITS.get(unit, unit)}'


def describe(x):
    same = x["name_expanded"].lower().rstrip(".") == x["name"].lower().rstrip(".")
    return x["name"] if same else f'{x["name"]} ({x["name_expanded"]})'


def revision(r, items):
    now = items.get(r["item"], {}).get("pn") if r["item"] else None
    text = f'{r["was"]} replaced by {now} (item {r["item"]})' if r["was"] and now else r["text"]
    return f'- {r["date"] + " " if r["date"] else ""}#{r["sym"]}: {text}'


PN = re.compile(r"^(\d{6,7})\s+(.*)")


def load_sizes():
    """pn -> 'size 10-32 x 3/8 flat phillips, phosphate (high: 2 sources)' for found fasteners."""
    sizes = {}
    for f in pathlib.Path("data/fasteners").glob("*.json"):
        s = json.loads(f.read_text())
        if s.get("confidence") not in ("high", "medium") or not (s.get("thread") or s.get("length")):
            continue
        dims = " x ".join(v for v in (s.get("thread"), s.get("length")) if v) if s.get("thread") else f'length {s["length"]}'
        desc = " ".join(v for v in (s.get("head"), s.get("drive")) if v)
        sizes[s["pn"]] = (f'size {dims}' if s.get("thread") else dims) + (f" {desc}" if desc else "") + (f', {s["finish"]}' if s.get("finish") else "") \
            + f' ({s["confidence"]}: {len(s.get("sources", []))} source{"s" * (len(s.get("sources", [])) != 1)})'
    # GM's own Standard Parts catalog wins over web findings
    std = pathlib.Path("data/std_parts.csv")
    for r in csv.DictReader(std.open()) if std.exists() else []:
        if r["spec"]:
            title = re.sub(r"\s*\(Cont'd\.?\)", "", r["title"], flags=re.I).split(" ", 1)[-1].title()
            page = f'p.{r["catalog_page"]}' if r["catalog_page"] else f'scan page {r["pdf_page"]}'
            group = f'group {r["title"][:5]}, ' if r["title"] else ""
            sizes[r["pn"]] = (f"{title}: " if title else "") + f'{r["spec"]} (GM Standard Parts catalog 1989, {group}{page})'
    return sizes


SIZES = {}  # filled in main()


def material_codes(pages):
    """'55d' -> '9985059 SEALER-BLACK PUMPABLE (UPC 0 sheet D6)', from the D-sheet code tables."""
    codes = {}
    for p in pages:
        for t in p.get("tables", []):
            if "CODE" in t["columns"] and "PART" in t["columns"]:
                ci, pi = t["columns"].index("CODE"), t["columns"].index("PART")
                for row in t["rows"]:
                    codes.setdefault(row[ci], f'{row[pi]} (UPC {p["group"]} sheet {p["sheet"]})')
    return codes


def table_parts(p):
    """Part numbers printed inside chart tables, so the CSV can find them too."""
    for t in p.get("tables", []):
        for row in t["rows"]:
            for cell in row:
                if m := PN.match(str(cell)):
                    yield m.group(1), m.group(2), " · ".join(str(c) for c in row if c != cell)


FASTENER = re.compile(r"\b(SCREW|BOLT|NUT|WASHER|RIVET|STUD|CLIP|RETAINER|PIN|FASTENER|GROMMET|SPACER)\b")


def section_names(pages):
    """('1', 'K') -> 'BODY – Doors', from the general index (UPC 0 sheet A2)."""
    names = {}
    for p in pages:
        for t in p.get("tables", []):
            if t["columns"][:2] == ["upc", "upc_title"]:
                for upc, title, sec, sec_title in t["rows"]:
                    names[(upc, sec)] = f"{title} – {sec_title}" if sec else title
    return names


def fastener_rollups(pages):
    """One section per (group, sheet letter): every fastener, with where it's used and its torque."""
    names, groups = section_names(pages), {}
    for p in pages:
        torques = {t["ref"]: torque(t) for t in p.get("torques", [])}
        items = {x["item"]: f'{x["name_expanded"]} {x["pn"]}' for x in p.get("parts", [])}
        key = (p["group"], p["sheet"][0] if p["group"].isdigit() else "")
        for x in p.get("parts", []):
            if FASTENER.search(x["name"]):
                use = f'{p["sheet"]} item {x["item"]}' + (f' at {torques[x["torque_ref"]]}' if x.get("torque_ref") in torques else "")
                use += f' ({",".join(x["models"])})' if x.get("models") else ""
                use += " [sheet CANCELED]" if p.get("status") == "canceled" else ""
                holds = [items.get(i, f"item {i}") for f in p.get("fastening", []) if x["item"] in f["fastener_items"] for i in f["holds"]]
                use += f' → {", ".join(dict.fromkeys(holds))}' if holds else ""
                groups.setdefault(key, {}).setdefault((x["pn"], x["name"]), []).append(use)
    out = []
    for (g, sec), fasteners in sorted(groups.items()):
        name = names.get((g, sec)) or names.get((g, "")) or g
        out += [f"## 1970 AIM UPC {g} section {sec or g} ({name}): all fasteners", "",
                f"Every screw, bolt, nut, washer, rivet, clip etc. on the extracted {name} sheets. Sizes are not in the AIM.", ""]
        out += [f"- {pn} {n}" + (f" ({SIZES[pn]})" if pn in SIZES else " (size unknown)") + ": " + "; ".join(uses)
                for (pn, n), uses in sorted(fasteners.items())]
        out.append("")
    return "\n".join(out)


def sheet_md(p):
    items = {x["item"]: x for x in p.get("parts", [])}
    label = lambda i: f'[{i}] {items[i]["name_expanded"]} {items[i]["pn"]}' if i in items else f"[{i}]"
    models = ", ".join(p.get("models") or []) or "all models"
    out = [f'## 1970 AIM UPC {p["group"]} sheet {p["sheet"]}: {p["title"]}',
           f'PDF page {p["page"]} · {models}' + (f' · {p["status"].upper()}' if p.get("status", "active") != "active" else ""), "", p["summary"]]
    if p.get("parts"):
        out += ["", "**Parts**"]
    for x in p.get("parts", []):
        extra = [f'torque △{x.get("torque_ref")}'] if x.get("torque_ref") else []
        extra += [f'models {",".join(x.get("models"))}'] if x.get("models") else []
        extra += ["digits uncertain"] if x.get("uncertain") else []
        extra += [SIZES[x["pn"]] + " — size not from the AIM"] if x["pn"] in SIZES else []
        pair = expand(x["pn"])
        pn = f'{x["pn"]} ({pair[0]} / {pair[1]})' if len(pair) == 2 else x["pn"]
        out.append(f'- [{x["item"]}] {pn} {describe(x)}' + (f' — {"; ".join(extra)}' if extra else ""))
    if p.get("torques", []):
        out += ["", "**Torques** (inch-pounds and foot-pounds differ 12×)"] + [f'- △{t["ref"]}: {torque(t)}' for t in p.get("torques", [])]
    if p.get("fastening", []):
        out += ["", "**How it's fastened**"]
        for f in p.get("fastening", []):
            tq = next((f" at {torque(t)}" for t in p.get("torques", []) if t["ref"] == f["torque_ref"]), "")
            qty = f' (qty {f["qty"]})' if f.get("qty") else ""
            what = f' {f.get("how", "holds")} {", ".join(map(label, f["holds"]))}' if f.get("holds") else ""
            to = f' to {f["to"]}' if f.get("to") else ""
            subject = " + ".join(map(label, f["fastener_items"])) or f.get("material") or "Assembly:"
            out.append(f'- {subject}{what}{to}{qty}{tq}. {f.get("note") or ""}')
    if p.get("materials", []):
        out += ["", "**Materials**"] + [f'- {m["code"]} {m["description"]} {m.get("amount") or ""}: {m.get("where") or ""}'
                                        + (f' — code {m["code"]} = GM {CODES[m["code"]]}' if m["code"] in CODES else "")
                                        for m in p.get("materials", [])]
    if p.get("notes", []):
        out += ["", "**Notes**"] + [f"- {n}" for n in p.get("notes", [])]
    if p.get("revisions", []):
        out += ["", "**Revisions**"] + [revision(r, items) for r in p.get("revisions", [])]
    for t in p.get("tables", []):
        out += ["", f'**{t.get("title") or "Table"}**', "", "| " + " | ".join(t["columns"]) + " |", "|" + "---|" * len(t["columns"])]
        out += ["| " + " | ".join(str(c).replace("|", "/") for c in row) + " |" for row in t["rows"]]
    return "\n".join(out) + "\n"


def main():
    DIST.mkdir(exist_ok=True)
    pages = [json.loads(f.read_text()) for f in sorted(pathlib.Path("data/pages").glob("*.json"))]
    CODES.update(material_codes(pages))
    SIZES.update(load_sizes())
    (DIST / "aim_sheets.md").write_text("\n".join(sheet_md(p) for p in pages) + "\n" + fastener_rollups(pages))
    with (DIST / "aim_parts.csv").open("w", newline="") as f:
        w = csv.writer(f)
        # one row per part number: LH/RH pairs are split so either number can be looked up
        w.writerow(["pn", "pair", "item", "name", "name_expanded", "group", "sheet", "title", "page", "models", "torque", "uncertain", "context", "size"])
        for p in pages:
            torques = {t["ref"]: torque(t) for t in p.get("torques", [])}
            for x in p.get("parts", []):
                for pn in expand(x["pn"]):
                    w.writerow([pn, x["pn"] if "-" in x["pn"] else "", x["item"], x["name"], x["name_expanded"], p["group"], p["sheet"],
                                p["title"], p["page"], ",".join(x.get("models") or p.get("models") or []),
                                torques.get(x.get("torque_ref"), ""), x.get("uncertain"), "", SIZES.get(pn, "")])
            for pn, name, context in table_parts(p):
                w.writerow([pn, "", "", name, "", p["group"], p["sheet"], p["title"], p["page"], "", "", "", context, ""])
    (DIST / "instructions.md").write_text(pathlib.Path("prompts/gpt_instructions.md").read_text())
    print(f"{len(pages)} sheets → dist/")


if __name__ == "__main__":
    main()
