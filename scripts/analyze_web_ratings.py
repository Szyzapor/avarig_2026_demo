#!/usr/bin/env python3
"""Summarise ratings collected by the online test (Google Sheet export).

Download the "ratings" and "participants" sheets as CSV (File > Download >
CSV) and run:

    python scripts/analyze_web_ratings.py ratings.csv participants.csv

Prints mean MOS with a 95% confidence interval per system, per dataset x
system, and per system split by each questionnaire field. By default only
sessions that passed the left/right headphone check and did not report
listening on loudspeakers are kept (--all keeps everyone).
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from typing import Dict, Iterable, List

SYSTEMS = ("crm", "zhu", "a2b")
SPLIT_FIELDS = ("device", "music_experience", "audio_experience",
                "spatial_audio_experience", "listening_tests", "age")


def ci95(xs: List[float]) -> str:
    n = len(xs)
    if n == 0:
        return "-"
    m = sum(xs) / n
    if n < 2:
        return f"{m:.2f} (n=1)"
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return f"{m:.2f} ± {1.96 * sd / math.sqrt(n):.2f} (n={n})"


def table(title: str, groups: Dict[str, Dict[str, List[float]]]) -> None:
    print(f"\n{title}")
    print(f"  {'':28s}" + "".join(f"{s:>22s}" for s in SYSTEMS))
    for g in sorted(groups):
        print(f"  {g:28s}" + "".join(f"{ci95(groups[g].get(s, [])):>22s}" for s in SYSTEMS))


def read(path: str) -> Iterable[dict]:
    with open(path, newline="", encoding="utf-8") as fp:
        yield from csv.DictReader(fp)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ratings")
    ap.add_argument("participants")
    ap.add_argument("--all", action="store_true", help="do not screen participants")
    args = ap.parse_args()

    people = {p["session_id"]: p for p in read(args.participants)}
    keep = {
        sid for sid, p in people.items()
        if args.all or (str(p.get("lr_passed")).upper() == "TRUE"
                        and p.get("device") != "dev_speakers")
    }
    print(f"participants: {len(people)}, kept after screening: {len(keep)}")

    # Last rating wins if a trial was somehow recorded twice.
    rows = {}
    for r in read(args.ratings):
        if r["session_id"] in keep:
            rows[(r["session_id"], r["dataset"], r["clip_id"], r["system"])] = r

    overall: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    by_ds: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    by_field = {f: defaultdict(lambda: defaultdict(list)) for f in SPLIT_FIELDS}
    for (sid, ds, _clip, system), r in rows.items():
        mos = float(r["mos"])
        overall["all"][system].append(mos)
        by_ds[ds][system].append(mos)
        for f in SPLIT_FIELDS:
            by_field[f][people[sid].get(f) or "(blank)"][system].append(mos)

    table("MOS overall", overall)
    table("MOS by dataset", by_ds)
    for f in SPLIT_FIELDS:
        table(f"MOS by {f}", by_field[f])


if __name__ == "__main__":
    main()
