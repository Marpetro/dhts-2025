from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

from src.pastry.node import Node, shared_prefix_len, hex_distance, in_range_inclusive


def random_node_id(bits: int = 128) -> str:
    # 128-bit -> 32 hex chars
    value = random.getrandbits(bits)
    return f"{value:032x}"


@dataclass
class LookupResult:
    responsible_node_id: str
    hops: int
    found_exact: bool


class PastryNetwork:
    """
    In-memory Pastry simulator suitable for experiments.
    - build() creates N nodes and initializes leaf sets + routing tables from global knowledge
      (OK for a project simulator; later you can refine join protocol if needed).
    - lookup() routes hop-by-hop and counts hops.
    """
    def __init__(self, leaf_total: int = 8, id_bits: int = 128, seed: Optional[int] = None) -> None:
        if seed is not None:
            random.seed(seed)
        if leaf_total % 2 != 0:
            raise ValueError("leaf_total must be even (e.g., 8)")
        self.leaf_total = leaf_total
        self.leaf_half = leaf_total // 2
        self.id_bits = id_bits

        self.nodes: Dict[str, Node] = {}

    # -------------------------
    # Build / maintenance
    # -------------------------
    def build(self, n_nodes: int) -> None:
        self.nodes.clear()

        # generate unique IDs
        ids = set()
        while len(ids) < n_nodes:
            ids.add(random_node_id(self.id_bits))
        sorted_ids = sorted(ids, key=lambda x: int(x, 16))

        # create nodes
        for nid in sorted_ids:
            self.nodes[nid] = Node(node_id=nid, leaf_half=self.leaf_half)

        # initialize leaf sets and routing tables from global view (simulation shortcut)
        self._recompute_all_leaf_sets(sorted_ids)
        self._recompute_all_routing_tables(sorted_ids)

    def _recompute_all_leaf_sets(self, sorted_ids: List[str]) -> None:
        n = len(sorted_ids)
        for idx, nid in enumerate(sorted_ids):
            node = self.nodes[nid]
            # lower neighbors: up to leaf_half smaller ids
            lower = sorted_ids[max(0, idx - self.leaf_half):idx]
            # upper neighbors: up to leaf_half larger ids
            upper = sorted_ids[idx + 1: min(n, idx + 1 + self.leaf_half)]
            node.leaf_lower = lower[:]  # already sorted
            node.leaf_upper = upper[:]

    def _recompute_all_routing_tables(self, sorted_ids: List[str]) -> None:
        # For each node, fill routing table entries using any node with matching prefix requirements.
        # Pastry routing: routing[row=prefix_len][col=digit] gives a node with that prefix+digit.
        for nid in sorted_ids:
            node = self.nodes[nid]
            node.routing.clear()
            L = len(nid)  # 32 hex chars

            for row in range(L):
                node.routing[row] = {}

            for other in sorted_ids:
                if other == nid:
                    continue
                p = shared_prefix_len(nid, other)
                if p >= L:
                    continue
                digit = int(other[p], 16)
                # only fill if empty; any choice works for simulation
                if digit not in node.routing[p]:
                    node.routing[p][digit] = other

    # -------------------------
    # DHT operations (basic)
    # -------------------------
    def lookup(self, key_id: str, start_node_id: Optional[str] = None, max_hops: int = 10_000) -> LookupResult:
        """
        Route from start_node_id (or a random node) toward key_id.
        Returns the "responsible" node as:
        - if key_id equals some node_id => that node
        - else the node whose id is numerically closest among candidates when routing converges
        """
        if not self.nodes:
            raise RuntimeError("Network is empty. Call build() first.")

        if start_node_id is None:
            start_node_id = random.choice(list(self.nodes.keys()))
        if start_node_id not in self.nodes:
            raise KeyError(f"Unknown start node: {start_node_id}")

        current = start_node_id
        hops = 0

        while hops < max_hops:
            if current == key_id:
                return LookupResult(responsible_node_id=current, hops=hops, found_exact=True)

            node = self.nodes[current]

            # 1) If key is within leaf set range, forward to closest in leaf set (or self).
            leaf_range = node.leaf_min_max()
            if leaf_range is not None:
                lo, hi = leaf_range
                # If key lies between smallest and largest leaf neighbor, choose closest among leaf+current
                if in_range_inclusive(key_id, lo, hi):
                    candidates = node.leaf_all() + [node.node_id]
                    next_id = min(candidates, key=lambda nid: hex_distance(nid, key_id))
                    if next_id == current:
                        return LookupResult(responsible_node_id=current, hops=hops, found_exact=False)
                    current = next_id
                    hops += 1
                    continue

            # 2) Try routing table entry
            p = shared_prefix_len(node.node_id, key_id)
            rt_next = node.routing_next_hop(key_id)
            if rt_next is not None and rt_next in self.nodes:
                current = rt_next
                hops += 1
                continue

            # 3) Fallback: pick closest candidate with prefix >= p
            fallback = node.closest_candidate(key_id, min_prefix=p)
            if fallback is None:
                # no better candidate known; stop here
                return LookupResult(responsible_node_id=current, hops=hops, found_exact=False)

            # if fallback isn't improving distance, stop
            if hex_distance(fallback, key_id) >= hex_distance(current, key_id):
                return LookupResult(responsible_node_id=current, hops=hops, found_exact=False)

            current = fallback
            hops += 1

        # safety
        return LookupResult(responsible_node_id=current, hops=hops, found_exact=False)

    def insert(self, key_id: str, key_str: str, value: Any, start_node_id: Optional[str] = None) -> Tuple[str, int]:
        """
        Insert (key_str -> value) to responsible node found via lookup(key_id).
        Returns (responsible_node_id, hops)
        """
        res = self.lookup(key_id, start_node_id=start_node_id)
        node = self.nodes[res.responsible_node_id]
        # allow multiple records per title (duplicates): store list
        if key_str in node.store:
            existing = node.store[key_str]
            if isinstance(existing, list):
                existing.append(value)
            else:
                node.store[key_str] = [existing, value]
        else:
            node.store[key_str] = [value]
        return res.responsible_node_id, res.hops

    def get_values(self, key_id: str, key_str: str, start_node_id: Optional[str] = None) -> Tuple[List[Any], int]:
        res = self.lookup(key_id, start_node_id=start_node_id)
        node = self.nodes[res.responsible_node_id]
        vals = node.store.get(key_str, [])
        if isinstance(vals, list):
            return vals, res.hops
        return [vals], res.hops

    def delete(self, key_id: str, key_str: str, start_node_id: Optional[str] = None) -> Tuple[bool, int]:
        res = self.lookup(key_id, start_node_id=start_node_id)
        node = self.nodes[res.responsible_node_id]
        existed = key_str in node.store
        node.store.pop(key_str, None)
        return existed, res.hops

