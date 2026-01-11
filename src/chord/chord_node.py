from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class ChordNode:
    node_id: int
    m: int = 128

    successor: Optional[int] = None
    predecessor: Optional[int] = None

    # finger[i] = successor of (node_id + 2^i)
    finger: List[int] = field(default_factory=list)

    store: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.finger = [self.node_id for _ in range(self.m)]