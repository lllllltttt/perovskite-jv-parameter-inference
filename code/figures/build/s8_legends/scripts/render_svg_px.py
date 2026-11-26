"""Render an SVG (width/height given in CSS px, 96 px/in) to PNG via Edge -> PDF -> raster.

usage: render_svg_px.py <svg> <out.png> [--dpi 600] [--bg white|transparent]
"""
import argparse
import math
import os
import re
import shutil
import subprocess
import tempfile

import pymupdf
from PIL import Image

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CSS_PX_PER_IN = 96.0


def _tmp_root():
    """Scratch on the roomy drive: C: is full, and every Edge run needs a
    private profile of a few tens of MB."""
    root = os.environ.get("SVGR_TMP") or "E:/project/work1/20261116_figs1_split/work/_tmp"
    os.makedirs(root, exist_ok=True)
    return root


def svg_size_px(path):
    """Intrinsic size in CSS px.  A width given in pt (matplotlib writes
    width="784.2pt") is converted at 96/72, otherwise the page would come out
    at 75 % and every dpi figure downstream would be wrong."""
    head = open(path, encoding="utf-8", errors="replace").read(4000)

    def dim(name):
        m = re.search(r"<svg[^>]*?%s=\"([\d.]+)(px|pt)?\"" % name, head)
        v, unit = float(m.group(1)), (m.group(2) or "px")
        return v * (96.0 / 72.0) if unit == "pt" else v

    return dim("width"), dim("height")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svg")
    ap.add_argument("png")
    ap.add_argument("--dpi", type=float, default=600)
    ap.add_argument("--bg", default="white")
    a = ap.parse_args()

    svg = os.path.abspath(a.svg)
    w_px, h_px = svg_size_px(svg)
    w_in, h_in = w_px / CSS_PX_PER_IN, h_px / CSS_PX_PER_IN

    raw = open(svg, encoding="utf-8", errors="replace").read()
    body = raw[raw.index("<svg"):]
    bg = "white" if a.bg == "white" else "transparent"
    p_w = math.ceil(w_in * 100 + 5) / 100.0
    p_h = math.ceil(h_in * 100 + 5) / 100.0
    html = ("<!doctype html><html><head><meta charset='utf-8'><style>"
            "@page{size:%.6fin %.6fin;margin:0}"
            "html,body{margin:0;padding:0;background:%s;}"
            "svg{display:block;position:absolute;left:0;top:0;"
            "width:%.6fin;height:%.6fin}"
            "</style></head><body>%s</body></html>"
            % (p_w, p_h, bg, w_in, h_in, body))

    tmp = tempfile.mkdtemp(prefix="svgr_", dir=_tmp_root())
    hp = os.path.join(tmp, "f.html")
    pp = os.path.join(tmp, "f.pdf")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--user-data-dir=" + os.path.join(tmp, "profile"),
           "--no-first-run", "--no-default-browser-check",
           "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
           "--virtual-time-budget=20000",
           "--print-to-pdf=" + pp, "file:///" + hp.replace("\\", "/")]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if not os.path.exists(pp):
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit("no pdf produced")

    doc = pymupdf.open(pp)
    pg = doc[0]
    zoom = a.dpi / 72.0
    pix = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom),
                        alpha=(a.bg != "white"))
    ox = int(round(w_in * a.dpi))
    oy = int(round(h_in * a.dpi))
    im = Image.frombytes("RGBA" if a.bg != "white" else "RGB",
                         (pix.width, pix.height), pix.samples)
    im = im.crop((0, 0, ox, oy))
    d = os.path.dirname(a.png)
    if d:
        os.makedirs(d, exist_ok=True)
    # embed the dpi tag: without it PowerPoint/Word place a 600-dpi PNG at
    # 96 dpi (6x too large); the pixel size is already right
    im.save(a.png, dpi=(a.dpi, a.dpi))
    shutil.rmtree(tmp, ignore_errors=True)
    print("%-34s %8.4f x %8.4f in -> %5d x %5d px @ %g dpi"
          % (os.path.basename(a.png), w_in, h_in, im.size[0], im.size[1], a.dpi))


if __name__ == "__main__":
    main()
