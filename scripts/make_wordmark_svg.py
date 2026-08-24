#!/usr/bin/env python3
"""
Render a word as an extruded 3D block, rasterize the extrusion to ASCII
characters, and emit the result as an animated SVG.

GitHub's <img> sandbox executes SVG SMIL animation but never JavaScript or
CSS animation-on-load reliably across renders, so the rock/oscillate motion
below is done as a flipbook: one pre-rendered ASCII frame per pose, cycled
with a discrete SMIL <animate> on each frame's opacity.

Pipeline: rasterize the text with a bold TTF -> threshold into a boolean
mask -> build a voxel shell from that mask (front/back caps + boundary
side walls) -> rotate the shell frame-by-frame and project it in
perspective -> z-buffer splat each frame into a character grid, picking a
character by Lambertian shading of the local surface normal.
"""
import argparse
import html
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))

TEXT = os.environ.get("WORDMARK_TEXT", "NIKHIL")
FONT_PATH = os.environ.get("WORDMARK_FONT", os.path.join(HERE, "fonts", "ArchivoBlack-Regular.ttf"))

COLS = int(os.environ.get("WORDMARK_COLS", 100))
ROW_MARGIN = int(os.environ.get("WORDMARK_ROW_MARGIN", 3))
CELL_W = 9.4
CELL_H = 16.0

MASK_H = 260               # glyph raster height in mask px, drives voxel density
TRACKING = 0.10             # extra letter-spacing (em); keeps counters open post-extrude
DEPTH_FRAC = 0.32           # extrusion depth as a fraction of glyph height
TILT_DEG = 4.0              # fixed camera tilt so the top face stays lit and readable
CAM_DIST = 6.0              # camera distance in word-widths
FOCAL = 4.1
FIT = 0.92                  # fraction of the grid the widest rotation frame may use

RAMP = " .`:-=+*czS#%@"     # sparse/dim -> dense/bright, index 0 is blank
LIGHT = np.array([-0.20, -0.40, -1.0])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
AMBIENT = 0.24
FOG = 0.30
FOG_SPAN = 0.55

BG_TOP = "#111722"
BG_BOTTOM = "#0d1117"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#2dd4bf"

PAD = 18
TITLEBAR_H = 28


def build_shell():
    probe = TEXT.replace("\n", "")
    font_size = MASK_H
    font = ImageFont.truetype(FONT_PATH, font_size)
    for _ in range(40):
        font = ImageFont.truetype(FONT_PATH, font_size)
        l, t, r, b = font.getbbox(probe)
        if b - t <= MASK_H:
            break
        font_size = int(font_size * 0.92)
    h = b - t
    track = int(round(TRACKING * font_size))

    def word_w(s):
        return sum(font.getlength(c) for c in s) + track * (len(s) - 1)

    total_w = int(round(word_w(probe))) + 8
    total_h = h + 8
    img = Image.new("L", (total_w, total_h), 0)
    d = ImageDraw.Draw(img)
    pen = 4.0
    base = -t + 4
    for ch in probe:
        d.text((pen, base), ch, font=font, fill=255)
        pen += font.getlength(ch) + track
    mask = np.array(img) > 127
    xs_any = np.nonzero(mask.any(0))[0]
    ys_any = np.nonzero(mask.any(1))[0]
    mask = mask[ys_any[0]:ys_any[-1] + 1, xs_any[0]:xs_any[-1] + 1]

    H, W = mask.shape
    depth = max(4, int(round(H * DEPTH_FRAC)))
    cy, cx = np.nonzero(mask)

    pts, nrm = [], []
    front = np.stack([cx, cy, np.full_like(cx, -0.6, dtype=float)], 1)
    pts.append(front)
    nrm.append(np.tile([0.0, 0.0, -1.0], (len(front), 1)))
    back = np.stack([cx, cy, np.full_like(cx, depth)], 1).astype(float)
    pts.append(back)
    nrm.append(np.tile([0.0, 0.0, 1.0], (len(back), 1)))

    pad = np.pad(mask, 1)
    empty_r = ~pad[1:-1, 2:]
    empty_l = ~pad[1:-1, :-2]
    empty_d = ~pad[2:, 1:-1]
    empty_u = ~pad[:-2, 1:-1]
    edge = mask & (empty_r | empty_l | empty_d | empty_u)
    ey, ex = np.nonzero(edge)
    nx = empty_r[ey, ex].astype(float) - empty_l[ey, ex].astype(float)
    ny = empty_d[ey, ex].astype(float) - empty_u[ey, ex].astype(float)
    ln = np.sqrt(nx * nx + ny * ny)
    ln[ln == 0] = 1.0
    nx, ny = nx / ln, ny / ln
    zsteps = np.linspace(0, depth, max(3, depth // 2))
    for z in zsteps:
        pts.append(np.stack([ex, ey, np.full_like(ex, z, dtype=float)], 1))
        nrm.append(np.stack([nx, ny, np.zeros_like(nx)], 1))

    P = np.concatenate(pts).astype(np.float32)
    N = np.concatenate(nrm).astype(np.float32)
    P[:, 0] -= W / 2.0
    P[:, 1] -= H / 2.0
    P[:, 2] -= depth / 2.0
    P /= float(W)
    return P, N


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float32)


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float32)


