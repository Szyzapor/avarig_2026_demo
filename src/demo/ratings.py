"""Persistence of MOS ratings collected through the Streamlit GUI.

Ratings are appended to a single CSV file inside ``ratings/`` named after
the rater identifier supplied at the start of the session. Every row stores
one rating: dataset, clip, system being rated, the MOS value (1-5), the
session identifier and an ISO timestamp. Optional free-text comments are
stored verbatim.

The CSV schema is intentionally flat so it can be read with any tool
(pandas, Excel, Google Sheets).
"""

from __future__ import annotations

import csv
import datetime as _dt
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional


CSV_HEADER = (
    "timestamp",
    "session_id",
    "rater",
    "dataset",
    "clip_id",
    "system",
    "blind_label",
    "mos",
    "comment",
)


def new_session_id() -> str:
    """Return a short unique identifier for one listening session."""
    return uuid.uuid4().hex[:12]


def now_iso() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


@dataclass
class Rating:
    """A single MOS rating row."""

    timestamp: str
    session_id: str
    rater: str
    dataset: str
    clip_id: str
    system: str          # canonical system name ('crm', 'zhu', 'a2b')
    blind_label: str     # what the user saw in the GUI ('A', 'B', 'C')
    mos: int             # 1..5
    comment: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RatingsStore:
    """Append-only CSV store of ratings for one rater."""

    csv_path: Path
    rows: List[Rating] = field(default_factory=list)

    @classmethod
    def for_rater(cls, root: str | Path, rater: str) -> "RatingsStore":
        """Open (or create) the CSV file for ``rater`` under ``root``."""
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in rater)
        csv_path = root / f"ratings_{safe or 'anonymous'}.csv"
        store = cls(csv_path=csv_path)
        store._ensure_header()
        store.rows = list(store.read_all())
        return store

    def _ensure_header(self) -> None:
        if not self.csv_path.exists() or self.csv_path.stat().st_size == 0:
            with self.csv_path.open("w", newline="", encoding="utf-8") as fp:
                csv.writer(fp).writerow(CSV_HEADER)

    def append(self, rating: Rating) -> None:
        """Append one rating to the CSV and remember it in memory."""
        with self.csv_path.open("a", newline="", encoding="utf-8") as fp:
            csv.writer(fp).writerow([
                rating.timestamp, rating.session_id, rating.rater,
                rating.dataset, rating.clip_id, rating.system,
                rating.blind_label, rating.mos, rating.comment,
            ])
        self.rows.append(rating)

    def read_all(self) -> List[Rating]:
        """Re-read the CSV from disk and return all stored ratings."""
        if not self.csv_path.exists():
            return []
        out: List[Rating] = []
        with self.csv_path.open("r", newline="", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                try:
                    out.append(Rating(
                        timestamp=row["timestamp"],
                        session_id=row["session_id"],
                        rater=row["rater"],
                        dataset=row["dataset"],
                        clip_id=row["clip_id"],
                        system=row["system"],
                        blind_label=row.get("blind_label", ""),
                        mos=int(row["mos"]),
                        comment=row.get("comment", ""),
                    ))
                except (KeyError, ValueError):
                    # Skip malformed rows rather than crash the GUI.
                    continue
        return out

    def count_by_dataset_clip(self) -> dict:
        """Map (dataset, clip_id) -> number of systems rated."""
        out: dict = {}
        for r in self.rows:
            key = (r.dataset, r.clip_id)
            out[key] = out.get(key, 0) + 1
        return out

    def has_rated(self, dataset: str, clip_id: str, system: str,
                  session_id: Optional[str] = None) -> bool:
        """Check whether the given clip + system has been rated.

        When ``session_id`` is provided only ratings from that session count.
        """
        for r in self.rows:
            if r.dataset == dataset and r.clip_id == clip_id and r.system == system:
                if session_id is None or r.session_id == session_id:
                    return True
        return False
