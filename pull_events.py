# Pulls update + DLC info for the games in games.csv and writes events.csv
# DLCs come from dlcs.csv, updates come from the Steam news API
# run: python3 pull_events.py

import csv
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

NEWS_URL = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
MAX_PAGES = 20  # 100 posts per page

columns = ["app_id", "game", "event_type", "event_name", "date", "month",
           "is_free", "is_major", "major_reason", "source", "url", "retrieved_at_utc"]

# cosmetic/filler dlc, not counted as major
minor_dlc = re.compile(
    r"soundtrack|\bost\b|artbook|art book|wallpaper|costume|hairstyle|gesture|"
    r"sticker|pose|emote|skin|outfit|cosmetic|bonus content|texture pack|"
    r"deluxe kit|supporter|digital extras|voice|pendant|layered|bundle|redmod|"
    r"pack \d+\b|charm|portrait|title|makeup|face paint", re.I)

# news posts that aren't actually updates
not_update = re.compile(
    r"hotfix|hot fix|maintenance|known issues|server|downtime|sale|discount|"
    r"\bfree weekend\b|community|spotlight|giveaway|contest|merch|twitch|"
    r"stream|survey|dev ?blog|developer diary|roadmap|esports|tournament|"
    r"recap|patch notes? preview|teaser|trailer|pre-?load|\bpack\b|bundle|"
    r"\bevent\b|collection|\btest\b|\bpts\b|ptb|beta|anti-?cheat|matchmaking|"
    r"reliability|countdown|coming soon|launches on steam|available on steam|"
    r"league|\blan\b|playoff|finals?\b|invite|fantasy|ranked season|"
    r"coming to|inbound|revealed|\bwire\b|cinematic|ea play|\$\d", re.I)

# words that usually mean a big update
major_words = re.compile(
    r"\bseason\b|\bexpansion\b|\bchapter\b|major update|content update|"
    r"free update|big update|title update|\bepisode\b|\bwarbond\b|"
    r"anniversary update|\bupdate \d+(?:\.0)?\b(?![./\d])", re.I)

# version numbers like 1.5 or 7.2.0 (7.2.2 would be a small patch)
version = re.compile(r"\b(?:v|version |patch )?(\d+)\.(\d+)(?:\.(\d+))?\b", re.I)


def parse_date(s):
    s = s.strip()
    for fmt in ["%b %d, %Y", "%d %b, %Y", "%B %d, %Y", "%b %Y", "%B %Y"]:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def get_dlcs(now):
    rows = []
    with open("dlcs.csv", newline="", encoding="utf-8") as f:
        for d in csv.DictReader(f):
            dt = parse_date(d["release_date"])
            if dt is None:
                print("skipping (bad date):", d["dlc_name"], d["release_date"])
                continue
            free = d["is_free"] == "True"
            major = d["type"] == "dlc" and not free and not minor_dlc.search(d["dlc_name"])
            rows.append({
                "app_id": d["parent_app_id"],
                "game": d["parent_game"],
                "event_type": "dlc",
                "event_name": d["dlc_name"],
                "date": dt.strftime("%Y-%m-%d"),
                "month": dt.strftime("%Y-%m"),
                "is_free": free,
                "is_major": major,
                "major_reason": "paid dlc" if major else "",
                "source": "steam_store",
                "url": d["store_url"],
                "retrieved_at_utc": now,
            })
    return rows


def get_news(app_id):
    # api only gives 100 at a time so keep going back with enddate
    posts = []
    enddate = None
    for _ in range(MAX_PAGES):
        params = {"appid": app_id, "count": 100, "maxlength": 1,
                  "feeds": "steam_community_announcements"}
        if enddate:
            params["enddate"] = enddate
        url = NEWS_URL + "?" + urllib.parse.urlencode(params)

        page = None
        for tries in range(3):
            try:
                with urllib.request.urlopen(url, timeout=30) as r:
                    page = json.load(r)["appnews"]["newsitems"]
                break
            except Exception as e:
                print("  request failed, retrying:", e)
                time.sleep(3)
        if page is None:
            break

        if enddate:
            page = [p for p in page if p["date"] < enddate]
        if not page:
            break
        posts += page
        enddate = min(p["date"] for p in page)
        time.sleep(0.5)
    return posts


def check_update(title, tags):
    # returns (is_major, reason), or None if the post isn't an update
    if not_update.search(title):
        return None
    if major_words.search(title):
        return True, "keyword"
    m = version.search(title)
    if m and m.group(3) in (None, "0"):
        return True, "version " + m.group(0)
    if "patchnotes" in tags or re.search(r"update|patch", title, re.I):
        return False, ""
    return None


def get_updates(games, now):
    rows = []
    for g in games:
        posts = get_news(g["app_id"])
        seen = set()
        count = 0
        for p in posts:
            dt = datetime.fromtimestamp(p["date"], tz=timezone.utc)
            # some posts show up twice with different ids, so check title + day too
            key = (p["title"].strip().lower(), dt.date())
            if p["gid"] in seen or key in seen:
                continue
            seen.add(p["gid"])
            seen.add(key)
            res = check_update(p["title"], p.get("tags", []))
            if res is None:
                continue
            rows.append({
                "app_id": g["app_id"],
                "game": g["selected_name"],
                "event_type": "update",
                "event_name": p["title"].strip(),
                "date": dt.strftime("%Y-%m-%d"),
                "month": dt.strftime("%Y-%m"),
                "is_free": True,
                "is_major": res[0],
                "major_reason": res[1],
                "source": "steam_news",
                "url": p["url"],
                "retrieved_at_utc": now,
            })
            count += 1
        print(g["selected_name"], "-", len(posts), "posts,", count, "updates")
    return rows


now = datetime.now(timezone.utc).isoformat()
with open("games.csv", newline="", encoding="utf-8") as f:
    games = list(csv.DictReader(f))

events = get_dlcs(now) + get_updates(games, now)

# drop anything from before the game came out on steam
# (pre-launch announcements, and warhammer II dlc that steam lists under warhammer III)
release = {g["app_id"]: parse_date(g["release_date"]).strftime("%Y-%m-%d") for g in games}
before = len(events)
events = [e for e in events if e["date"] >= release[e["app_id"]]]
print("dropped", before - len(events), "events from before the steam release")

events.sort(key=lambda e: (e["game"], e["date"], e["event_type"]))

with open("events.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=columns)
    w.writeheader()
    w.writerows(events)

print("wrote", len(events), "events to events.csv,", sum(e["is_major"] for e in events), "major")
