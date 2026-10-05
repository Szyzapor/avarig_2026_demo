#!/usr/bin/env python3
"""Screen and summarise webMUSHRA results of listening test v2.

    python analyze_results.py results/foa2bin_v2_session1/mushra.csv \
        [results/foa2bin_v2_session2/mushra.csv] [--manifest manifest.json]

Screening rules, fixed before data collection:

1. Training pages (trial id ``training_*``) are not analysed.
2. A page is invalid if every slider is still at the start value (100) or all
   six ratings are equal, or if the listener spent less than ``--min-page-s``
   seconds on it (default 20 s, which is twice the stimulus length).
   webMUSHRA does not lock "Next", so an untouched page would otherwise count
   as a valid all-100 answer.
3. A listener is excluded if they rate the hidden reference below 90 on more
   than 15% of their valid test pages (ITU-R BS.1534-3, section 4.1.2).
4. Repeated pages (``*_repeat``) measure reliability: the mean absolute
   difference to the first rating over the five non-reference stimuli is
   reported per listener, and listeners above ``--max-repeat-diff`` points
   (default 20) are flagged. Flagged listeners are not dropped automatically.
   Repeats are not used in the means.

Output: listeners kept and dropped, then mean ± 95% CI per stimulus for each
criterion, overall and per dataset.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

ORDER = ["reference", "proposed_crm_v2", "zhu2022", "a2b_btpab", "anchor_foa_cardioid", "anchor_lp3500"]
TRIAL_RE = re.compile(r"^(?P<crit>[a-z_]+?)_(?P<ds>zhu|argentum_pg)__(?P<clip>[a-z_]+_\d+)(?P<rep>_repeat)?$")


def ci(xs):
    n = len(xs)
    if n == 0:
        return "-"
    m = statistics.fmean(xs)
    if n < 2:
        return f"{m:5.1f}       (n=1)"
    h = 1.96 * statistics.stdev(xs) / math.sqrt(n)
    return f"{m:5.1f} ± {h:4.1f} (n={n})"


def load(paths):
    pages = defaultdict(dict)        # (session_uuid, trial_id) -> {stimulus: score}
    meta = {}                        # (session_uuid, trial_id) -> (time_s, code)
    for p in paths:
        with open(p, newline="", encoding="utf-8") as fp:
            for r in csv.DictReader(fp):
                key = (r["session_uuid"], r["trial_id"])
                pages[key][r["rating_stimulus"]] = float(r["rating_score"])
                meta[key] = (float(r["rating_time"]) / 1000.0, r.get("participant_code", "").strip().upper())
    return pages, meta


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="+")
    ap.add_argument("--min-page-s", type=float, default=20.0)
    ap.add_argument("--max-repeat-diff", type=float, default=20.0)
    a = ap.parse_args()

    pages, meta = load(a.csv)
    # listener = participant code if given (links both sessions), else session uuid
    who = {k: (meta[k][1] or k[0]) for k in pages}

    valid, invalid = {}, defaultdict(int)
    for k, scores in pages.items():
        tid = k[1]
        if tid.startswith("training_"):
            continue
        vals = list(scores.values())
        untouched = all(v == 100 for v in vals) or len(set(vals)) == 1
        if untouched or meta[k][0] < a.min_page_s:
            invalid[who[k]] += 1
            continue
        valid[k] = scores

    # BS.1534-3 §4.1.2 post-screening on the hidden reference
    ref_low, n_pages = defaultdict(int), defaultdict(int)
    for k, s in valid.items():
        if k[1].endswith("_repeat"):
            continue
        n_pages[who[k]] += 1
        ref_low[who[k]] += s.get("reference", 100) < 90
    dropped = {w for w in n_pages if ref_low[w] > 0.15 * n_pages[w]}

    # reliability from repeated pages
    rep_diff = defaultdict(list)
    for k, s in valid.items():
        if not k[1].endswith("_repeat"):
            continue
        first = valid.get((k[0], k[1][: -len("_repeat")]))
        if first:
            rep_diff[who[k]] += [abs(s[x] - first[x]) for x in s if x != "reference" and x in first]

    print("listener              valid  invalid  ref<90   repeat |Δ|  status")
    for w in sorted(set(who.values())):
        d = statistics.fmean(rep_diff[w]) if rep_diff[w] else float("nan")
        if n_pages[w] == 0:
            status = "no valid pages"
        elif w in dropped:
            status = "DROPPED (BS.1534-3 4.1.2)"
        else:
            status = "flag: unreliable" if d > a.max_repeat_diff else "ok"
        print(f"{w[:20]:20s} {n_pages[w]:6d} {invalid[w]:8d} {ref_low[w]:7d} {d:10.1f}  {status}")

    groups = defaultdict(lambda: defaultdict(list))
    for k, s in valid.items():
        m = TRIAL_RE.match(k[1])
        if not m or m["rep"] or who[k] in dropped:
            continue
        for stim, v in s.items():
            groups[(m["crit"], "all")][stim].append(v)
            groups[(m["crit"], m["ds"])][stim].append(v)

    for (crit, ds) in sorted(groups):
        print(f"\n{crit} · {ds}")
        for stim in ORDER:
            print(f"  {stim:22s} {ci(groups[(crit, ds)].get(stim, []))}")


if __name__ == "__main__":
    main()
