# -*- coding: utf-8 -*-
"""Generate a small synthetic ``books.csv`` so the pipeline runs after a clone.

The real Goodreads dataset is not redistributed in this repository. This script
produces a structurally identical sample — same columns, same dtypes, same quirks
(missing values, duplicates, out-of-range ratings) — so that a reviewer can run::

    python scripts/generate_sample_data.py
    python main.py

and obtain a populated analytical database in under a minute.

The generated data is random and carries no analytical meaning. It exists to
demonstrate that the pipeline, its validation rules and its cleaning steps work.

Usage:
    python scripts/generate_sample_data.py [--rows 300] [--seed 42]
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

REQUIRED_COLUMNS = [
    "bookID",
    "title",
    "authors",
    "average_rating",
    "isbn13",
    "language_code",
    "num_pages",
    "ratings_count",
    "text_reviews_count",
    "publication_date",
    "publisher_name",
    "genre_name",
]

TITLE_HEAD = ["The", "A", "Last", "Silent", "Broken", "Hidden", "Winter", "Iron", "Golden", "Quiet"]
TITLE_TAIL = ["Garden", "Compass", "Harbour", "Machine", "Archive", "Signal", "Orchard", "Circuit", "Lantern", "River"]
SURNAMES = ["Adeyemi", "Novak", "Lindqvist", "Moreau", "Okafor", "Tanaka", "Silva", "Ferrand", "Brennan", "Kaur"]
GIVEN = ["Ana", "Piotr", "Maya", "Luc", "Nadia", "Kenji", "Rui", "Claire", "Sean", "Ishani"]
PUBLISHERS = ["Northwind Press", "Marlowe & Sons", "Blue Harbor", "Verso Nord", "Kestrel Books", "Atlas Petit"]
LANGUAGES = ["eng", "eng", "eng", "fre", "spa", "ger", "en-US"]
# Must match the whitelist in config/config.yaml, otherwise every row falls back to "Other".
GENRES = [
    "History & Politics",
    "Health & Medicine",
    "Mystery & Thriller",
    "Arts & Design",
    "Non-Fiction",
    "Science Fiction & Fantasy",
    "Countries & Geography",
]


def _title(rng: random.Random) -> str:
    return f"{rng.choice(TITLE_HEAD)} {rng.choice(TITLE_TAIL)}"


def _authors(rng: random.Random) -> str:
    count = rng.choices([1, 2, 3], weights=[80, 15, 5])[0]
    names = [f"{rng.choice(GIVEN)} {rng.choice(SURNAMES)}" for _ in range(count)]
    return "/".join(names)


def _publication_date(rng: random.Random) -> str:
    start = date(1990, 1, 1)
    return (start + timedelta(days=rng.randint(0, 12_000))).strftime("%Y-%m-%d")


def build_rows(rows: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    records: list[dict] = []

    for book_id in range(1, rows + 1):
        ratings_count = rng.randint(0, 90_000)
        records.append(
            {
                "bookID": book_id,
                "title": _title(rng),
                "authors": _authors(rng),
                "average_rating": round(rng.uniform(2.4, 4.9), 2),
                "isbn13": f"978{rng.randint(1_000_000_000, 9_999_999_999)}",
                "language_code": rng.choice(LANGUAGES),
                "num_pages": rng.randint(48, 1200),
                "ratings_count": ratings_count,
                "text_reviews_count": rng.randint(0, max(1, ratings_count // 20)),
                "publication_date": _publication_date(rng),
                "publisher_name": rng.choice(PUBLISHERS),
                "genre_name": rng.choice(GENRES),
            }
        )

    # Deliberate imperfections, so the cleaning and validation stages have work to do
    # and a reviewer can see them reported in the logs.
    if rows >= 20:
        records.append(dict(records[0]))                      # exact duplicate row
        records[3]["num_pages"] = ""                          # missing value
        records[5]["average_rating"] = 7.4                    # rating outside the 0-5 range
        records[7]["publication_date"] = "1998-02-31"         # impossible calendar date
        records[9]["language_code"] = ""                      # missing dimension key
        records[11]["ratings_count"] = 0                      # forces the engagement guard

    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=300, help="number of clean rows (default: 300)")
    parser.add_argument("--seed", type=int, default=42, help="random seed (default: 42)")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/books.csv"),
        help="destination path (default: data/raw/books.csv)",
    )
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    records = build_rows(args.rows, args.seed)

    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(records)

    print(f"{len(records)} synthetic rows written to {args.output}")
    print("Run the pipeline with: python main.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
