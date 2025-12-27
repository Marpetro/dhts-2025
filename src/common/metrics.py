from __future__ import annotations

import csv
import os
import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class MetricEvent:
    protocol: str           # "pastry" | "chord"
    operation: str          # "build"|"insert"|"lookup"|"update"|"delete"|"join"|"leave"
    n_nodes: int
    n_keys: int
    trial_id: int
    hops: int
    success: int            # 1/0
    time_ms: float
    key: Optional[str] = None
    extra: Optional[str] = None  # keep it simple; JSON string if you want


class MetricsLogger:
    """
    Append-only CSV logger. Use one file per run, or reuse same file across runs.
    """
    FIELDNAMES = [
        "protocol", "operation", "n_nodes", "n_keys", "trial_id",
        "hops", "success", "time_ms", "key", "extra"
    ]

    def __init__(self, csv_path: str) -> None:
        self.csv_path = csv_path
        os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
        self._ensure_header()

    def _ensure_header(self) -> None:
        if not os.path.exists(self.csv_path) or os.path.getsize(self.csv_path) == 0:
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
                writer.writeheader()

    def log(self, event: MetricEvent) -> None:
        row = asdict(event)
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            writer.writerow(row)

    def timed(self, **base_fields: Any):
        """
        Context manager-like helper:
            with logger.timed(protocol="pastry", operation="lookup", ... ) as finish:
                ... do work ...
                finish(hops=..., success=..., key=..., extra=...)
        """
        start = time.perf_counter()

        def finish(*, hops: int, success: int, key: Optional[str] = None, extra: Optional[str] = None):
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            evt = MetricEvent(
                protocol=str(base_fields["protocol"]),
                operation=str(base_fields["operation"]),
                n_nodes=int(base_fields["n_nodes"]),
                n_keys=int(base_fields["n_keys"]),
                trial_id=int(base_fields.get("trial_id", 0)),
                hops=int(hops),
                success=int(success),
                time_ms=float(elapsed_ms),
                key=key,
                extra=extra
            )
            self.log(evt)

        return finish
