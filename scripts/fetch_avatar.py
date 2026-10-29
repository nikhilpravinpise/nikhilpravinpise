#!/usr/bin/env python3
"""
Download the live GitHub avatar for USERNAME and write it to
data/avatar.jpg. Source image for the ASCII-art portrait panel rendered by
render_photo_ascii.py.

Uses the *.png?size=N vanity URL, which redirects to
avatars.githubusercontent.com and always resolves to whatever avatar the
account currently has - so this stays in sync automatically if the avatar
ever changes. Run daily by .github/workflows/update-profile-art.yml.
"""
import os
import sys

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
USERNAME = os.environ.get("GITHUB_REPOSITORY_OWNER", "nikhilpravinpise")
URL = f"https://github.com/{USERNAME}.png?size=460"
OUT_PATH = os.path.join(HERE, "..", "data", "avatar.jpg")


def fetch_avatar():
    resp = requests.get(URL, headers={"User-Agent": "profile-readme-bot"}, timeout=30)
    resp.raise_for_status()
    ctype = resp.headers.get("Content-Type", "")
    if not ctype.startswith("image/"):
        print(f"unexpected content-type {ctype!r} from {URL} - avatar URL may have changed", file=sys.stderr)
        sys.exit(1)
    return resp.content


if __name__ == "__main__":
    content = fetch_avatar()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "wb") as f:
        f.write(content)
    print(f"wrote {OUT_PATH} ({len(content)} bytes)")
