#!/usr/bin/env python3
"""Télécharge les données publiques Chess.com (PubAPI), en lecture seule.

Aucun identifiant, aucun cookie, aucune requête d'écriture.
Doc : https://www.chess.com/news/view/published-data-api
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
BRUSSELS = ZoneInfo("Europe/Brussels")
UA = "Zoliandru-chess-study/1.0 (personal training workspace; read-only PubAPI)"
API = "https://api.chess.com/pub/player"


def get_json(url: str, pause: float = 0.25) -> dict:
    last_error: Exception | None = None
    for attempt in range(4):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                payload = json.load(response)
            time.sleep(pause)
            return payload
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429 or exc.code >= 500:
                time.sleep(3 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError as exc:
            last_error = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"échec de lecture {url}: {last_error}")


def annotate_pgn(pgn: str, time_class: str, rated: bool, rules: str) -> str:
    """Ajoute trois en-têtes factuels absents du PGN renvoyé par l'API."""
    extra = [
        f'[TimeClass "{time_class}"]',
        f'[Rated "{"true" if rated else "false"}"]',
        f'[Rules "{rules}"]',
    ]
    lines = pgn.strip().splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith("[Event "):
            insert_at = i + 1
            break
    lines[insert_at:insert_at] = extra
    return "\n".join(lines).strip() + "\n"


def month_counts(games: list[dict]) -> dict:
    by_class: Counter[str] = Counter()
    by_rules: Counter[str] = Counter()
    by_tc: Counter[str] = Counter()
    by_class_rules: Counter[str] = Counter()
    for game in games:
        time_class = str(game.get("time_class") or "?")
        rules = str(game.get("rules") or "?")
        tc = str(game.get("time_control") or "?")
        by_class[time_class] += 1
        by_rules[rules] += 1
        by_tc[tc] += 1
        by_class_rules[f"{time_class}|{rules}"] += 1
    return {
        "games": len(games),
        "by_time_class": dict(by_class),
        "by_rules": dict(by_rules),
        "by_time_control": dict(by_tc),
        "by_class_rules": dict(by_class_rules),
    }


def write_month_pgn(month: str, games: list[dict], dest: Path) -> int:
    """Écrit les parties d'échecs standard blitz et rapide. Renvoie le nombre écrit."""
    kept = []
    for game in games:
        rules = game.get("rules")
        time_class = game.get("time_class")
        if rules != "chess":
            continue
        if time_class not in {"blitz", "rapid"}:
            continue
        pgn = game.get("pgn")
        if not pgn:
            continue
        kept.append((int(game.get("end_time") or 0), game))
    kept.sort(key=lambda item: item[0])
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as handle:
        for _, game in kept:
            handle.write(
                annotate_pgn(
                    game["pgn"],
                    str(game.get("time_class") or ""),
                    bool(game.get("rated")),
                    str(game.get("rules") or ""),
                )
            )
            handle.write("\n")
    return len(kept)


