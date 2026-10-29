#!/usr/bin/env python3
"""Embed both animated cards in one SVG so GitHub scales them together.

Run after render_photo_ascii.py and make_wordmark_svg.py. All SVG content
is embedded; external image references cannot load in GitHub's img sandbox.
"""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG_NS = "http://www.w3.org/2000/svg"
GAP = 212  # 96 display pixels when the cards are 144 pixels tall.


def render(photo, wordmark, out):
    cards = [ET.parse(path).getroot() for path in (photo, wordmark)]
    sizes = [tuple(map(float, card.attrib["viewBox"].split())) for card in cards]
    height = sizes[0][3]
    if height != sizes[1][3]:
        raise ValueError("Regenerate both cards with matching canvas heights first")
    width = sizes[0][2] + GAP + sizes[1][2]

    ET.register_namespace("", SVG_NS)
    hero = ET.Element(f"{{{SVG_NS}}}svg", {
        "width": f"{width:g}", "height": f"{height:g}",
        "viewBox": f"0 0 {width:g} {height:g}",
        "role": "img", "aria-labelledby": "hero-title",
    })
    ET.SubElement(hero, f"{{{SVG_NS}}}title", {"id": "hero-title"}).text = (
        "Nikhil's ASCII avatar portrait and animated 3D wordmark"
    )
    for card, x in zip(cards, (0, sizes[0][2] + GAP)):
        card.set("x", f"{x:g}")
        card.set("y", "0")
        hero.append(card)
    ET.ElementTree(hero).write(out, encoding="utf-8", xml_declaration=False)
    print(f"wrote {out}  {width:g}x{height:g}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--photo", type=Path, default=ROOT / "photo-ascii.svg")
    parser.add_argument("--wordmark", type=Path, default=ROOT / "wordmark.svg")
    parser.add_argument("--out", type=Path, default=ROOT / "profile-hero.svg")
    args = parser.parse_args()
    render(args.photo, args.wordmark, args.out)


if __name__ == "__main__":
    main()