def join_node(self, new_node_id: str, bootstrap_node_id: Optional[str] = None) -> int:
    """
    Εισαγωγή νέου κόμβου στο δίκτυο. 
    Επιστρέφει τον αριθμό των hops που απαιτήθηκαν για το join.
    """
    if new_node_id in self.nodes:
        return 0
    
    new_node = Node(node_id=new_node_id, leaf_half=self.leaf_half)
    self.nodes[new_node_id] = new_node
    
    if not bootstrap_node_id or len(self.nodes) == 1:
        # Ο πρώτος κόμβος ή αν δεν υπάρχει bootstrap, ενημερώνουμε στατικά
        self._recompute_all_leaf_sets(sorted(self.nodes.keys(), key=lambda x: int(x, 16)))
        return 0

    # Προσομοίωση του Join Protocol:
    # 1. Routing προς το ID του νέου κόμβου
    res = self.lookup(new_node_id, start_node_id=bootstrap_node_id)
    
    # 2. Ενημέρωση Routing Table & Leaf Set (Simulation of data exchange)
    # Στην πραγματικότητα ο νέος κόμβος παίρνει στοιχεία από κάθε hop.
    # Εδώ ανανεώνουμε τη δομή για να αντικατοπτρίζει τη νέα κατάσταση.
    all_ids = sorted(self.nodes.keys(), key=lambda x: int(x, 16))
    self._recompute_all_leaf_sets(all_ids)
    self._recompute_all_routing_tables(all_ids)
    
    return res.hops

def leave_node(self, node_id: str):
    """
    Αφαίρεση κόμβου και ανακατανομή των δεδομένων του (προαιρετικά).
    """
    if node_id not in self.nodes:
        return
    
    # Μεταφορά δεδομένων στους γείτονες (απαραίτητο για DHT consistency)
    node_to_leave = self.nodes[node_id]
    all_ids = sorted(self.nodes.keys(), key=lambda x: int(x, 16))
    idx = all_ids.index(node_id)
    
    # Ο κοντινότερος γείτονας αναλαμβάνει τα κλειδιά
    neighbor_id = all_ids[idx-1] if idx > 0 else all_ids[idx+1]
    self.nodes[neighbor_id].store.update(node_to_leave.store)
    
    # Αφαίρεση και αναδιοργάνωση
    del self.nodes[node_id]
    new_ids = sorted(self.nodes.keys(), key=lambda x: int(x, 16))
    self._recompute_all_leaf_sets(new_ids)
    self._recompute_all_routing_tables(new_ids)