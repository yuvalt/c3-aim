"""Parse the GM Standard Parts catalog (Section III, English) from its Vision OCR into one row per part number.

    .venv/bin/python std_parts.py
Reads two Vision OCR passes, work/std/ocr1x/ and work/std/ocr2x/ (native and 2x renders of
docs/SECTION III_ENGLISH STANDARD PARTS.pdf); each drops different light cells, so they are merged.
Writes work/std/std_parts.csv (every row) and data/std_parts.csv (only part numbers the 1970 AIM uses).
"""
import csv, json, pathlib, re

PN = re.compile(r"[#*]*(\d{6,8})$")  # catalog marks some numbers with # or *
ROW_TOL = 14  # px; cells on one table row share a baseline within this


LATIN = str.maketrans("АВСЕНКМОРТХаеорсх", "ABCEHKMOPTXaeopcx")  # Vision sometimes returns Cyrillic look-alikes


def rows(boxes):
    """Group OCR boxes into visual rows, top to bottom."""
    out = []
    for b in sorted(boxes, key=lambda b: b["y"]):
        if out and abs(out[-1][0]["y"] - b["y"]) < ROW_TOL:
            out[-1].append(b)
        else:
            out.append([b])
    return [sorted(r, key=lambda b: b["x"]) for r in out]


def center(b):
    return b["x"] + b["w"] / 2


SKIP = {"PART NO.", "PART NO", "GROUP", "PRIME/USE", "PRIMEUSE", "UNIT", "PKG", "PKG.", "QTY.", "PACK"}


def printed_page(boxes):
    """The catalog's own page number, centered at the bottom."""
    nums = [b for b in boxes if re.fullmatch(r"\d{1,3}", b["text"].strip()) and b["y"] > 2900]
    return nums[0]["text"].strip() if nums else ""


def parse_page(n, boxes):
    title, columns, out, cat_page = "", [], [], printed_page(boxes)
    for row in rows(boxes):
        text = [b["text"].strip() for b in row]
        if re.match(r"8\.\d{3}$", text[0]) or re.match(r"8\.\d{3}\s", text[0]):
            group = text[0][:5]
            title = group + " " + " ".join([text[0][5:].strip()] + text[1:]).strip()
            continue
        if any("PART NO" in t.upper() for t in text):
            # header labels: this row plus any label line just above it (e.g. "GROUP / PRIME/USE")
            near = [b for b in boxes if -45 < row[0]["y"] - b["y"] < 30 and b["text"].isupper()]
            columns = [(center(b), b["text"].strip().upper()) for b in near]
            continue
        if not columns:
            continue
        for pb in row:
            m = PN.match(pb["text"].strip())
            if not m:
                continue
            # scans are skewed, so take every box level with this part number, not just its sorted-row neighbours
            mid = pb["y"] + pb["h"] / 2
            level = [b for b in boxes if abs(b["y"] + b["h"] / 2 - mid) < pb["h"] * 0.45 and b is not pb]
            cells = {}
            for b in sorted(level, key=lambda b: b["x"]):
                if PN.match(b["text"].strip()):
                    continue
                col = min(columns, key=lambda c: abs(c[0] - center(b)))[1]
                if col not in SKIP:
                    cells[col] = (cells.get(col, "") + " " + b["text"].strip()).strip()
            cells = {k: v for k, v in cells.items() if v not in ("—", "-", "--")}
            out.append({"pn": m.group(1), "title": title, "cells": cells, "catalog_page": cat_page, "pdf_page": n})
    return out


def parse_pass(folder):
    out = {}
    for f in sorted(pathlib.Path(folder).glob("*.json")):
        boxes = json.loads(f.read_text())
        for b in boxes:
            b["text"] = b["text"].translate(LATIN)
        for r in parse_page(int(f.stem), boxes):
            out.setdefault(r["pn"], r)
    return out


SIZE_COLS = re.compile(r"THREAD|SIZE|LENGTH|DIA|O\.L\.|HOLE|OUTSIDE|INSIDE|THICK")
ONE = r'(#?\d{1,2}-\d+|\d+/\d+-\d+|(\d )?\d+/\d+|\.\d+|\d{1,2}(\.\d+)?|#\d{1,2})'
SIZE = re.compile(rf'^{ONE}( x {ONE})?$')  # 10-32, 1/4-20, 1 3/8, .489, #10, 1/4 x 3/4


def clean(v):
    return v.replace(":", "/").replace('"', "").rstrip(".").strip() if v else v


def merge(a, b):
    """Union of both passes' cells. Values are normalized; for size columns a well-formed value beats garbage.
    Anything still disagreeing, or a size that doesn't look like a size, is kept and flagged."""
    r = dict(a or b)
    r["title"] = (a or {}).get("title") or (b or {}).get("title") or ""
    cells, conflict = {}, []
    for k in dict.fromkeys(list((a or {}).get("cells", {})) + list((b or {}).get("cells", {}))):
        va, vb = clean((a or {}).get("cells", {}).get(k)), clean((b or {}).get("cells", {}).get(k))
        if SIZE_COLS.search(k):
            va, vb = (va if va and SIZE.match(va) else None) or va, (vb if vb and SIZE.match(vb) else None) or vb
            good = [v for v in (va, vb) if v and SIZE.match(v)]
            if good and len(set(good)) == 1:
                cells[k] = good[0]
                continue
        if va and vb and va.lower() != vb.lower():
            cells[k] = f"{va} | {vb}"; conflict.append(k)
        else:
            cells[k] = va or vb
            if SIZE_COLS.search(k) and cells[k] and not SIZE.match(cells[k]):
                cells[k] = "?"  # OCR damage (e.g. "314" for 3/4); show unknown rather than garbage
                conflict.append(k)
    if "DIAMETER" in cells and "HOLE SIZE" in cells:
        cells.pop("DIAMETER HOLE SIZE", None)  # a merged two-line header, duplicates the two columns
        conflict = [c for c in conflict if c != "DIAMETER HOLE SIZE"]
    r["spec"] = "; ".join(f"{k.title()}: {v}" for k, v in cells.items())
    r["ocr_conflict"] = ",".join(conflict)
    return r


def main():
    one, two = parse_pass("work/std/ocr1x"), parse_pass("work/std/ocr2x")
    allrows = [merge(one.get(p), two.get(p)) for p in sorted(one.keys() | two.keys())]
    fixes = {r["pn"]: r["spec"] for r in csv.DictReader(open("data/std_corrections.csv"))}  # rows read by eye where OCR failed
    for r in allrows:
        if r["pn"] in fixes:
            r["spec"], r["ocr_conflict"] = fixes[r["pn"]], ""
    keys = ["pn", "title", "spec", "catalog_page", "pdf_page", "ocr_conflict"]
    with open("work/std/std_parts.csv", "w", newline="") as f:
        w = csv.DictWriter(f, keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(allrows)
    aim = {r["pn"] for r in csv.DictReader(open("work/registry.csv"))}
    for p in pathlib.Path("data/pages").glob("*.json"):
        aim |= {x for part in json.loads(p.read_text()).get("parts", []) for x in re.findall(r"\d{6,7}", part["pn"])}
    used = [r for r in allrows if r["pn"] in aim]
    with open("data/std_parts.csv", "w", newline="") as f:
        w = csv.DictWriter(f, keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(used, key=lambda r: r["pn"]))
    print(f"{len(allrows)} catalog rows, {len(used)} used by the 1970 AIM → data/std_parts.csv")


if __name__ == "__main__":
    main()
