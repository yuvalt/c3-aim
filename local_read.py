"""Independent second read of each page's callout list by a local vision model (Ollama).

    .venv/bin/python local_read.py --pages 112 [--model qwen3-vl:8b]
Writes work/local/NNN.json. Skips pages already done.
"""
import argparse, base64, json, pathlib, re, urllib.request
import pymupdf
from ocr import PDF, page_range

OUT = pathlib.Path("work/local")
PROMPT = """This is a sheet from the 1970 Corvette Assembly Instruction Manual.
Read the parts callout list: each line has a boxed item number, a GM part number (6-7 digits, LH/RH pairs like 3966685-6) and a name.
Also read the torque legend (triangle number, value, unit) at the lower left.
Copy exactly. If a digit is unreadable or hidden, write ? for it. Do not guess.
Answer only JSON: {"parts":[{"item":"1","pn":"3966796","name":"WASHER"}],"torques":[{"ref":"1","value":"20-30","unit":"LBS IN"}]}"""


def read_page(doc, n, model):
    png = doc[n - 1].get_pixmap(dpi=150, colorspace=pymupdf.csGRAY).tobytes("png")
    body = {"model": model, "stream": False, "format": "json", "options": {"temperature": 0},
            "messages": [{"role": "user", "content": PROMPT, "images": [base64.b64encode(png).decode()]}]}
    req = urllib.request.Request("http://localhost:11434/api/chat", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    text = json.load(urllib.request.urlopen(req, timeout=900))["message"]["content"]
    return json.loads(re.search(r"\{.*\}", text, re.S).group(0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="1-435")
    ap.add_argument("--model", default="qwen3-vl:8b")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(PDF)
    for n in page_range(args.pages):
        out = OUT / f"{n:03d}.json"
        if out.exists() and not args.force:
            continue
        res = read_page(doc, n, args.model)
        res["model"] = args.model
        out.write_text(json.dumps(res, indent=1))
        print(n, len(res.get("parts", [])), "parts", flush=True)


if __name__ == "__main__":
    main()
