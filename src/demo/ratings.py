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


def now_stamp() -> str:
    """Filename-safe sitting timestamp: ``YYYY-MM-DD--HHMM`` (local time)."""
    return _dt.datetime.now().strftime("%Y-%m-%d--%H%M")


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
    def for_rater(cls, root: str | Path, rater: str,
                  stamp: Optional[str] = None) -> "RatingsStore":
        """Open (or create) the CSV file for ``rater`` under ``root``.

        The filename is ``ratings_<YYYY-MM-DD--HHMM>_<name>.csv`` (date and
        sitting-start time first) so a directory of ratings sorts and groups by
        sitting. ``stamp`` must be frozen at session start so every write in one
        sitting lands in the same file; it defaults to the current time.
        """
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in rater.strip())
        stamp = stamp or now_stamp()
        csv_path = root / f"ratings_{stamp}_{safe or 'anonymous'}.csv"
        store = cls(csv_path=csv_path)
        store._ensure_header()
        store.rows = list(store.read_all())
        return store

    def _ensure_header(self) -> None:
        if not self.csv_path.exists() or self.csv_path.stat().st_size == 0:
            with self.csv_path.open("w", newline="", encoding="utf-8") as fp:
                csv.writer(fp).writerow(CSV_HEADER)

    @staticmethod
    def _row(r: Rating) -> list:
        return [
            r.timestamp, r.session_id, r.rater,
            r.dataset, r.clip_id, r.system,
            r.blind_label, r.mos, r.comment,
        ]

    def append(self, rating: Rating) -> None:
        """Append one rating to the CSV and remember it in memory."""
        with self.csv_path.open("a", newline="", encoding="utf-8") as fp:
            csv.writer(fp).writerow(self._row(rating))
        self.rows.append(rating)

    def upsert(self, rating: Rating) -> None:
        """Insert ``rating``, replacing any existing row for the same key.

        The key is ``(session_id, dataset, clip_id, system)`` -- one opinion per
        listener per clip per system. Re-rating overwrites the previous value in
        place (the CSV is rewritten) instead of appending a duplicate row, so a
        plain mean over the file never double-counts a revised score.
        """
        key = (rating.session_id, rating.dataset, rating.clip_id, rating.system)
        out: List[Rating] = []
        replaced = False
        for r in self.read_all():
            if (r.session_id, r.dataset, r.clip_id, r.system) == key:
                if not replaced:
                    out.append(rating)
                    replaced = True
                # drop any further duplicates of this key
            else:
                out.append(r)
        if not replaced:
            out.append(rating)
        with self.csv_path.open("w", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp)
            writer.writerow(CSV_HEADER)
            for r in out:
                writer.writerow(self._row(r))
        self.rows = out

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

    def count_by_dataset_clip(self, session_id: Optional[str] = None) -> dict:
        """Map (dataset, clip_id) -> number of DISTINCT systems rated.

        Counting distinct systems (rather than rows) keeps the value capped at
        the number of systems even if a row was somehow duplicated. When
        ``session_id`` is given, only that session's ratings are counted so the
        progress shown to the current rater is not inflated by earlier sittings.
        """
        seen: dict = {}
        for r in self.rows:
            if session_id is not None and r.session_id != session_id:
                continue
            seen.setdefault((r.dataset, r.clip_id), set()).add(r.system)
        return {k: len(v) for k, v in seen.items()}

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
