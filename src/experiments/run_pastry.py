from __future__ import annotations
from pathlib import Path
import os

import random
from typing import List, Dict, Any, Tuple

from src.common.hash_utils import normalize_title, key_for_title
from src.common.metrics import MetricsLogger
from src.pastry.network import PastryNetwork
from src.pastry.local_index import MovieRecord

print("RUN_PASTRY MODULE LOADED")

def key_id_hex_from_title(title: str) -> str:
    # 128-bit -> 32 hex chars
    return f"{key_for_title(title, bits=128):032x}"


def make_dummy_movies(n: int) -> List[MovieRecord]:
    """
    Dummy records until you integrate the real CSV.
    """
    movies: List[MovieRecord] = []
    for i in range(n):
        title = f"Movie {i}"
        movies.append(
            MovieRecord(
                movie_id=str(i),
                title=title,
                popularity=float(random.randint(0, 100)),
                vote_average=round(random.uniform(0, 10), 1),
                runtime=random.randint(60, 200),
            )
        )
    return movies


def bulk_insert_movies(net: PastryNetwork, movies: List[MovieRecord]) -> None:
    for rec in movies:
        key_str = normalize_title(rec.title)
        key_id = key_id_hex_from_title(rec.title)
        # store the record in the DHT store
        resp_id, _ = net.insert(key_id, key_str, rec)
        # ALSO maintain local index on responsible node
        net.nodes[resp_id].local_index.upsert(rec)


def run_k_title_query(
    net: PastryNetwork,
    titles: List[str],
    popularity_filter: Tuple[float, float] | None = None,
) -> Tuple[int, int]:
    """
    For each title:
      - DHT lookup
      - local filter on responsible node by popularity range (optional)
    Returns: (total_hops, successes)
    """
    total_hops = 0
    successes = 0

    for t in titles:
        key_str = normalize_title(t)
        key_id = key_id_hex_from_title(t)

        # DHT lookup + read values
        values, hops = net.get_values(key_id, key_str)
        total_hops += hops

        if not values:
            continue

        # local filtering using index (optional)
        # `lookup` returns (responsible_node_id, hops)
        resp_id, _ = net.lookup(key_id)
        node = net.nodes[resp_id]
        if popularity_filter is not None:
            lo, hi = popularity_filter
            _filtered = node.local_index.range_query("popularity", lo, hi)
            # we don't need to return them yet; just to exercise index
        successes += 1

    return total_hops, successes


def main() -> None:
    # Experiment knobs (can be overridden by environment variables for smoke tests)
    # Example: N_NODES='5' N_KEYS='50' K_TITLES='10' TRIALS='1'
    def _parse_list_env(name: str, default: str) -> list[int]:
        raw = os.getenv(name, default)
        return [int(x) for x in str(raw).split(",") if str(x).strip()]

    N_NODES = _parse_list_env("N_NODES", "50,100,200")
    N_KEYS = _parse_list_env("N_KEYS", "2000")
    K_TITLES = int(os.getenv("K_TITLES", "200"))
    TRIALS = int(os.getenv("TRIALS", "3"))
    SEED = int(os.getenv("SEED", "7"))

    project_root = Path(__file__).resolve().parents[2]  # DHTS-2025
    results_dir = project_root / "results"
    results_dir.mkdir(exist_ok=True)

    csv_path = results_dir / "pastry_metrics.csv"
    logger = MetricsLogger(str(csv_path))
   
    print(f"Writing results to: {csv_path}")

    for n_nodes in N_NODES:
        for n_keys in N_KEYS:
            for trial in range(TRIALS):
                random.seed(SEED + trial)

                # BUILD
                net = PastryNetwork(seed=SEED + trial)
                finish = logger.timed(
                    protocol="pastry",
                    operation="build",
                    n_nodes=n_nodes,
                    n_keys=n_keys,
                    trial_id=trial,
                )
                net.build(n_nodes)
                finish(hops=0, success=1)

                # INSERT BULK
                movies = make_dummy_movies(n_keys)
                finish = logger.timed(
                    protocol="pastry",
                    operation="insert",
                    n_nodes=n_nodes,
                    n_keys=n_keys,
                    trial_id=trial,
                )
                try:
                    bulk_insert_movies(net, movies)
                    finish(hops=0, success=1, extra=f"bulk={n_keys}")
                except Exception as e:
                    finish(hops=0, success=0, extra=str(e))

                # LOOKUP K TITLES
                sample_titles = [m.title for m in random.sample(movies, k=min(K_TITLES, len(movies)))]
                finish = logger.timed(
                    protocol="pastry",
                    operation="lookup",
                    n_nodes=n_nodes,
                    n_keys=n_keys,
                    trial_id=trial,
                )
                total_hops, ok = run_k_title_query(net, sample_titles, popularity_filter=(10.0, 80.0))
                # average hops per lookup (store as int rounded)
                avg_hops = int(round(total_hops / max(1, len(sample_titles))))
                finish(hops=avg_hops, success=1, extra=f"k={len(sample_titles)} ok={ok}")

    print("Done. Results in results/pastry_metrics.csv")


if __name__ == "__main__":
    main()
