"""Create per-game monthly average player charts from the cleaned CSV files."""

import argparse
import csv
import math
import re
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
MONTH_FORMAT = "%Y-%m"


def read_games(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {"app_id", "game"}
        if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
            raise ValueError(f"{path} must contain app_id and game columns")

        games = {
            row["app_id"].strip(): row["game"].strip()
            for row in reader
            if row["app_id"].strip() and row["game"].strip()
        }

    if not games:
        raise ValueError(f"No games with an app_id and game were found in {path}")
    return games


def read_monthly_history(
    path: Path, games: dict[str, str]
) -> dict[str, list[tuple[datetime, float]]]:
    history: dict[str, list[tuple[datetime, float]]] = {app_id: [] for app_id in games}
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {"app_id", "month", "avg_players"}
        if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
            raise ValueError(
                f"{path} must contain app_id, month, and avg_players columns"
            )

        for line_number, row in enumerate(reader, start=2):
            app_id = row["app_id"].strip()
            if app_id not in games:
                continue

            month_label = row["month"].strip()
            try:
                try:
                    month = datetime.strptime(month_label, MONTH_FORMAT)
                except ValueError:
                    if month_label.lower() == "last 30 days":
                        continue
                    month = datetime.strptime(month_label, "%B %Y")
                average_players = float(row["avg_players"])
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Invalid monthly history on line {line_number} of {path}: {error}"
                ) from error

            if not math.isfinite(average_players):
                raise ValueError(
                    f"Non-finite avg_players on line {line_number} of {path}"
                )
            history[app_id].append((month, average_players))

    for entries in history.values():
        entries.sort(key=lambda entry: entry[0])
    return history


def read_monthly_event_months(
    path: Path, games: dict[str, str]
) -> dict[str, dict[str, list[datetime]]]:
    event_months: dict[str, dict[str, list[datetime]]] = {
        app_id: {"update": [], "dlc": []} for app_id in games
    }
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {"app_id", "month", "event_name", "event_type"}
        if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
            raise ValueError(
                f"{path} must contain app_id, month, event_name, and event_type columns"
            )

        for line_number, row in enumerate(reader, start=2):
            app_id = row["app_id"].strip()
            if app_id not in games or not row["event_name"].strip():
                continue

            try:
                month = datetime.strptime(row["month"].strip(), MONTH_FORMAT)
            except ValueError as error:
                raise ValueError(
                    f"Invalid event month on line {line_number} of {path}: {error}"
                ) from error

            event_type_value = row["event_type"].strip()
            event_types = {
                event_type.strip().lower() for event_type in event_type_value.split(";")
            }
            if not event_type_value or not event_types.issubset({"update", "dlc"}):
                raise ValueError(
                    f"Invalid event type on line {line_number} of {path}"
                )
            for event_type in event_types:
                event_months[app_id][event_type].append(month)

    for app_events in event_months.values():
        for event_type, months in app_events.items():
            app_events[event_type] = sorted(set(months))
    return event_months


def read_events(
    path: Path, games: dict[str, str]
) -> dict[str, dict[str, list[tuple[datetime, str]]]]:
    events: dict[str, dict[str, list[tuple[datetime, str]]]] = {
        app_id: {"update": [], "dlc": []} for app_id in games
    }
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {"app_id", "event_type", "event_name", "date"}
        if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
            raise ValueError(
                f"{path} must contain app_id, event_type, event_name, and date columns"
            )

        for line_number, row in enumerate(reader, start=2):
            app_id = row["app_id"].strip()
            if app_id not in games:
                continue

            event_type = row["event_type"].strip().lower()
            if event_type not in {"update", "dlc"}:
                continue

            event_name = row["event_name"].strip()
            if not event_name:
                continue

            normalized_event_name = event_name.lower()
            if "patch" in normalized_event_name:
                continue
            elif "bugfix" in normalized_event_name:
                continue
            elif "dev" in normalized_event_name:
                continue
            elif "developer" in normalized_event_name:
                continue

            date_value = row["date"].strip()
            try:
                event_date = datetime.strptime(date_value, "%Y-%m-%d")
            except ValueError as error:
                raise ValueError(
                    f"Invalid event date on line {line_number} of {path}: {error}"
                ) from error

            events[app_id][event_type].append((event_date, event_name))

    for app_events in events.values():
        for event_type in app_events:
            app_events[event_type].sort(key=lambda event: event[0])

    return events


