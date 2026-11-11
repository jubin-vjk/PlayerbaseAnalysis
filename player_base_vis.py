"""Create per-game monthly average player charts from the collected CSV files."""

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
MONTH_FORMAT = "%B %Y"


def read_games(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {"app_id", "selected_name"}
        if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
            raise ValueError(f"{path} must contain app_id and selected_name columns")

        games = {
            row["app_id"].strip(): row["selected_name"].strip()
            for row in reader
            if row["app_id"].strip() and row["selected_name"].strip()
        }

    if not games:
        raise ValueError(f"No games with an app_id and selected_name were found in {path}")
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
            if month_label == "Last 30 Days":
                continue

            try:
                month = datetime.strptime(month_label, MONTH_FORMAT)
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


def read_dlc_dates(path: Path, games: dict[str, str]) -> dict[str, list[datetime]]:
    dlc_dates: dict[str, set[datetime]] = {app_id: set() for app_id in games}
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {"parent_app_id", "release_date"}
        if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
            raise ValueError(
                f"{path} must contain parent_app_id and release_date columns"
            )

        for line_number, row in enumerate(reader, start=2):
            app_id = row["parent_app_id"].strip()
            if app_id not in games:
                continue

            try:
                release_date = datetime.strptime(row["release_date"].strip(), "%b %d, %Y")
            except ValueError as error:
                raise ValueError(
                    f"Invalid release_date on line {line_number} of {path}: {error}"
                ) from error
            dlc_dates[app_id].add(release_date)

    return {
        app_id: sorted(releases)
        for app_id, releases in dlc_dates.items()
    }


def write_monthly_csv(
    path: Path,
    games: dict[str, str],
    history: dict[str, list[tuple[datetime, float]]],
) -> int:
    row_count = 0
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["app_id", "game", "month", "avg_players"])
        for app_id, game in games.items():
            for month, average_players in history[app_id]:
                writer.writerow(
                    [app_id, game, month.strftime("%Y-%m"), average_players]
                )
                row_count += 1
    return row_count


def write_game_charts(
    output_dir: Path,
    games: dict[str, str],
    history: dict[str, list[tuple[datetime, float]]],
    dlc_dates: dict[str, list[datetime]],
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
        for index, release_date in enumerate(dlc_dates[app_id]):
            axis.axvline(
                release_date,
                color="red",
                linestyle="--",
                linewidth=1,
                alpha=0.7,
                label="DLC release" if index == 0 else None,
            )
        if dlc_dates[app_id]:
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
        description="Plot monthly average players for each game in games.csv."
    )
    parser.add_argument("--games", type=Path, default=ROOT / "games.csv")
    parser.add_argument("--history", type=Path, default=ROOT / "player_history.csv")
    parser.add_argument("--dlcs", type=Path, default=ROOT / "dlcs.csv")
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "monthly_player_charts_with_DLC"
    )
    args = parser.parse_args()

    games = read_games(args.games)
    history = read_monthly_history(args.history, games)
    dlc_dates = read_dlc_dates(args.dlcs, games)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    row_count = write_monthly_csv(
        args.output_dir / "monthly_player_counts.csv", games, history
    )
    chart_count = write_game_charts(args.output_dir, games, history, dlc_dates)
    print(
        f"Wrote {row_count} monthly rows and {chart_count} game charts "
        f"to {args.output_dir}"
    )


if __name__ == "__main__":
    main()