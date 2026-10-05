#!/usr/bin/env python3
"""Summarise MOS ratings collected with the Streamlit GUI (app.py).

    python scripts/analyze_demo_ratings.py ratings/            # or several dirs / CSV files

Reads every ``ratings_*.csv`` and ``participants_*.csv``. Rules, fixed before
looking at the results:

1. Only ratings made on audio package ``--audio-version`` (default v2.1) are
   used. Ratings without the column (older app) or from another package are
   counted and reported, never pooled.
2. Only datasets in ``--datasets`` (default zhu, argentum_pg). a2b_2mp is out:
   its FOA input is not standard B-format for the baselines.
3. A session needs a complete listener profile; sessions without one are
   reported and dropped.
4. A session whose ratings are all identical (at least 6 ratings) is dropped
   as non-discriminating.
5. If a row was re-rated, the last value wins (the app already upserts).

Output: kept/dropped counts, mean MOS ± 95% CI per system (overall, per
dataset, per profile group), and paired differences CRM - baseline on the
same clip and session, which removes listener and clip offsets.
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

SYSTEMS = ("crm", "zhu", "a2b")
PROFILE = ("age", "hearing", "headphones", "environment", "music_experience",
           "audio_experience", "spatial_experience", "listening_tests")


def ci(xs):
    if not xs:
        return "-"
    m = statistics.fmean(xs)
    if len(xs) < 2:
        return f"{m:5.2f} (n=1)"
    h = 1.96 * statistics.stdev(xs) / math.sqrt(len(xs))
    return f"{m:5.2f} ± {h:.2f} (n={len(xs)})"


def files(paths, pattern):
    for p in map(Path, paths):
        if p.is_dir():
            yield from sorted(p.glob(pattern))
        elif p.match(pattern):
            yield p


def table(title, groups):
    print(f"\n{title}")
    print(f"  {'':24s}" + "".join(f"{s:>22s}" for s in SYSTEMS))
    for g in sorted(groups):
        print(f"  {g:24s}" + "".join(f"{ci(groups[g].get(s, [])):>22s}" for s in SYSTEMS))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--audio-version", default="v2.1")
    ap.add_argument("--datasets", nargs="+", default=["zhu", "argentum_pg"])
    a = ap.parse_args()

    profiles = {}
    for f in files(a.paths, "participants_*.csv"):
        with open(f, newline="", encoding="utf-8") as fp:
            for r in csv.DictReader(fp):
                profiles[r["session_id"]] = r

    rows, dropped = {}, Counter()
    for f in files(a.paths, "ratings_*.csv"):
        with open(f, newline="", encoding="utf-8") as fp:
            for r in csv.DictReader(fp):
                ver = r.get("audio_version") or "unknown"
                if ver != a.audio_version:
                    dropped[f"audio package {ver}"] += 1
                    continue
                if r["dataset"] not in a.datasets:
                    dropped[f"dataset {r['dataset']}"] += 1
                    continue
                rows[(r["session_id"], r["dataset"], r["clip_id"], r["system"])] = r

    by_session = defaultdict(list)
    for k, r in rows.items():
        by_session[k[0]].append(int(r["mos"]))
    bad = set()
    for sid, scores in by_session.items():
        p = profiles.get(sid)
        if not p or not all(p.get(k) for k in PROFILE):
            bad.add(sid)
            dropped["session without complete profile"] += len(scores)
        elif len(scores) >= 6 and len(set(scores)) == 1:
            bad.add(sid)
            dropped["session with identical ratings"] += len(scores)
    kept = {k: r for k, r in rows.items() if k[0] not in bad}

    raters = {k[0] for k in kept}
    print(f"kept {len(kept)} ratings from {len(raters)} sessions")
    for reason, n in dropped.most_common():
        print(f"  dropped {n:5d}  {reason}")

    overall, per_ds = defaultdict(lambda: defaultdict(list)), defaultdict(lambda: defaultdict(list))
    per_group = {k: defaultdict(lambda: defaultdict(list)) for k in PROFILE}
    for (sid, ds, clip, system), r in kept.items():
        v = int(r["mos"])
        overall["all"][system].append(v)
        per_ds[ds][system].append(v)
        for k in PROFILE:
            per_group[k][profiles[sid][k]][system].append(v)
    table("MOS overall", overall)
    table("MOS by dataset", per_ds)
    for k in PROFILE:
        table(f"MOS by {k}", per_group[k])

    # paired differences on the same session and clip
    diffs = defaultdict(lambda: defaultdict(list))
    clips = defaultdict(dict)
    for (sid, ds, clip, system), r in kept.items():
        clips[(sid, ds, clip)][system] = int(r["mos"])
    for (sid, ds, clip), s in clips.items():
        for base in ("zhu", "a2b"):
            if "crm" in s and base in s:
                diffs["all"][base].append(s["crm"] - s[base])
                diffs[ds][base].append(s["crm"] - s[base])
    print("\nPaired difference CRM - baseline (same session and clip; > 0 favours CRM)")
    for g in sorted(diffs):
        print(f"  {g:24s} vs zhu {ci(diffs[g]['zhu']):>22s}   vs a2b {ci(diffs[g]['a2b']):>22s}")


if __name__ == "__main__":
    main()
