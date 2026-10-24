"""Render AIM pages at 300 dpi and OCR them with Apple Vision.

    .venv/bin/python ocr.py --pages 112        # or 1-435; skips pages already done
"""
import argparse, subprocess, pathlib
import pymupdf

PDF = pathlib.Path("docs/1970 CORVETTE ASSEMBLY MANUAL_compressed.pdf")
RENDERS, OCR = pathlib.Path("work/renders"), pathlib.Path("work/ocr")


def page_range(s):
    a, _, b = s.partition("-")
    return range(int(a), int(b or a) + 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="1-435")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    RENDERS.mkdir(parents=True, exist_ok=True)
    OCR.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(PDF)
    for n in page_range(args.pages):
        png, js = RENDERS / f"{n:03d}.png", OCR / f"{n:03d}.json"
        if js.exists() and not args.force:
            continue
        doc[n - 1].get_pixmap(dpi=300, colorspace=pymupdf.csGRAY).save(png)
        js.write_bytes(subprocess.run(["bin/vision_ocr", png], check=True, capture_output=True).stdout)
        print(n, end=" ", flush=True)
    print()


if __name__ == "__main__":
    main()
