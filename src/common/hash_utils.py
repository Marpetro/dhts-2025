from __future__ import annotations

import hashlib
import re
from typing import Optional


_WS_RE = re.compile(r"\s+")
_NONALNUM_RE = re.compile(r"[^a-z0-9\s]+")


def normalize_title(title: str) -> str:
    """
    Normalize movie titles so that lookups are consistent.
    - lower
    - strip
    - remove punctuation
    - collapse whitespace
    """
    t = (title or "").strip().lower()
    t = _NONALNUM_RE.sub(" ", t)
    t = _WS_RE.sub(" ", t).strip()
    return t


def hash_to_int(text: str, bits: int = 128) -> int:
    """
    Deterministic hash -> integer in [0, 2^bits).
    Default 128 bits (md5) is plenty for simulations.
    """
    if bits <= 0 or bits > 256:
        raise ValueError("bits must be in 1..256")
    # Use SHA-256 and truncate if needed (stable across platforms)
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    value = int.from_bytes(digest, byteorder="big")
    if bits < 256:
        value = value >> (256 - bits)
    return value


def key_for_title(title: str, bits: int = 128) -> int:
    return hash_to_int(normalize_title(title), bits=bits)