def rebuild_index(pgn_dir: Path, index_path: Path) -> int:
    import chess.pgn

    index_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(pgn_dir.glob("*.pgn")):
        with path.open(encoding="utf-8") as handle:
            while True:
                game = chess.pgn.read_game(handle)
                if game is None:
                    break
                headers = game.headers
                rows.append(
                    {
                        "link": headers.get("Link", ""),
                        "pgn_file": path.name,
                        "date_utc": headers.get("UTCDate", headers.get("Date", "")),
                        "utc_time": headers.get("UTCTime", ""),
                        "end_date_utc": headers.get("EndDate", ""),
                        "end_time_utc": headers.get("EndTime", ""),
                        "white": headers.get("White", ""),
                        "black": headers.get("Black", ""),
                        "result": headers.get("Result", ""),
                        "white_elo": headers.get("WhiteElo", ""),
                        "black_elo": headers.get("BlackElo", ""),
                        "time_control": headers.get("TimeControl", ""),
                        "time_class": headers.get("TimeClass", ""),
                        "rated": headers.get("Rated", ""),
                        "rules": headers.get("Rules", ""),
                        "eco": headers.get("ECO", ""),
                        "opening_url": headers.get("ECOUrl", ""),
                        "termination": headers.get("Termination", ""),
                    }
                )
    rows.sort(key=lambda row: (row["end_date_utc"], row["end_time_utc"], row["link"]))
    with index_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lecture seule de la PubAPI Chess.com")
    parser.add_argument("--username", default="zoliandru")
    parser.add_argument(
        "--pgn-months",
        nargs="+",
        default=["2026/08", "2026/09", "2026/10", "2026/11"],
        help="Mois YYYY/MM dont les PGN blitz/rapide standard sont enregistrés",
    )
    parser.add_argument(
        "--skip-census",
        action="store_true",
        help="Ne pas reparcourir toutes les archives (profil et mois PGN seulement)",
    )
    args = parser.parse_args()
    username = args.username.lower()
    source = ROOT / "games" / "source"
    source.mkdir(parents=True, exist_ok=True)
    now = datetime.now(BRUSSELS).isoformat(timespec="seconds")

    profile = get_json(f"{API}/{username}")
    stats = get_json(f"{API}/{username}/stats")
    archives = get_json(f"{API}/{username}/games/archives")
    (source / "profile.json").write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (source / "stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    archive_urls = list(archives.get("archives") or [])
    wanted = {month.strip() for month in args.pgn_months}
    census_months = []
    pgn_written = {}

    urls = archive_urls
    if args.skip_census:
        urls = [url for url in archive_urls if url.rstrip("/").split("/")[-2] + "/" + url.rstrip("/").split("/")[-1] in wanted]
        # rebuild wanted filter properly below

    def month_of(url: str) -> str:
        parts = url.rstrip("/").split("/")
        return f"{parts[-2]}/{parts[-1]}"

    if args.skip_census:
        urls = [url for url in archive_urls if month_of(url) in wanted]

    for url in urls:
        month = month_of(url)
        print(f"archive {month}", flush=True)
        try:
            payload = get_json(url, pause=0.2)
        except Exception as exc:  # noqa: BLE001 — on continue le recensement
            census_months.append({"month": month, "error": str(exc)})
            print(f"  erreur {exc}", file=sys.stderr)
            continue
        games = list(payload.get("games") or [])
        counts = month_counts(games)
        counts["month"] = month
        census_months.append(counts)
        print(f"  {counts['games']} parties {counts['by_time_class']}", flush=True)
        if month in wanted:
            dest = ROOT / "games" / "pgn" / f"{month.replace('/', '-')}.pgn"
            n_kept = write_month_pgn(month, games, dest)
            pgn_written[month] = {"file": str(dest.relative_to(ROOT)), "games": n_kept}
            print(f"  pgn {n_kept}", flush=True)

    census = {
        "username": username,
        "fetched_at": now,
        "timezone": "Europe/Brussels",
        "api": f"{API}/{username}",
        "note": "Instantané public en lecture seule. Aucun secret.",
        "archives": [month_of(url) for url in archive_urls],
        "months": census_months,
        "pgn_written": pgn_written,
        "census_complete": not args.skip_census,
    }
    census_path = source / "archive-census.json"
    if args.skip_census and census_path.exists():
        previous = json.loads(census_path.read_text(encoding="utf-8"))
        by_month = {row.get("month"): row for row in previous.get("months") or [] if row.get("month")}
        for row in census_months:
            if row.get("month"):
                by_month[row["month"]] = row
        census["months"] = [by_month[key] for key in sorted(by_month)]
        census["archives"] = previous.get("archives") or census["archives"]
        census["census_complete"] = bool(previous.get("census_complete"))
    census_path.write_text(json.dumps(census, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    index_n = rebuild_index(ROOT / "games" / "pgn", ROOT / "games" / "index.jsonl")
    manifest = {
        "username": username,
        "fetched_at": now,
        "timezone": "Europe/Brussels",
        "pgn_months": pgn_written,
        "index_games": index_n,
        "source": {
            "profile": "games/source/profile.json",
            "stats": "games/source/stats.json",
            "census": "games/source/archive-census.json",
        },
    }
    (ROOT / "games" / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"index {index_n} parties")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
