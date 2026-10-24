"""Cross-check extracted part numbers against Apple Vision OCR, the local model and the 1970 Corvette Registry.

    .venv/bin/python check.py --pages 112
Writes data/review/queue.csv (one row per disagreement) and prints a summary.
"""
import argparse, csv, html, json, pathlib, re, urllib.request
from ocr import page_range

REGISTRY_URL = "http://1970corvetteregistry.org/aim/aimstatic.html"
REGISTRY = pathlib.Path("work/registry.csv")
QUEUE = pathlib.Path("data/review/queue.csv")


def registry():
    """{(upc, sheet): {pn: name}}; downloaded once and cached. Registry page = our page - 2."""
    if not REGISTRY.exists():
        t = urllib.request.urlopen(REGISTRY_URL, timeout=60).read().decode("cp1252")
        rows = []
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S):
            cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(cells) == 6 and cells[0] != "codigo":
                rows.append(cells)
        with REGISTRY.open("w", newline="") as f:
            csv.writer(f).writerows([["pn", "name", "upc", "sheet", "title", "page"]] + rows)
    reg = {}
    for r in csv.DictReader(REGISTRY.open()):
        reg.setdefault((r["upc"], r["sheet"]), {})[r["pn"]] = r["name"]
    return reg


def expand(pn):
    """'3966685-6' -> ['3966685', '3966686']; '3954589-90' -> ['3954589', '3954590']."""
    base, _, tail = pn.partition("-")
    return [base] if not tail else [base, base[: len(base) - len(tail)] + tail]


def candidates(registry_pns, pattern):
    # a binder hole can hide more digits than the reader counted, so a run of ? matches 1+ digits
    rx = re.compile("^" + re.sub(r"\?+", r"\\d+", pattern) + "$")
    return [p for p in registry_pns if rx.match(p)]


def check_page(n, reg, queue, fill=False):
    path = pathlib.Path(f"data/pages/{n:03d}.json")
    page = json.loads(path.read_text())
    ocr_path, local_path = pathlib.Path(f"work/ocr/{n:03d}.json"), pathlib.Path(f"work/local/{n:03d}.json")
    ocr_tokens = {w for b in json.loads(ocr_path.read_text()) for w in re.findall(r"[\d?]{6,7}(?:-\d{1,2})?", b["text"])} if ocr_path.exists() else set()
    local = {p["item"] + ":" + p["pn"] for p in json.loads(local_path.read_text()).get("parts", [])} if local_path.exists() else None
    reg_pns = reg.get((page["group"], page["sheet"]), {})
    ours = {m for t in page.get("tables", []) for row in t["rows"] for c in row for m in re.findall(r"\b\d{6,7}\b", str(c))}
    ours |= {x for p in page["parts"] if "?" not in p["pn"] for x in expand(p["pn"])}

    def flag(item, pn, issue, hint=""):
        queue.append({"page": n, "sheet": f'{page["group"]}/{page["sheet"]}', "item": item, "pn": pn, "issue": issue, "hint": hint})

    for p in page["parts"]:
        pns = expand(p["pn"])
        if "?" in p["pn"]:
            fills = [c for c in candidates(reg_pns, pns[0]) if c not in ours]
            tail = p["pn"].partition("-")[2]
            if tail and len(fills) > 1:  # LH/RH pair: both halves match the base pattern; keep the one whose partner exists
                fills = [c for c in fills if (mate := expand(f"{c}-{tail}")[1]) != c and mate in reg_pns] or fills
            if fill and len(fills) == 1:
                p.update(pn=fills[0] + ("-" + tail if tail else ""), uncertain=False, source="registry")
                ours.update(expand(p["pn"]))
                continue
            flag(p["item"], p["pn"], "unreadable digits", "registry: " + ",".join(fills) if fills else "no registry match")
            continue
        if p.get("source") == "registry":
            continue
        if not re.fullmatch(r"\d{6,7}(-\d{1,2})?", p["pn"]):
            flag(p["item"], p["pn"], "bad format")
        if ocr_tokens and p["pn"] not in ocr_tokens and pns[0] not in ocr_tokens:
            flag(p["item"], p["pn"], "OCR disagrees", "registry agrees" if pns[0] in reg_pns else "")
        if local is not None and f'{p["item"]}:{p["pn"]}' not in local:
            flag(p["item"], p["pn"], "local model disagrees", "registry agrees" if pns[0] in reg_pns else "")
        if reg_pns and not set(pns) & reg_pns.keys():
            flag(p["item"], p["pn"], "not in registry")
    unread = [x for p in page["parts"] if "?" in p["pn"] for x in expand(p["pn"])]
    for pn in reg_pns.keys() - ours:
        if not any(candidates([pn], x) for x in unread):
            flag("", pn, "registry has it, we don't", reg_pns[pn])
    if fill:
        path.write_text(json.dumps(page, indent=2, ensure_ascii=False) + "\n")
    refs = {t["ref"] for t in page.get("torques", [])}
    for p in page["parts"]:
        if p["torque_ref"] and p["torque_ref"] not in refs:
            flag(p["item"], p["pn"], f'torque ref {p["torque_ref"]} not in legend')
    return len(page["parts"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="1-435")
    ap.add_argument("--fill", action="store_true", help="fill hole-punched digits when the registry has exactly one match")
    args = ap.parse_args()
    reg, queue, parts = registry(), [], 0
    for n in page_range(args.pages):
        if pathlib.Path(f"data/pages/{n:03d}.json").exists():
            parts += check_page(n, reg, queue, args.fill)
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE.open("w", newline="") as f:
        w = csv.DictWriter(f, ["page", "sheet", "item", "pn", "issue", "hint"])
        w.writeheader()
        w.writerows(queue)
    print(f"{parts} parts checked, {len(queue)} in review queue")
    for q in queue:
        print(" ", q)


if __name__ == "__main__":
    main()
