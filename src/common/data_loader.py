from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Optional

from src.pastry.local_index import MovieRecord


def load_movies(csv_dir: Optional[str] = None, max_records: Optional[int] = None) -> List[MovieRecord]:
    """Load movies from `movies_dataset_cleaned/data_movies_clean.csv`.

    If the CSV is missing, returns an empty list (the experiments fall back to
    dummy movie generation).
    """
    if csv_dir is None:
        csv_dir = Path.cwd() / "movies_dataset_cleaned"
    csv_path = Path(csv_dir) / "data_movies_clean.csv"

    movies: List[MovieRecord] = []

    if not csv_path.exists():
        return movies

    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader):
            if max_records is not None and i >= max_records:
                break
            # Best-effort parsing with graceful fallbacks
            movie_id = row.get("movie_id") or row.get("id") or str(i)
            title = (row.get("title") or "").strip()
            if not title:
                continue
            try:
                popularity = float(row["popularity"]) if row.get("popularity") else None
            except Exception:
                popularity = None
            try:
                vote_average = float(row["vote_average"]) if row.get("vote_average") else None
            except Exception:
                vote_average = None
            try:
                runtime = int(float(row["runtime"])) if row.get("runtime") else None
            except Exception:
                runtime = None

            movies.append(
                MovieRecord(
                    movie_id=str(movie_id),
                    title=title,
                    popularity=popularity,
                    vote_average=vote_average,
                    runtime=runtime,
                )
            )

    return movies


if __name__ == "__main__":
    # Quick smoke test
    m = load_movies(max_records=5)
    print(f"Loaded {len(m)} records (sample):")
    for rec in m[:5]:
        print(rec)
