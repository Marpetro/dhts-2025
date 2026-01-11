from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from src.pastry.local_index import LocalIndex


HEX_BASE = 16


def shared_prefix_len(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def hex_distance(a: str, b: str) -> int:
    # numeric distance in keyspace for comparisons
    return abs(int(a, 16) - int(b, 16))


def in_range_inclusive(x: str, lo: str, hi: str) -> bool:
    xi = int(x, 16)
    return int(lo, 16) <= xi <= int(hi, 16)


@dataclass
class Node:
    """
    Pastry node (simulation).
    - node_id: 32 hex chars (128-bit)
    - leaf_set: up to L nodes below + L nodes above (we will store full list and enforce size in network)
    - routing_table: prefix-based table (rows = prefix length, cols = 16 digits)
    - store: dict key -> value (value can be list of records for same title)
    - local_index: local filtering/ranking structure (your part)
    """
    node_id: str
    leaf_half: int = 4  # L/2 below, L/2 above (so total L = 8)

    # neighbors
    leaf_lower: List[str] = field(default_factory=list)  # sorted ascending by id
    leaf_upper: List[str] = field(default_factory=list)  # sorted ascending by id

    # routing table: row -> col -> node_id
    routing: Dict[int, Dict[int, str]] = field(default_factory=dict)

    # data
    store: Dict[str, Any] = field(default_factory=dict)
    local_index: LocalIndex = field(default_factory=LocalIndex)

    def leaf_all(self) -> List[str]:
        return self.leaf_lower + self.leaf_upper

    def leaf_min_max(self) -> Optional[Tuple[str, str]]:
        all_ids = self.leaf_all()
        if not all_ids:
            return None
        all_ids_sorted = sorted(all_ids, key=lambda x: int(x, 16))
        return all_ids_sorted[0], all_ids_sorted[-1]

    def routing_next_hop(self, target_id: str) -> Optional[str]:
        """
        Standard Pastry idea:
        - Let p = shared prefix length between self and target.
        - Next digit d = target[p]
        - Try routing[p][d]
        """
        p = shared_prefix_len(self.node_id, target_id)
        if p >= len(self.node_id):
            return None
        d_char = target_id[p]
        d = int(d_char, 16)
        row = self.routing.get(p)
        if not row:
            return None
        return row.get(d)

    def candidate_set(self) -> List[str]:
        """
        Candidates used when routing entry is missing:
        - leaf set nodes
        - all routing table entries
        """
        cands = set(self.leaf_all())
        for row in self.routing.values():
            cands.update(row.values())
        cands.discard(self.node_id)
        return list(cands)

    def closest_candidate(self, target_id: str, min_prefix: int) -> Optional[str]:
        """
        Choose candidate that:
        - has prefix >= min_prefix with target
        - and is numerically closest to target
        """
        best = None
        best_dist = None
        for nid in self.candidate_set():
            if shared_prefix_len(nid, target_id) < min_prefix:
                continue
            dist = hex_distance(nid, target_id)
            if best is None or dist < best_dist:  # type: ignore[operator]
                best = nid
                best_dist = dist
        return best