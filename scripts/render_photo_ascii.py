#!/usr/bin/env python3
"""
Render data/avatar.jpg (written by fetch_avatar.py) as a monochrome ASCII
density grid: grayscale + contrast/gamma tuned, mapped through the same
sparse -> dense RAMP used by the 3D wordmark, inside a matching terminal-
styled card. Rows wipe in left-to-right one at a time, staggered
top-to-bottom (typewriter reveal), then hold.

Plain Pillow only - no background removal, no face isolation. The avatar
is rendered as-is, whatever it is.

Run by .github/workflows/update-profile-art.yml after fetch_avatar.py.
"""
import argparse
import html
import os

import numpy as np
from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "avatar.jpg")
OUT_PATH = os.path.join(HERE, "..", "photo-ascii.svg")

COLS = int(os.environ.get("PHOTO_COLS", 90))
CELL_W = 9.4    # matches make_wordmark_svg.py's cell metrics so both
CELL_H = 16.0   # panels share the same glyph density/texture

CONTRAST = float(os.environ.get("PHOTO_CONTRAST", 1.3))
GAMMA = float(os.environ.get("PHOTO_GAMMA", 1.0))
# empirically, bright px -> dense char reads better than the inverted
# "pencil sketch" convention for this source (a scene, not a face on a
# plain background) - most of the frame is mid-dark, so inverting floods
# the grid with ink and the shape washes out. see photo_a/b/c/d in the
# tuning pass: non-inverted at higher COLS was the clear winner.
INVERT = os.environ.get("PHOTO_INVERT", "0") == "1"

RAMP = " .`:-=+*czS#%@"
INK = "#2dd4bf"

BG_TOP = "#111722"
BG_BOTTOM = "#0d1117"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"

PAD = 18
TITLEBAR_H = 28

REVEAL_ROW_STAGGER = 0.035
REVEAL_ROW_DUR = 0.45


def to_ascii(path):
    im = Image.open(path).convert("L")
    w, h = im.size
    rows_n = max(1, round(COLS * (h / w) * (CELL_W / CELL_H)))
    im = im.resize((COLS, rows_n), Image.Resampling.LANCZOS)
    im = ImageEnhance.Contrast(im).enhance(CONTRAST)
    arr = np.asarray(im, dtype=np.float64) / 255.0
    if INVERT:
        arr = 1.0 - arr
    arr = np.clip(arr, 0.0, 1.0) ** GAMMA
    idx = np.clip((arr * (len(RAMP) - 1)).round().astype(int), 0, len(RAMP) - 1)
    rows_txt = ["".join(RAMP[i] for i in row) for row in idx]
    return rows_txt, COLS, rows_n


def emit(rows_txt, cols, rows_n, out):
    art_w = cols * CELL_W
    art_h = rows_n * CELL_H
    canvas_w = art_w + PAD * 2
    canvas_h = TITLEBAR_H + art_h + PAD
    art_top = TITLEBAR_H + PAD * 0.3
    fs = CELL_H * 0.9

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w:.0f}" height="{canvas_h:.0f}" '
        f'viewBox="0 0 {canvas_w:.0f} {canvas_h:.0f}" font-family="ui-monospace, SFMono-Regular, '
        f'Menlo, Consolas, monospace">',
        '<defs><linearGradient id="pbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOTTOM}"/>'
        '</linearGradient></defs>',
        f'<rect width="{canvas_w:.0f}" height="{canvas_h:.0f}" rx="12" fill="url(#pbg)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1:.0f}" height="{canvas_h-1:.0f}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w:.0f}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{PAD + i*15}" cy="{TITLEBAR_H/2}" r="4.5" fill="{dot}"/>')
    p.append(f'<text x="{canvas_w/2:.0f}" y="{TITLEBAR_H/2 + 4:.0f}" fill="{TITLE_TEXT}" '
             f'font-size="11.5" text-anchor="middle">nikhil@github: ~$ ./avatar.sh --ascii</text>')

    for ry, line in enumerate(rows_txt):
        y_top = art_top + ry * CELL_H
        y_text = y_top + CELL_H * 0.78
        begin = ry * REVEAL_ROW_STAGGER
        clip_id = f"prow{ry}"
        p.append(
            f'<clipPath id="{clip_id}"><rect x="{PAD}" y="{y_top:.1f}" height="{CELL_H:.1f}" width="0">'
            f'<animate attributeName="width" from="0" to="{art_w:.1f}" begin="{begin:.3f}s" '
            f'dur="{REVEAL_ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
        )
        p.append(
            f'<g clip-path="url(#{clip_id})"><text xml:space="preserve" x="{PAD}" y="{y_text:.1f}" '
            f'font-size="{fs:.1f}" fill="{INK}" textLength="{art_w:.1f}" lengthAdjust="spacing">'
            f'{html.escape(line)}</text></g>'
        )

    p.append("</svg>")
    svg = "".join(p)
    with open(out, "w") as fh:
        fh.write(svg)
    print(f"wrote {out}  {len(svg)/1024:.1f} KB  {cols}x{rows_n}  {canvas_w:.0f}x{canvas_h:.0f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=IN_PATH)
    ap.add_argument("--out", default=OUT_PATH)
    ap.add_argument("--preview", action="store_true", help="print the ASCII grid to stdout instead of writing")
    a = ap.parse_args()

    rows_txt, cols, rows_n = to_ascii(a.inp)
    if a.preview:
        for row in rows_txt:
            print(row)
        return
    emit(rows_txt, cols, rows_n, a.out)


if __name__ == "__main__":
    main()
