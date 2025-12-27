from __future__ import annotations

from dataclasses import dataclass
from bisect import bisect_left, bisect_right, insort
from typing import Any, Dict, List, Tuple, Optional, Iterable


@dataclass(frozen=True)
class MovieRecord:
    """
    Ελάχιστο record. Μπορείς να προσθέσεις πεδία όταν φορτώσεις το dataset.
    """
    movie_id: str
    title: str
    popularity: Optional[float] = None
    vote_average: Optional[float] = None
    runtime: Optional[int] = None
    # ... πρόσθεσε ό,τι άλλο θες


class SortedIndex:
    """
    Sorted list index for one numeric field.
    Stores (value, movie_id) sorted ascending.
    """
    def __init__(self) -> None:
        self._pairs: List[Tuple[float, str]] = []
        self._pos: Dict[str, float] = {}  # movie_id -> value

    def add_or_update(self, movie_id: str, value: Optional[float]) -> None:
        if value is None:
            # if missing value, keep it out of the index
            self.remove(movie_id)
            return

        if movie_id in self._pos:
            old = self._pos[movie_id]
            if old == value:
                return
            self._remove_pair(old, movie_id)

        insort(self._pairs, (float(value), movie_id))
        self._pos[movie_id] = float(value)

    def remove(self, movie_id: str) -> None:
        if movie_id not in self._pos:
            return
        old = self._pos.pop(movie_id)
        self._remove_pair(old, movie_id)

    def _remove_pair(self, value: float, movie_id: str) -> None:
        # find range with same value and remove exact id
        left = bisect_left(self._pairs, (value, ""))
        right = bisect_right(self._pairs, (value, chr(0x10FFFF)))
        for i in range(left, right):
            if self._pairs[i][1] == movie_id:
                self._pairs.pop(i)
                return

    def range_query_ids(self, low: float, high: float) -> List[str]:
        if low > high:
            low, high = high, low
        left = bisect_left(self._pairs, (float(low), ""))
        right = bisect_right(self._pairs, (float(high), chr(0x10FFFF)))
        return [mid for _, mid in self._pairs[left:right]]

    def top_k_ids(self, k: int) -> List[str]:
        if k <= 0:
            return []
        # largest values at end
        return [mid for _, mid in self._pairs[-k:]][::-1]  # descending


class LocalIndex:
    """
    Holds records and a couple of numeric indexes (popularity, vote_average, runtime...).
    """
    def __init__(self) -> None:
        self.records: Dict[str, MovieRecord] = {}
        self.indexes: Dict[str, SortedIndex] = {
            "popularity": SortedIndex(),
            "vote_average": SortedIndex(),
            "runtime": SortedIndex(),
        }

    def upsert(self, rec: MovieRecord) -> None:
        self.records[rec.movie_id] = rec
        self.indexes["popularity"].add_or_update(rec.movie_id, rec.popularity)
        self.indexes["vote_average"].add_or_update(rec.movie_id, rec.vote_average)
        # runtime is int but stored as float in index for simplicity
        self.indexes["runtime"].add_or_update(rec.movie_id, float(rec.runtime) if rec.runtime is not None else None)

    def delete(self, movie_id: str) -> None:
        if movie_id not in self.records:
            return
        self.records.pop(movie_id, None)
        for idx in self.indexes.values():
            idx.remove(movie_id)

    def range_query(self, field: str, low: float, high: float) -> List[MovieRecord]:
        if field not in self.indexes:
            raise KeyError(f"Unknown field index: {field}")
        ids = self.indexes[field].range_query_ids(low, high)
        return [self.records[mid] for mid in ids if mid in self.records]

    def top_k(self, field: str, k: int) -> List[MovieRecord]:
        if field not in self.indexes:
            raise KeyError(f"Unknown field index: {field}")
        ids = self.indexes[field].top_k_ids(k)
        return [self.records[mid] for mid in ids if mid in self.records]
