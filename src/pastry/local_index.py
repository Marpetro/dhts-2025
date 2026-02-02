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
    adult: Optional[bool] = None
    original_language: Optional[str] = None
    original_country: Optional[List[str]] = None
    release_date: Optional[str] = None

    genre_names: Optional[List[str]] = None
    production_company_names: Optional[List[str]] = None

    budget: Optional[float] = None
    revenue: Optional[float] = None

    popularity: Optional[float] = None
    vote_average: Optional[float] = None
    runtime: Optional[int] = None
    vote_count: Optional[int] = None
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
        self.by_title: Dict[str, List[str]] = {}
        self.indexes: Dict[str, SortedIndex] = {
            "popularity": SortedIndex(),
            "vote_average": SortedIndex(),
            "runtime": SortedIndex(),
            "vote_count": SortedIndex(),
            "budget": SortedIndex(),
            "revenue": SortedIndex(),
        }

    def upsert(self, rec: MovieRecord) -> None:
        self.records[rec.movie_id] = rec
        self.indexes["popularity"].add_or_update(rec.movie_id, rec.popularity)
        self.indexes["vote_average"].add_or_update(rec.movie_id, rec.vote_average)
        # runtime is int but stored as float in index for simplicity
        self.indexes["runtime"].add_or_update(rec.movie_id, float(rec.runtime) if rec.runtime is not None else None)
        self.indexes["vote_count"].add_or_update(
        rec.movie_id, float(rec.vote_count) if rec.vote_count is not None else None)
        self.indexes["budget"].add_or_update(rec.movie_id, float(rec.budget) if rec.budget is not None else None)
        self.indexes["revenue"].add_or_update(rec.movie_id, float(rec.revenue) if rec.revenue is not None else None)

    def delete(self, movie_id: str) -> None:
        if movie_id not in self.records:
            return
        self.records.pop(movie_id, None)
        for idx in self.indexes.values():
            idx.remove(movie_id)
def upsert_for_title(self, title: str, rec: MovieRecord) -> None:
    """
    Upsert record και σύνδεση του movie_id κάτω από το συγκεκριμένο title.
    """
    self.upsert(rec)

    ids = self.by_title.setdefault(title, [])
    if rec.movie_id not in ids:
        ids.append(rec.movie_id)

def get_by_title(self, title: str) -> List[MovieRecord]:
    """
    Επιστρέφει όλα τα records που ανήκουν στο συγκεκριμένο title.
    """
    ids = self.by_title.get(title, [])
    return [self.records[mid] for mid in ids if mid in self.records]

def delete_for_title(self, title: str, movie_id: str) -> None:
    """
    Σβήνει συγκεκριμένο movie_id και το αποσυνδέει από το title.
    """
    # remove from title list
    if title in self.by_title:
        self.by_title[title] = [mid for mid in self.by_title[title] if mid != movie_id]
        if not self.by_title[title]:
            self.by_title.pop(title, None)

    # remove record + indexes
    self.delete(movie_id)

def delete_title(self, title: str) -> None:
    """
    Σβήνει ΟΛΑ τα records κάτω από ένα title.
    """
    ids = self.by_title.pop(title, [])
    for mid in ids:
        self.delete(mid)

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

def range_query_within_title(self, title: str, field: str, low: float, high: float) -> List[MovieRecord]:
    if field not in self.indexes:
        raise KeyError(f"Unknown field index: {field}")

    ids_in_range = set(self.indexes[field].range_query_ids(low, high))
    title_ids = self.by_title.get(title, [])
    return [self.records[mid] for mid in title_ids if mid in ids_in_range and mid in self.records]

def top_k_within_title(self, title: str, field: str, k: int) -> List[MovieRecord]:
    if field not in self.indexes:
        raise KeyError(f"Unknown field index: {field}")

    title_set = set(self.by_title.get(title, []))
    # πάρε παραπάνω candidates και φιλτράρισε
    candidates = self.indexes[field].top_k_ids(max(k * 5, k))
    out = [self.records[mid] for mid in candidates if mid in title_set and mid in self.records]
    return out[:k]
