from __future__ import annotations
import random
from typing import Dict, List, Optional, Tuple, Any
from src.chord.chord_node import ChordNode

class ChordNetwork:
    def __init__(self, m: int = 128):
        self.m = m
        self.nodes: Dict[int, ChordNode] = {}
        self._sorted_ids: List[int] = []

    def build(self, n_nodes: int):
        """Builds the network with n_nodes."""
        self.nodes.clear()
        ids = set()
        while len(ids) < n_nodes:
            ids.add(random.getrandbits(self.m))
        
        self._sorted_ids = sorted(list(ids))
        
        for nid in self._sorted_ids:
            self.nodes[nid] = ChordNode(node_id=nid, m=self.m)
        
        # Ενημέρωση Finger Tables
        self._update_all_fingers()

    def _update_all_fingers(self):
        n = len(self._sorted_ids)
        for i, nid in enumerate(self._sorted_ids):
            node = self.nodes[nid]
            node.successor = self._sorted_ids[(i + 1) % n]
            node.predecessor = self._sorted_ids[(i - 1) % n]
            
            for j in range(self.m):
                start = (nid + 2**j) % (2**self.m)
                node.finger[j] = self._find_first_node_after(start)

    def _find_first_node_after(self, value: int) -> int:
        for nid in self._sorted_ids:
            if nid >= value:
                return nid
        return self._sorted_ids[0]

    def lookup(self, key_id_hex: str) -> Tuple[int, int]:
        """
        Επιστρέφει (responsible_node_id, hops).
        """
        key_id = int(key_id_hex, 16)
        if not self._sorted_ids:
            return 0, 0

        start_node_id = random.choice(self._sorted_ids)
        current = start_node_id
        hops = 0
        
        # Απλοποιημένη λογική Lookup για το πείραμα
        while not self._is_responsible(current, key_id):
            next_node = self._closest_preceding_node(current, key_id)
            if next_node == current:
                current = self.nodes[current].successor
            else:
                current = next_node
            hops += 1
            if hops > 200: break # Safety break
            
        return current, hops

    def _is_responsible(self, node_id: int, key_id: int) -> bool:
        pred = self.nodes[node_id].predecessor
        if pred is None: return True
        if pred < node_id:
            return pred < key_id <= node_id
        else: # Wrap around
            return key_id > pred or key_id <= node_id

    def _closest_preceding_node(self, current_id: int, key_id: int) -> int:
        node = self.nodes[current_id]
        for i in range(self.m - 1, -1, -1):
            finger = node.finger[i]
            if self._is_between(current_id, finger, key_id):
                return finger
        return current_id

    def _is_between(self, start: int, middle: int, end: int) -> bool:
        if start < end:
            return start < middle < end
        else:
            return middle > start or middle < end

    # --- ΟΙ ΜΕΘΟΔΟΙ ΠΟΥ ΕΛΕΙΠΑΝ Ή ΗΤΑΝ ΛΑΘΟΣ ---

    def insert(self, key_id: str, key_str: str, value: Any) -> Tuple[int, int]:
        """
        Βρίσκει τον υπεύθυνο κόμβο και αποθηκεύει την τιμή.
        Επιστρέφει (node_id, hops).
        """
        node_id, hops = self.lookup(key_id)
        if node_id in self.nodes:
            self.nodes[node_id].store[key_str] = value
        return node_id, hops  # <--- ΤΩΡΑ ΕΠΙΣΤΡΕΦΕΙ HOPS, ΟΧΙ None

    def get_values(self, key_id: str, key_str: str) -> Tuple[Any, int]:
        """
        Βρίσκει τον υπεύθυνο κόμβο και επιστρέφει την τιμή.
        Επιστρέφει (value, hops).
        """
        node_id, hops = self.lookup(key_id)
        val = None
        if node_id in self.nodes:
            val = self.nodes[node_id].store.get(key_str)
        return val, hops

    def delete(self, key_id: str, key_str: str) -> Tuple[bool, int]:
        """
        Βρίσκει τον υπεύθυνο κόμβο και διαγράφει την τιμή.
        Επιστρέφει (existed, hops).
        """
        node_id, hops = self.lookup(key_id)
        existed = False
        if node_id in self.nodes:
            existed = key_str in self.nodes[node_id].store
            self.nodes[node_id].store.pop(key_str, None)
        return existed, hops