from __future__ import annotations

from pathlib import Path
import csv
from collections import defaultdict
from typing import Dict, List

import matplotlib.pyplot as plt


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_metrics(csv_path: Path) -> List[dict]:
    rows: List[dict] = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            r["n_nodes"] = int(r["n_nodes"])
            r["n_keys"] = int(r["n_keys"])
            r["trial_id"] = int(r["trial_id"])
            r["hops"] = int(r["hops"])
            r["success"] = int(r["success"])
            r["time_ms"] = float(r["time_ms"])
            rows.append(r)
    return rows


def mean(xs: List[float]) -> float:
    return sum(xs) / max(1, len(xs))


def main() -> None:
    csv_path = project_root() / "results" / "pastry_metrics.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    rows = load_metrics(csv_path)

    grouped: Dict[int, List[int]] = defaultdict(list)
    for r in rows:
        if r["operation"] == "lookup" and r["protocol"] == "pastry":
            grouped[r["n_nodes"]].append(r["hops"])

    xs = sorted(grouped.keys())
    ys = [mean([float(h) for h in grouped[n]]) for n in xs]

    plt.figure()
    plt.plot(xs, ys, marker="o")
    plt.xlabel("Number of nodes (N)")
    plt.ylabel("Average hops per lookup")
    plt.title("Pastry: Lookup hops vs N")
    plt.grid(True, linestyle="--", linewidth=0.5)
    plt.tight_layout()

    out = project_root() / "results" / "pastry_lookup_hops.png"
    plt.savefig(out, dpi=200)
    print(f"Saved plot to: {out}")


if __name__ == "__main__":
    main()
