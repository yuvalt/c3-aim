"""Find printed sizes for unsized AIM fasteners in the Corvette parts catalogs (14A fiches 1-6, 1953-73 P&A).

    .venv/bin/python catalog_sizes.py      -> work/catalog_candidates.json (each needs a by-eye check)
Reads Vision OCR in work/fiche1..6/ocr and work/pa73/ocr. A candidate is the catalog line holding the
part number (same text row, same page column) whose description prints a size in parentheses or after a comma.
"""
import csv, glob, json, re, collections
from check import expand

SOURCES = {f"work/fiche{n}": f"Corvette Parts & Illustration Catalog 14A (rev. 12-83), fiche {n}" for n in range(1, 7)}
SOURCES["work/pa73"] = "Corvette Parts & Accessories Catalog 1953-73 (rev. 1-75)"
FAST = re.compile(r"\b(SCREW|BOLT|NUT|WASHER|RIVET|STUD|PIN|SPACER)\b")
SIZE = re.compile(r'(#?\d{1,2}\s*-\s*\d{2}|\d+/\d+"?\s*-\s*\d+|\d+/\d+"?\s*[xX]\s*[\d/ -]+|\.\d+\s*[xX]|#\d+\b)')


def unsized():
    uses, names = collections.Counter(), {}
    for f in glob.glob("data/pages/*.json"):
        for x in json.load(open(f)).get("parts", []):
            if "?" in x["pn"] or not FAST.search(x["name"]):
                continue
            for pn in expand(x["pn"]):
                uses[pn] += 1; names.setdefault(pn, x["name"])
    std = {r["pn"] for r in csv.DictReader(open("data/std_parts.csv")) if r["spec"]}
    found = {json.load(open(f))["pn"] for f in glob.glob("data/fasteners/*.json") if json.load(open(f))["confidence"] in ("high", "medium")}
    return {p: (names[p], uses[p]) for p in uses if p not in std | found}


def main():
    want, out = unsized(), []
    for folder, title in SOURCES.items():
        for f in sorted(glob.glob(f"{folder}/ocr/*.json")):
            boxes = json.load(open(f)); page = int(f[-8:-5]); mid = max((b["x"] + b["w"] for b in boxes), default=2000) / 2
            for b in boxes:
                for pn in re.findall(r"\b\d{6,8}\b", b["text"]):
                    if pn not in want:
                        continue
                    side = (b["x"] < mid)
                    row = sorted([c for c in boxes if abs(c["y"] - b["y"]) < b["h"] * 0.7 and (c["x"] < mid) == side], key=lambda c: c["x"])
                    text = " | ".join(c["text"] for c in row)
                    if SIZE.search(text) and FAST.search(text.upper()):
                        out.append({"pn": pn, "aim_name": want[pn][0], "uses": want[pn][1], "source": title, "folder": folder,
                                    "page": page, "y": b["y"], "h": b["h"], "x0": min(c["x"] for c in row), "row": text})
    seen, uniq = set(), []
    for c in sorted(out, key=lambda c: -c["uses"]):
        if (c["pn"], c["folder"]) not in seen:
            seen.add((c["pn"], c["folder"])); uniq.append(c)
    json.dump(uniq, open("work/catalog_candidates.json", "w"), indent=1)
    print(len(want), "unsized fasteners;", len(uniq), "candidate lines;", len({c['pn'] for c in uniq}), "distinct parts")


if __name__ == "__main__":
    main()
