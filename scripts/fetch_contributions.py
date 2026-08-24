#!/usr/bin/env python3
"""
Pull daily contribution counts from GitHub's public, unauthenticated
contribution-calendar fragment (the same HTML the profile page itself
renders) and write data/contributions.json with the raw days plus derived
stats: current streak, longest streak, best day.

No token needed - just the public calendar markup GitHub already serves.
Run daily by .github/workflows/update-profile-art.yml.
"""
import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
USERNAME = os.environ.get("GITHUB_REPOSITORY_OWNER", "nikhilpravinpise")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(HERE, "..", "data", "contributions.json")


def fetch_days():
    resp = requests.get(URL, headers={"User-Agent": "profile-readme-bot"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        print("no calendar cells found - GitHub's calendar markup may have changed", file=sys.stderr)
        sys.exit(1)

    days = []
    for td in cells:
        date = td.get("data-date")
        if not date:
            continue
        td_id = td.get("id")
        tooltip = soup.find("tool-tip", attrs={"for": td_id}) if td_id else None
        text = tooltip.get_text(strip=True) if tooltip else ""
        if re.search(r"no contributions", text, re.I):
            count = 0
        else:
            m = re.match(r"([\d,]+)", text)
            count = int(m.group(1).replace(",", "")) if m else 0
        days.append({"date": date, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


def current_streak(days):
    idx = len(days) - 1
    if days[idx]["count"] == 0:
        idx -= 1  # today may not be over yet - don't let it snap the streak
    length = 0
    end = idx
    while idx >= 0 and days[idx]["count"] > 0:
        length += 1
        idx -= 1
    if length == 0:
        return {"length": 0, "start": None, "end": None}
    return {"length": length, "start": days[end - length + 1]["date"], "end": days[end]["date"]}


def longest_streak(days):
    best_len = run = 0
    best_start = best_end = None
    run_start = None
    for i, d in enumerate(days):
        if d["count"] > 0:
            if run == 0:
                run_start = i
            run += 1
            if run > best_len:
                best_len = run
                best_start = days[run_start]["date"]
                best_end = days[i]["date"]
        else:
            run = 0
    return {"length": best_len, "start": best_start, "end": best_end}


def build_data(days):
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"] > 0)
    best = max(days, key=lambda d: d["count"])
    return {
        "username": USERNAME,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active,
        "current_streak": current_streak(days),
        "longest_streak": longest_streak(days),
        "best_day": {"date": best["date"], "count": best["count"]},
        "days": days,
    }


if __name__ == "__main__":
    data = build_data(fetch_days())
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(
        f"wrote {OUT_PATH}: {data['total_contributions']} contributions, "
        f"current streak {data['current_streak']['length']}, "
        f"longest streak {data['longest_streak']['length']}"
    )