def project(P, N, yaw):
    M = rot_x(math.radians(TILT_DEG)) @ rot_y(yaw)
    p = P @ M.T
    n = N @ M.T
    vis = n[:, 2] < 0.0
    p, n = p[vis], n[vis]

    z = p[:, 2] + CAM_DIST
    f = FOCAL / z
    lam = n @ LIGHT
    inten = AMBIENT + (1 - AMBIENT) * np.clip(lam, 0, 1)
    t = np.clip((z - CAM_DIST) / FOG_SPAN, -1.0, 1.0)
    inten *= 1.0 - FOG * (t + 1.0) / 2.0
    idx = np.clip((inten * (len(RAMP) - 1)).round().astype(int), 1, len(RAMP) - 1)
    return p[:, 0] * f, p[:, 1] * f, z, idx


def fit(projected):
    xs = np.concatenate([q[0] for q in projected])
    ys = np.concatenate([q[1] for q in projected])
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    ar = CELL_W / CELL_H
    scale = FIT * (COLS - 1) / (x1 - x0)
    rows = int(math.ceil((y1 - y0) * ar * scale)) + 1 + 2 * ROW_MARGIN
    cx = (COLS - 1) / 2.0 - (x0 + x1) / 2.0 * scale
    cy = (rows - 1) / 2.0 - (y0 + y1) / 2.0 * scale * ar
    return scale, cx, cy, rows


def rasterize(q, scale, cx, cy, rows):
    x, y, z, idx = q
    col = np.round(cx + x * scale).astype(int)
    row = np.round(cy + y * scale * (CELL_W / CELL_H)).astype(int)
    ok = (col >= 0) & (col < COLS) & (row >= 0) & (row < rows)
    col, row, z, idx = col[ok], row[ok], z[ok], idx[ok]

    grid = np.zeros((rows, COLS), np.int8)
    order = np.argsort(-z)
    grid[row[order], col[order]] = idx[order]
    return ["".join(RAMP[i] for i in r) for r in grid]


