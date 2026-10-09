#!/usr/bin/env python3
"""Analysis of the webMUSHRA results of listening test v2 (stimuli version 3.1), fixed in advance.

    python analyze_results.py results/foa2bin_v3_session1/mushra.csv \
        [results/foa2bin_v3_session2_*/mushra.csv] [--listener-column pid]

Input: the ``mushra.csv`` files written by webMUSHRA (``session_test_id``, questionnaire columns,
``session_uuid``, ``trial_id``, ``rating_stimulus``, ``rating_score``, ``rating_time`` in ms, ...).
The listener is identified by ``--listener-column`` (default: ``pid`` if present, else
``session_uuid``). Use per-person ?pid= links so that both sessions of one person are joined.
Requires scipy.

Screening:
  1. practice pages (``training_*``) are not analysed;
  2. a page is invalid if all ratings are equal (webMUSHRA starts every slider at 100 and does
     not lock "Next") or the listener spent less than ``--min-page-s`` (20 s) on it;
  3. listeners who answered Bluetooth headphones or loudspeakers (``headphones`` column) or
     failed an L/R check (``lr_passed`` column, if the hosting page records it) are excluded;
  4. a listener is excluded if the hidden reference is rated below 90 on more than 15% of
     their valid test pages and on at least 2 pages (ITU-R BS.1534-3 section 4.1.2). There is
     no mid anchor, and the FOA anchor is never used for screening (it is closer to the
     reference than the baselines on Argentum);
  5. repeated pages (``*_repeat``) give a reliability measure (mean |difference| to the
     original over the five non-reference conditions, flagged above 20 points) and are not
     part of the means.

Analysis: per listener and dataset, the mean score of each condition; across listeners,
mean ± 95% CI and paired Wilcoxon signed-rank tests of proposed_crm_v2 against zhu2022 and
against a2b_btpab within each dataset, Holm-corrected within each criterion. Session 1
(overall) is primary, session 2 (attributes) exploratory. Report Zhu and Argentum separately:
Argentum is the proposed model's training domain (see the README of the repository).
Ceiling check: share of system ratings >= 80 (BS.1534-3 warns if most conditions are 80-100).
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
from collections import defaultdict

CONDS = ["reference", "proposed_crm_v2", "zhu2022", "a2b_btpab", "anchor_lp3500", "anchor_foa_cardioid"]
SYSTEMS = ["proposed_crm_v2", "zhu2022", "a2b_btpab"]
TRIAL = re.compile(r"^(?P<crit>[a-z_]+?)_(?P<ds>zhu|argentum_pg)__(?P<clip>[a-z_]+_\d+)(?P<rep>_repeat)?$")
EXCLUDED_HEADPHONES = {"bluetooth", "speakers"}


def holm(p):
    order = sorted(range(len(p)), key=lambda i: p[i])
    out, run = [0.0] * len(p), 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (len(p) - r) * p[i]))
        out[i] = run
    return out


def mean_ci(xs):
    if not xs:
        return "-"
    m = statistics.fmean(xs)
    if len(xs) < 2:
        return f"{m:5.1f}         (n=1)"
    from scipy import stats
    h = stats.t.ppf(0.975, len(xs) - 1) * statistics.stdev(xs) / math.sqrt(len(xs))
    return f"{m:5.1f} ± {h:4.1f} (n={len(xs)})"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="+")
    ap.add_argument("--listener-column", default=None)
    ap.add_argument("--min-page-s", type=float, default=20.0)
    ap.add_argument("--max-repeat-diff", type=float, default=20.0)
    a = ap.parse_args()
    from scipy import stats

    pages, meta, info = defaultdict(dict), {}, defaultdict(dict)
    for path in a.csv:
        with open(path, newline="", encoding="utf-8") as fp:
            rd = csv.DictReader(fp)
            col = a.listener_column or ("pid" if "pid" in rd.fieldnames else "session_uuid")
            for r in rd:
                who = r[col].strip()
                m = TRIAL.match(r["trial_id"])
                if r["trial_id"].startswith("training_") or not m:
                    continue
                k = (who, r["trial_id"])
                pages[k][r["rating_stimulus"]] = float(r["rating_score"])
                meta[k] = {"crit": m["crit"], "ds": m["ds"], "repeat": bool(m["rep"]),
                           "time_s": float(r["rating_time"]) / 1000.0}
                for c in ("headphones", "lr_passed"):
                    if r.get(c):
                        info[who][c] = r[c]

    valid = {k: v for k, v in pages.items()
             if len(set(v.values())) > 1 and meta[k]["time_s"] >= a.min_page_s}
    listeners = sorted({k[0] for k in pages})
    dropped = {}
    print("listener              valid  invalid  ref<90  repeat|Δ|  status")
    for w in listeners:
        test = [k for k in valid if k[0] == w and not meta[k]["repeat"]]
        invalid = sum(1 for k in pages if k[0] == w) - sum(1 for k in valid if k[0] == w)
        ref_low = sum(valid[k].get("reference", 100) < 90 for k in test)
        diffs = []
        for k in valid:
            if k[0] == w and meta[k]["repeat"]:
                o = valid.get((w, k[1][: -len("_repeat")]))
                if o:
                    diffs += [abs(valid[k][c] - o[c]) for c in valid[k] if c != "reference" and c in o]
        rep = statistics.fmean(diffs) if diffs else float("nan")
        reason = None
        if info[w].get("headphones") in EXCLUDED_HEADPHONES:
            reason = f"headphones: {info[w]['headphones']}"
        elif str(info[w].get("lr_passed", "true")).lower() not in ("true", "1"):
            reason = "failed L/R check"
        elif not test:
            reason = "no valid pages"
        elif ref_low > 0.15 * len(test) and ref_low >= 2:
            reason = f"hidden reference < 90 on {ref_low}/{len(test)} pages"
        if reason:
            dropped[w] = reason
        print(f"{w[:20]:20s} {len(test):6d} {invalid:8d} {ref_low:7d} {rep:10.1f}  "
              f"{reason or ('flag: repeats differ' if rep > a.max_repeat_diff else 'ok')}")
    print(f"{len(listeners) - len(dropped)} listeners kept, {len(dropped)} excluded")

    for crit in sorted({m["crit"] for m in meta.values()}):
        per = defaultdict(lambda: defaultdict(list))
        for k, sc in valid.items():
            if k[0] in dropped or meta[k]["repeat"] or meta[k]["crit"] != crit:
                continue
            for c, v in sc.items():
                per[(meta[k]["ds"], k[0])][c].append(v)
        if not per:
            continue
        print(f"\n=== {'PRIMARY' if crit == 'overall' else 'EXPLORATORY'} · {crit}")
        tests = []
        for ds in sorted({d for d, _ in per}):
            lm = {w: {c: statistics.fmean(v) for c, v in cs.items()} for (d, w), cs in per.items() if d == ds}
            print(f"\n  {ds} (listener means)")
            for c in CONDS:
                print(f"    {c:22s} {mean_ci([m[c] for m in lm.values() if c in m])}")
            sysr = [v for (d, _), cs in per.items() if d == ds for c in SYSTEMS for v in cs.get(c, [])]
            print(f"    ceiling check: {100 * sum(v >= 80 for v in sysr) / max(1, len(sysr)):.0f}% of system ratings >= 80")
            for base in ("zhu2022", "a2b_btpab"):
                pairs = [(m["proposed_crm_v2"], m[base]) for m in lm.values() if "proposed_crm_v2" in m and base in m]
                d = [x - y for x, y in pairs]
                p = stats.wilcoxon([x for x, _ in pairs], [y for _, y in pairs]).pvalue \
                    if len(d) >= 2 and any(d) else float("nan")
                tests.append((ds, base, d, p))
        idx = [i for i, t in enumerate(tests) if not math.isnan(t[3])]
        adj = dict(zip(idx, holm([tests[i][3] for i in idx])))
        print("\n  CRM - baseline, paired over listeners (Wilcoxon signed-rank, Holm)")
        for i, (ds, base, d, p) in enumerate(tests):
            md = statistics.median(d) if d else float("nan")
            print(f"    {ds:12s} vs {base:10s} median {md:+6.1f}  mean {mean_ci(d):>22s}  "
                  f"p = {p:.4f}  p_holm = {adj.get(i, float('nan')):.4f}")


if __name__ == "__main__":
    main()
