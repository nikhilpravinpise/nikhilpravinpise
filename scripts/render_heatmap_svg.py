#!/usr/bin/env python3
"""
Render data/contributions.json (written by fetch_contributions.py) as a
GitHub-style contribution heatmap: a 53-week x 7-day grid of rounded boxes
inside a terminal-styled card, with a one-shot diagonal reveal (CSS
keyframes - GitHub's <img> sandbox runs CSS animation same as inline
<style>, plays on load then freezes) and a stats footer below the grid.

Run by .github/workflows/update-profile-art.yml after fetch_contributions.py.
"""
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

PALETTE = ["#161b22", "#0f3d38", "#0f6d5f", "#14a087", "#2dd4bf", "#7ff2e3"]

CELL = 11
GAP = 3
STEP = CELL + GAP
PAD = 20
LEFT_LABEL_W = 28
TOP_LABEL_H = 18
TITLEBAR_H = 28

BG_TOP = "#111722"
BG_BOTTOM = "#0d1117"
FRAME = "#30363d"
MUTED = "#7d8590"
TEXT = "#c9d1d9"
ACCENT = "#2dd4bf"
GOLD = "#f2cc60"

COL_T = 0.016
ROW_T = 0.04
CELL_DUR = 0.4


def level_for(count):
    if count == 0:
        return 0
    if count <= 3:
        return 1
    if count <= 8:
        return 2
    if count <= 15:
        return 3
    if count <= 25:
        return 4
    return 5


def build_grid(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    lead_pad = (first.weekday() + 1) % 7  # Sunday-first week, like GitHub's own grid
    grid = []
    col = [None] * lead_pad
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        weekday = (date.weekday() + 1) % 7
        while len(col) < weekday:
            col.append(None)
        col.append((d["date"], d["count"], level_for(d["count"])))
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        while len(col) < 7:
            col.append(None)
        grid.append(col)
    return grid


def render(data):
    days = data["days"]
    grid = build_grid(days)
    n_cols = len(grid)
    art_w = n_cols * STEP
    art_h = 7 * STEP

    month_labels = []
    seen = set()
    for ci, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue
            date = datetime.date.fromisoformat(cell[0])
            key = (date.year, date.month)
            if key not in seen and date.day <= 7:
                seen.add(key)
                month_labels.append((ci, date.strftime("%b")))
            break

    canvas_w = PAD + LEFT_LABEL_W + art_w + PAD
    stats_h = 66
    canvas_h = TITLEBAR_H + TOP_LABEL_H + art_h + stats_h + PAD

    css = f"""
@keyframes cell {{
  0%   {{ opacity: 0; transform: translateY(-5px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}
.c {{ opacity: 0; animation: cell {CELL_DUR:.2f}s cubic-bezier(.2,.8,.2,1) both; }}
""".strip()

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<style>{css}</style>',
        '<defs><linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG_BOTTOM}"/></linearGradient></defs>',
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="url(#hbg)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1}" height="{canvas_h-1}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{PAD + i*15}" cy="{TITLEBAR_H/2}" r="4.5" fill="{dot}"/>')
    p.append(f'<text x="{canvas_w/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="11.5" '
             f'text-anchor="middle">nikhil@github: ~/contributions --graph</text>')

    grid_top = TITLEBAR_H + TOP_LABEL_H
    grid_left = PAD + LEFT_LABEL_W

    for ci, label in month_labels:
        x = grid_left + ci * STEP
        p.append(f'<text x="{x}" y="{TITLEBAR_H + 13}" fill="{MUTED}" font-size="9.5">{label}</text>')

    for wi, wname in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = grid_top + wi * STEP + CELL * 0.78
        p.append(f'<text x="{PAD}" y="{y:.1f}" fill="{MUTED}" font-size="8.5">{wname}</text>')

    for ci, column in enumerate(grid):
        gx = grid_left + ci * STEP
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            gy = grid_top + ri * STEP
            delay = ci * COL_T + ri * ROW_T
            plural = "s" if count != 1 else ""
            p.append(
                f'<rect class="c" x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{PALETTE[lvl]}" style="animation-delay:{delay:.3f}s">'
                f'<title>{date_s}: {count} contribution{plural}</title></rect>'
            )

    leg_y = grid_top + art_h + 8
    leg_x = canvas_w - PAD - (len(PALETTE) * CELL + 66)
    p.append(f'<text x="{leg_x}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" '
             f'font-size="9.5" text-anchor="end">Less</text>')
    lx = leg_x + 8
    for _lvl, color in enumerate(PALETTE):
        p.append(f'<rect x="{lx}" y="{leg_y}" width="{CELL-1}" height="{CELL-1}" rx="2.2" fill="{color}"/>')
        lx += CELL
    p.append(f'<text x="{lx + 4}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="9.5">More</text>')

    sep_y = leg_y + CELL + 14
    p.append(f'<line x1="0" y1="{sep_y}" x2="{canvas_w}" y2="{sep_y}" stroke="{FRAME}" stroke-opacity="0.6"/>')

    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    total = data["total_contributions"]
    best = data["best_day"]
    rng = data["range"]

    ly = sep_y + 22
    p.append(f'<text x="{PAD}" y="{ly}" font-size="12.5" fill="{ACCENT}">'
             f'<tspan font-weight="700">{total:,}</tspan>'
             f'<tspan fill="{MUTED}"> contributions in the last year</tspan></text>')
    p.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="11" fill="{MUTED}" text-anchor="end">'
             f'{rng["start"]} &#8594; {rng["end"]}</text>')
    ly += 22
    p.append(f'<text x="{PAD}" y="{ly}" font-size="12.5" fill="{MUTED}">current streak '
             f'<tspan fill="{TEXT}" font-weight="700">{cs} days</tspan>'
             f'<tspan fill="{MUTED}">   &#183;   longest </tspan>'
             f'<tspan fill="{TEXT}" font-weight="700">{ls} days</tspan></text>')
    p.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="11" fill="{MUTED}" text-anchor="end">'
             f'best day <tspan fill="{GOLD}" font-weight="700">{best["count"]}</tspan> on {best["date"]}</text>')

    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    with open(IN_PATH) as f:
        data = json.load(f)
    svg = render(data)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")