def emit(frames, rows, out, dur, reveal):
    art_w = COLS * CELL_W
    art_h = rows * CELL_H
    canvas_w = art_w + PAD * 2
    canvas_h = TITLEBAR_H + art_h + PAD
    art_top = TITLEBAR_H + PAD * 0.3
    fs = CELL_H * 0.9
    n = len(frames)

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w:.0f}" height="{canvas_h:.0f}" '
        f'viewBox="0 0 {canvas_w:.0f} {canvas_h:.0f}" font-family="ui-monospace, SFMono-Regular, '
        f'Menlo, Consolas, monospace">',
        '<defs><linearGradient id="wbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOTTOM}"/>'
        '</linearGradient></defs>',
        f'<rect width="{canvas_w:.0f}" height="{canvas_h:.0f}" rx="12" fill="url(#wbg)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1:.0f}" height="{canvas_h-1:.0f}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w:.0f}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{PAD + i*15}" cy="{TITLEBAR_H/2}" r="4.5" fill="{dot}"/>')
    p.append(f'<text x="{canvas_w/2:.0f}" y="{TITLEBAR_H/2 + 4:.0f}" fill="{TITLE_TEXT}" '
             f'font-size="11.5" text-anchor="middle">nikhil@github: ~$ ./wordmark.sh --3d</text>')

    def frame_g(rows_txt, extra=""):
        out_rows = []
        for ry, line in enumerate(rows_txt):
            s = line.rstrip()
            if not s.strip():
                continue
            lead = len(s) - len(s.lstrip(" "))
            body = s[lead:]
            x = PAD + lead * CELL_W
            y = art_top + ry * CELL_H + CELL_H * 0.78
            out_rows.append(
                f'<text xml:space="preserve" x="{x:.1f}" y="{y:.1f}" font-size="{fs:.1f}" '
                f'textLength="{len(body)*CELL_W:.1f}" lengthAdjust="spacing">{html.escape(body)}</text>'
            )
        return f'<g fill="{INK}"{extra}>' + "".join(out_rows) + "</g>"

    p.append(f'<clipPath id="wipe"><rect x="{PAD}" y="{art_top:.1f}" height="{art_h:.1f}" width="0">'
             f'<animate attributeName="width" from="0" to="{art_w:.0f}" begin="0s" '
             f'dur="{reveal:.2f}s" fill="freeze"/></rect></clipPath>')
    p.append(f'<g clip-path="url(#wipe)">{frame_g(frames[0])}'
             f'<set attributeName="opacity" to="0" begin="{reveal:.2f}s"/></g>')
    p.append(f'<rect x="{PAD}" y="{art_top+2:.1f}" width="{CELL_W*1.6:.1f}" height="{art_h-4:.1f}" '
             f'fill="{INK}" opacity="0.16">'
             f'<animate attributeName="x" from="{PAD}" to="{PAD+art_w:.0f}" begin="0s" '
             f'dur="{reveal:.2f}s" fill="freeze"/>'
             f'<set attributeName="opacity" to="0" begin="{reveal:.2f}s"/></rect>')

    for i, rows_txt in enumerate(frames):
        if i == 0:
            vals, kt = "1;0", f"0;{1/n:.5f}"
        else:
            vals, kt = "0;1;0", f"0;{i/n:.5f};{(i+1)/n:.5f}"
        anim = (f'<animate attributeName="opacity" calcMode="discrete" values="{vals}" '
                f'keyTimes="{kt}" dur="{dur:.2f}s" begin="{reveal:.2f}s" '
                f'repeatCount="indefinite"/>')
        p.append(frame_g(rows_txt, ' opacity="0"').replace("</g>", anim + "</g>"))

    p.append("</svg>")
    svg = "".join(p)
    with open(out, "w") as fh:
        fh.write(svg)
    print(f"wrote {out}  {len(svg)/1024:.1f} KB  {n} frames  {canvas_w:.0f}x{canvas_h:.0f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "..", "wordmark.svg"))
    ap.add_argument("--frames", type=int, default=20)
    ap.add_argument("--dur", type=float, default=5.0)
    ap.add_argument("--reveal", type=float, default=1.6)
    ap.add_argument("--preview", action="store_true", help="print frame 0 to stdout instead of writing")
    a = ap.parse_args()

    P, N = build_shell()
    rest = math.radians(-13)
    amp = math.radians(11)
    yaws = [rest + amp * math.sin(2 * math.pi * i / a.frames) for i in range(a.frames)]

    proj = [project(P, N, y) for y in yaws]
    scale, cx, cy, rows = fit(proj)
    frames = [rasterize(q, scale, cx, cy, rows) for q in proj]

    if a.preview:
        for row in frames[0]:
            print(row.rstrip())
        return

    emit(frames, rows, a.out, a.dur, a.reveal)


if __name__ == "__main__":
    main()
