# Cleans up games.csv and player_history.csv so they line up with events.csv
#  - months become YYYY-MM (same as the month column in events.csv)
#  - dates become YYYY-MM-DD
#  - drops the "Last 30 Days" rows since they aren't a real month
#  - player history sorted oldest -> newest for each game
# writes games_clean.csv and player_history_clean.csv, original files aren't changed
# run after pull_events.py: python3 normalize.py

import csv
from datetime import datetime


def read(name):
    with open(name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(name, rows):
    with open(name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("wrote", len(rows), "rows to", name)


def to_num(s, decimals):
    if s == "":
        return ""
    if decimals == 0:
        return int(float(s))
    return round(float(s), decimals)


# games
games = []
for g in read("games.csv"):
    g["release_date"] = datetime.strptime(g["release_date"], "%b %d, %Y").strftime("%Y-%m-%d")
    games.append(g)
write("games_clean.csv", games)

# player history
history = []
skipped = 0
for r in read("player_history.csv"):
    try:
        month = datetime.strptime(r["month"], "%B %Y").strftime("%Y-%m")
    except ValueError:
        skipped += 1  # "Last 30 Days"
        continue
    history.append({
        "app_id": r["app_id"],
        "game": r["game"],
        "month": month,
        "avg_players": to_num(r["avg_players"], 2),
        "gain": to_num(r["gain"], 2),
        "percent_gain": to_num(r["percent_gain"], 2),
        "peak_players": to_num(r["peak_players"], 0),
        "source_url": r["source_url"],
        "retrieved_at_utc": r["retrieved_at_utc"],
    })
history.sort(key=lambda r: (r["game"], r["month"]))
print("skipped", skipped, "rows that weren't a month")
write("player_history_clean.csv", history)

# quick check that events actually match up with the player data
months = {(r["app_id"], r["month"]) for r in history}
events = read("events.csv")
matched = sum((e["app_id"], e["month"]) in months for e in events)
print(matched, "of", len(events), "events have player data for their month")
