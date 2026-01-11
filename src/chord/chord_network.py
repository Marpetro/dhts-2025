from __future__ import annotations

import random
from typing import Dict, List, Tuple, Any, Optional

from src.chord.chord_node import ChordNode


def hex_to_int(h: str) -> int:
    return int(h, 16)


def int_to_hex(i: int, width: int = 32) -> str:
    return f"{i:0{width}x}"


def random_node_id(bits: int = 128) -> str:
    value = random.getrandbits(bits)
    return int_to_hex(value)


class ChordNetwork:
    """Simple in-memory Chord simulator (global-knowledge for simulation).

    The goal is to provide a small, functioning implementation compatible with
    the experiment runner's expectations: `build`, `lookup`, `insert`,
    `get_values`, `join_node`, `leave_node`.
    """

    def __init__(self, m_bits: int = 128, seed: Optional[int] = None) -> None:
        if seed is not None:
            random.seed(seed)
        self.m_bits = m_bits
        self.id_hex_width = m_bits // 4
        self.nodes: Dict[str, ChordNode] = {}

    # -------------------------
    # Build / helpers
    # -------------------------
    def build(self, n_nodes: int) -> None:
        self.nodes.clear()
        ids = set()
        while len(ids) < n_nodes:
            ids.add(random_node_id(self.m_bits))
        sorted_ids = sorted(ids, key=lambda x: hex_to_int(x))
        for nid in sorted_ids:
            self.nodes[nid] = ChordNode(node_id=nid, m_bits=self.m_bits)
        self._recompute_ring(sorted_ids)

    def _recompute_ring(self, sorted_ids: List[str]) -> None:
        n = len(sorted_ids)
        for i, nid in enumerate(sorted_ids):
            node = self.nodes[nid]
            node.successor = sorted_ids[(i + 1) % n]
            node.predecessor = sorted_ids[(i - 1) % n] if n > 1 else None
        # build finger tables (simple: m entries per node)
        for nid in sorted_ids:
            node = self.nodes[nid]
            node.fingers = [None] * self.id_hex_width
            nid_int = hex_to_int(nid)
            mod = 1 << self.m_bits
            for k in range(self.id_hex_width):
                start = (nid_int + (1 << (4 * k))) % mod
                # find successor of start
                succ = self._find_successor_id_by_int(start, sorted_ids)
                node.fingers[k] = succ

    def _find_successor_id_by_int(self, target_int: int, sorted_ids: List[str]) -> str:
        # return first node id whose int value >= target_int, or wrap
        for nid in sorted_ids:
            if hex_to_int(nid) >= target_int:
                return nid
        return sorted_ids[0]

    def _closest_preceding_node(self, current_id: str, key_id: str) -> Optional[str]:
        # search current node's fingers for the closest preceding node to key
        node = self.nodes[current_id]
        key_int = hex_to_int(key_id)
        curr_int = hex_to_int(current_id)
        mod = 1 << self.m_bits
        # iterate fingers from high to low
        for fid in reversed(node.fingers):
            if fid is None:
                continue
            fid_int = hex_to_int(fid)
            # consider fid in (curr, key) modulo ring
            if self._in_interval(fid_int, curr_int, key_int):
                if fid in self.nodes:
                    return fid
        # fallback to successor
        return node.successor if node.successor in self.nodes else None

    def _in_interval(self, value: int, start: int, end: int) -> bool:
        # open interval (start, end) on modulo ring
        mod = 1 << self.m_bits
        if start < end:
            return start < value < end
        if start > end:
            return value > start or value < end
        return False

    # -------------------------
    # DHT operations
    # -------------------------
    def lookup(self, key_id: str, start_node_id: Optional[str] = None, max_hops: int = 10_000) -> Tuple[str, int]:
        if not self.nodes:
            raise RuntimeError("Network is empty. Call build() first.")
        if start_node_id is None:
            current = random.choice(list(self.nodes.keys()))
        else:
            if start_node_id not in self.nodes:
                raise KeyError(f"Unknown start node: {start_node_id}")
            current = start_node_id
        hops = 0
        # simple iterative lookup
        while hops < max_hops:
            node = self.nodes[current]
            succ = node.successor
            if succ is None:
                return current, hops
            # if key is in (current, successor] then successor is responsible
            if self._in_interval(hex_to_int(key_id), hex_to_int(current), hex_to_int(succ)) or hex_to_int(key_id) == hex_to_int(succ):
                return succ, hops + 1
            # otherwise forward to closest preceding node
            next_hop = self._closest_preceding_node(current, key_id)
            if next_hop is None or next_hop == current:
                return current, hops
            current = next_hop
            hops += 1
        return current, hops

    def insert(self, key_id: str, key_str: str, value: Any, start_node_id: Optional[str] = None) -> Tuple[str, int]:
        node_id, hops = self.lookup(key_id, start_node_id=start_node_id)
        node = self.nodes[node_id]
        if key_str in node.store:
            existing = node.store[key_str]
            if isinstance(existing, list):
                existing.append(value)
            else:
                node.store[key_str] = [existing, value]
        else:
            node.store[key_str] = [value]
        return node_id, hops

    def get_values(self, key_id: str, key_str: str, start_node_id: Optional[str] = None) -> Tuple[List[Any], int]:
        node_id, hops = self.lookup(key_id, start_node_id=start_node_id)
        node = self.nodes[node_id]
        vals = node.store.get(key_str, [])
        if isinstance(vals, list):
            return vals, hops
        return [vals], hops

    def delete(self, key_id: str, key_str: str, start_node_id: Optional[str] = None) -> Tuple[bool, int]:
        node_id, hops = self.lookup(key_id, start_node_id=start_node_id)
        node = self.nodes[node_id]
        existed = key_str in node.store
        node.store.pop(key_str, None)
        return existed, hops

    def join_node(self, new_node_id: str, bootstrap_node_id: Optional[str] = None) -> Tuple[str, int]:
        if new_node_id in self.nodes:
            return new_node_id, 0
        self.nodes[new_node_id] = ChordNode(node_id=new_node_id, m_bits=self.m_bits)
        # integrate into ring and recompute fingers globally (simulation shortcut)
        all_ids = sorted(self.nodes.keys(), key=lambda x: hex_to_int(x))
        self._recompute_ring(all_ids)
        if bootstrap_node_id is None or len(self.nodes) == 1:
            return new_node_id, 0
        # do a lookup from bootstrap to find hops
        _, hops = self.lookup(new_node_id, start_node_id=bootstrap_node_id)
        return new_node_id, hops

    def leave_node(self, node_id: str) -> Tuple[str, int]:
        if node_id not in self.nodes:
            return node_id, 0
        node = self.nodes[node_id]
        succ = node.successor
        # move store to successor
        if succ and succ in self.nodes:
            self.nodes[succ].store.update(node.store)
        del self.nodes[node_id]
        if self.nodes:
            all_ids = sorted(self.nodes.keys(), key=lambda x: hex_to_int(x))
            self._recompute_ring(all_ids)
        return node_id, 0
