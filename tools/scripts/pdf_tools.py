#!/usr/bin/env python3
"""
pdf_tools.py — PDF utilities for the paper-reading-guide skill.

Turns a paper PDF into the raw materials a reading guide needs:
  * full text (so the model can read the prose)
  * rendered page images (so the model can SEE figures, equations, tables)
  * figure-caption coordinates (anchors for cropping figures)
  * precise region crops (to extract a figure into the guide's figs/ folder)

Why a script: these steps are deterministic and fiddly. Doing them by hand
wastes the model's attention; doing them in code makes every guide reproducible.

Dependencies: PyMuPDF  (pip install pymupdf)

Subcommands
-----------
  fetch    URL  -o out.pdf            download a PDF (handles arXiv abs/pdf links)
  text     in.pdf [-o out.txt]        extract full text, page-delimited
  render   in.pdf --pages 1-8 -o DIR  render pages to PNG (to read figures)
  captions in.pdf [--pages 1-12]      find "Figure N" caption positions (JSON)
  images   in.pdf                     inventory embedded raster images + vector density
  crop     in.pdf --page 8 --box x0,y0,x1,y1 -o fig.png    crop a region (PDF points)

Coordinates are in PDF points (72 pt = 1 inch); a Letter page is 612x792.
`captions` and `images` tell you where things are; `crop` pulls them out.
Typical loop: render a page -> look at it -> crop by caption anchor -> verify -> embed.
"""
import argparse, json, os, sys, re, urllib.request

def _fitz():
    try:
        import fitz
        return fitz
    except ImportError:
        sys.exit("PyMuPDF not installed. Run:  pip3 install pymupdf")

def _parse_pages(spec, n):
    """'1-8' / '3' / '1,4,7' / None -> sorted 0-indexed list."""
    if not spec:
        return list(range(n))
    out = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a) - 1, int(b)))
        else:
            out.add(int(part) - 1)
    return sorted(p for p in out if 0 <= p < n)

def cmd_fetch(args):
    url = args.url
    # Normalise arXiv links to the PDF endpoint.
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([\w.]+?)(?:v\d+)?(?:\.pdf)?$", url)
    if m:
        url = f"https://arxiv.org/pdf/{m.group(1)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        data = r.read()
    with open(args.out, "wb") as f:
        f.write(data)
    print(json.dumps({"saved": args.out, "bytes": len(data)}))

def cmd_text(args):
    fitz = _fitz()
    d = fitz.open(args.pdf)
    parts = []
    for i in range(d.page_count):
        parts.append(f"===== PAGE {i+1} =====")
        parts.append(d[i].get_text())
    txt = "\n".join(parts)
    if args.out:
        with open(args.out, "w") as f:
            f.write(txt)
        print(json.dumps({"saved": args.out, "pages": d.page_count, "chars": len(txt)}))
    else:
        sys.stdout.write(txt)

def cmd_render(args):
    fitz = _fitz()
    d = fitz.open(args.pdf)
    os.makedirs(args.out, exist_ok=True)
    m = fitz.Matrix(args.zoom, args.zoom)
    saved = []
    for p in _parse_pages(args.pages, d.page_count):
        pix = d[p].get_pixmap(matrix=m)
        fn = os.path.join(args.out, f"page-{p+1}.png")
        pix.save(fn)
        saved.append({"page": p + 1, "file": fn, "w": pix.width, "h": pix.height})
    print(json.dumps({"zoom": args.zoom, "rendered": saved}, ensure_ascii=False, indent=2))

def cmd_captions(args):
    fitz = _fitz()
    d = fitz.open(args.pdf)
    hits = []
    # Match the common caption openers. Colon/period forms are almost always
    # the caption itself; bare "Figure N" can also be an in-text reference, so
    # we report the variant we matched and let the caller judge.
    for p in _parse_pages(args.pages, d.page_count):
        pg = d[p]
        for n in range(1, 40):
            for variant in (f"Figure {n}:", f"Figure {n}.", f"Fig. {n}:",
                            f"Fig. {n}.", f"Figure {n} ", f"Fig {n}:"):
                for r in pg.search_for(variant):
                    hits.append({"page": p + 1, "label": variant.strip(),
                                 "x": round(r.x0, 1), "y": round(r.y0, 1),
                                 "page_w": round(pg.rect.width),
                                 "page_h": round(pg.rect.height)})
                    break  # one hit per variant is enough as an anchor
    print(json.dumps({"captions": hits}, ensure_ascii=False, indent=2))

def cmd_images(args):
    fitz = _fitz()
    d = fitz.open(args.pdf)
    raster, vector = [], []
    for i in range(d.page_count):
        for x in d[i].get_images(full=True):
            try:
                pix = fitz.Pixmap(d, x[0])
                raster.append({"page": i + 1, "xref": x[0], "w": pix.width, "h": pix.height})
            except Exception:
                pass
        nd = len(d[i].get_drawings())
        if nd > 40:
            vector.append({"page": i + 1, "vector_ops": nd})
    print(json.dumps({
        "raster_images": raster,
        "vector_heavy_pages": vector,
        "hint": "Vector-heavy pages usually hold matplotlib plots/diagrams that "
                "get_images() CANNOT extract — crop those by region instead."
    }, ensure_ascii=False, indent=2))

def cmd_crop(args):
    fitz = _fitz()
    d = fitz.open(args.pdf)
    x0, y0, x1, y1 = (float(v) for v in args.box.split(","))
    pix = d[args.page - 1].get_pixmap(matrix=fitz.Matrix(args.zoom, args.zoom),
                                      clip=fitz.Rect(x0, y0, x1, y1))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    pix.save(args.out)
    print(json.dumps({"saved": args.out, "w": pix.width, "h": pix.height,
                      "kb": round(os.path.getsize(args.out) / 1024)}))

def main():
    ap = argparse.ArgumentParser(description="PDF utilities for paper reading guides")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("fetch"); s.add_argument("url"); s.add_argument("-o", "--out", default="paper.pdf"); s.set_defaults(fn=cmd_fetch)
    s = sub.add_parser("text"); s.add_argument("pdf"); s.add_argument("-o", "--out"); s.set_defaults(fn=cmd_text)
    s = sub.add_parser("render"); s.add_argument("pdf"); s.add_argument("--pages"); s.add_argument("--zoom", type=float, default=2.0); s.add_argument("-o", "--out", default="pages"); s.set_defaults(fn=cmd_render)
    s = sub.add_parser("captions"); s.add_argument("pdf"); s.add_argument("--pages"); s.set_defaults(fn=cmd_captions)
    s = sub.add_parser("images"); s.add_argument("pdf"); s.set_defaults(fn=cmd_images)
    s = sub.add_parser("crop"); s.add_argument("pdf"); s.add_argument("--page", type=int, required=True); s.add_argument("--box", required=True, help="x0,y0,x1,y1 in PDF points"); s.add_argument("--zoom", type=float, default=2.2); s.add_argument("-o", "--out", required=True); s.set_defaults(fn=cmd_crop)

    args = ap.parse_args()
    args.fn(args)

if __name__ == "__main__":
    main()