def write_monthly_csv(
    path: Path,
    games: dict[str, str],
    history: dict[str, list[tuple[datetime, float]]],
    events: dict[str, dict[str, list[tuple[datetime, str]]]],
) -> int:
    row_count = 0
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            ["app_id", "game", "month", "avg_players", "event_name", "event_type"]
        )
        for app_id, game in games.items():
            for month, average_players in history[app_id]:
                month_events = [
                    (event_type, name)
                    for event_type, event_list in events[app_id].items()
                    for event_date, name in event_list
                    if event_date.strftime("%Y-%m") == month.strftime("%Y-%m") and name
                ]
                if not month_events:
                    continue

                event_names = [name for _, name in month_events]
                event_types = [
                    event_type
                    for event_type in ("update", "dlc")
                    if any(kind == event_type for kind, _ in month_events)
                ]
                writer.writerow(
                    [
                        app_id,
                        game,
                        month.strftime("%Y-%m"),
                        average_players,
                        "; ".join(event_names),
                        "; ".join(event_types),
                    ]
                )
                row_count += 1
    return row_count


def write_game_charts(
    output_dir: Path,
    games: dict[str, str],
    history: dict[str, list[tuple[datetime, float]]],
    event_months: dict[str, dict[str, list[datetime]]],
) -> int:
    chart_count = 0
    for app_id, game in games.items():
        entries = history[app_id]
        if not entries:
            print(
                f"Warning: no monthly history found for {game} ({app_id})",
                file=sys.stderr,
            )
            continue

        months, average_players = zip(*entries)
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", game).strip("._")
        output_path = output_dir / f"{safe_name}.png"

        figure, axis = plt.subplots(figsize=(11, 5))
        axis.plot(months, average_players, marker="o", markersize=3, linewidth=1.5)

        for index, event_month in enumerate(event_months[app_id]["update"]):
            axis.axvline(
                event_month,
                linestyle=(0, (1, 5)),
                color="blue",
                linewidth=1,
                alpha=0.8,
                label="Update" if index == 0 else None,
            )

        for index, event_month in enumerate(event_months[app_id]["dlc"]):
            axis.axvline(
                event_month,
                linestyle=(0, (1, 7)),
                color="red",
                linewidth=1,
                alpha=0.8,
                label="DLC" if index == 0 else None,
            )

        if event_months[app_id]["update"] or event_months[app_id]["dlc"]:
            axis.legend()

        axis.margins(x=0)
        axis.set_title(f"Monthly Average Players - {game}")
        axis.set_xlabel("Month")
        axis.set_ylabel("Average concurrent players")
        axis.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        axis.grid(True, alpha=0.3)
        figure.autofmt_xdate()
        figure.tight_layout()
        figure.savefig(output_path, dpi=150)
        plt.close(figure)
        chart_count += 1

    return chart_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot monthly average players from player_history.csv with events from the generated monthly CSV."
    )
    parser.add_argument("--history", type=Path, default=ROOT / "player_history.csv")
    parser.add_argument("--events", type=Path, default=ROOT / "events.csv")
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "monthly_player_charts_with_stripped_events"
    )
    args = parser.parse_args()

    games = read_games(args.history)
    history = read_monthly_history(args.history, games)
    events = read_events(args.events, games)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    monthly_csv_path = args.output_dir / "monthly_player_counts.csv"
    row_count = write_monthly_csv(monthly_csv_path, games, history, events)
    event_months = read_monthly_event_months(monthly_csv_path, games)
    chart_count = write_game_charts(args.output_dir, games, history, event_months)
    print(
        f"Wrote {row_count} monthly rows and {chart_count} game charts "
        f"to {args.output_dir}"
    )


if __name__ == "__main__":
    main()