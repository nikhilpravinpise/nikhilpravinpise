#!/usr/bin/env python3
"""
Download the streak SVG from a public service, recolor it to match README theme,
and write it to `output/github-streak.svg` only if content changed.

Run by GitHub Actions daily; keeps a repo-hosted copy that displays reliably.
"""
import os
import re
import sys
from pathlib import Path
from urllib.request import urlopen, Request

USERNAME = os.environ.get("GITHUB_REPOSITORY_OWNER", "nikhilpravinpise")
URLS = [
    f"https://github-readme-streak-stats.herokuapp.com?user={USERNAME}",
    f"https://streak-stats.demolab.com?user={USERNAME}",
]
OUT_PATH = Path("output") / "github-streak.svg"


def fetch_svg() -> str:
    """Try fetching SVG from multiple mirrors until one works."""
    # Use a generic user-agent to avoid being blocked by some endpoints
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    errors = []
    for url in URLS:
        print(f"Trying fetching from: {url}")
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=15) as r:
                data = r.read()
            return data.decode("utf-8")
        except Exception as e:
            print(f"Failed {url}: {e}")
            errors.append(f"{url}: {e}")
            
    raise Exception(f"All URLs failed: {errors}")


def recolor(svg_text: str) -> str:
    # Map of original -> replacement (approximate); apply globally
    replaces = {
        "#FFFEFE": "#0d1117",  # background -> dark
        "#E4E2E2": "#2F363D",  # light border -> muted
        "#151515": "#e6eef8",  # headings -> light
        "#464646": "#9aa6b2",  # secondary text -> muted light
        "#FB8C00": "#FFB86B",  # accent -> warmer but lighter
        "fill='#FFFEFE'": "fill='#0d1117'",
        "stroke='#E4E2E2'": "stroke='#2F363D'",
    }

    out = svg_text
    for a, b in replaces.items():
        out = out.replace(a, b)

    # Fallback: change any remaining obvious dark-on-light to light-on-dark heuristically
    out = re.sub(r"fill=['\"]#(0|f){3,6}['\"]", "fill='#e6eef8'", out, flags=re.IGNORECASE)
    return out


def write_if_changed(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old = path.read_text(encoding="utf-8")
        if old == content:
            print("No change in SVG.")
            return False
    path.write_text(content, encoding="utf-8")
    print(f"Wrote {path}")
    return True


def main() -> int:
    try:
        svg = fetch_svg()
    except Exception as e:
        print(f"Failed to fetch SVG: {e}")
        return 2

    svg = recolor(svg)

    changed = write_if_changed(OUT_PATH, svg)
    return 0 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
