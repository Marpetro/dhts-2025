from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class ChordNode:
    node_id: str
    m_bits: int = 128

    def __post_init__(self):
        self.store: Dict[str, Any] = {}
        self.predecessor: Optional[str] = None
        self.successor: Optional[str] = None
        # finger table: list of node ids
        self.fingers: List[Optional[str]] = [None] * (self.m_bits // 4 * 1)  # placeholder size; will be set by network

    def __repr__(self) -> str:  # useful for debugging
        return f"ChordNode({self.node_id})"
