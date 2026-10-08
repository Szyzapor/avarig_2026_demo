#!/usr/bin/env python3
"""Analysis of the online MUSHRA test, fixed before data collection.

Input: the Google Sheet tabs exported as CSV (``mushra.csv``, ``participants.csv``)
and/or JSON files that participants downloaded (``mushra_<pid>_session<n>.json``).

    python scripts/analyze_mushra.py --mushra mushra.csv --participants participants.csv \
        [--json downloads/*.json] [--manifest web/manifest.json]

Requires scipy (Wilcoxon signed-rank test).

Screening (per listener and session; ITU-R BS.1534-3 section 4.1.2 where noted):
  * participants who reported Bluetooth headphones or loudspeakers never reach
    the test pages; listeners who failed the left/right check are excluded;
  * hidden reference rated below 90 on more than 15% of test pages -> excluded
    (BS.1534-3);
  * mid anchor (anchor_lp7000) rated above 90 on more than 15% of the test pages
    where it is audible enough -> excluded (BS.1534-3). "Audible enough" =
    ``mid_anchor_screening`` in the manifest: the 7 kHz low-pass removes at least
    -30 dB of the reference energy. On the other clips (most Argentum excerpts)
    there is too little energy above 7 kHz for this rule to be fair;
  * both 15% rules additionally need at least 2 pages: with only 4 eligible
    mid-anchor pages, "more than 15%" would otherwise mean a single page
    (a stated deviation from BS.1534-3);
  * practice pages are never analysed; repeated pages measure reliability
    (mean |difference| to the original over the six non-reference conditions,
    flagged above 20 points) and are not part of the means.

Primary analysis (session 1, overall quality): for each listener and dataset,
the mean score per condition over that dataset's trials; then, across
listeners, mean ± 95% CI, and paired Wilcoxon signed-rank tests of
proposed_crm_v2 against zhu2022 and against a2b_btpab within each dataset
(4 tests, Holm correction). Session 2 (attributes) is exploratory: the same
per criterion, Holm within each criterion.

Ceiling check: BS.1534-3 warns that results are questionable if most
conditions score 80-100; the share of system ratings (CRM, Zhu, A2B) >= 80 is
reported per dataset.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import math
import statistics
from collections import defaultdict

CONDS = ["reference", "proposed_crm_v2", "zhu2022", "a2b_btpab", "anchor_lp7000", "anchor_lp3500",
         "anchor_foa_cardioid"]
SYSTEMS = ["proposed_crm_v2", "zhu2022", "a2b_btpab"]
BASELINES = ["zhu2022", "a2b_btpab"]


def load_rows(args):
    rows = []
    if args.mushra:
        with open(args.mushra, newline="", encoding="utf-8") as fp:
            for r in csv.DictReader(fp):
                rows.append({"pid": r["pid"], "session": int(r["session"]), "kind": r["kind"],
                             "page_id": r["page_id"], "trial_id": r["trial_id"], "dataset": r["dataset"],
                             "criterion": r["criterion"], "condition": r["condition"],
                             "score": float(r["score"])})
    parts = {}
    if args.participants:
        with open(args.participants, newline="", encoding="utf-8") as fp:
            for r in csv.DictReader(fp):
                if not r.get("excluded"):
                    parts[(r["pid"], int(r["session"]))] = r
    for pattern in args.json or []:
        for f in glob.glob(pattern):
            d = json.load(open(f, encoding="utf-8"))
            key = (d["pid"], int(d["session"]))
            parts.setdefault(key, {"lr_passed": str(d["check"].get("lr_passed")).upper(), **d["survey"]})
            for page in d["results"]:
                for r in page["ratings"]:
                    rows.append({"pid": d["pid"], "session": int(d["session"]), "kind": page["kind"],
                                 "page_id": page["page_id"], "trial_id": page["trial_id"],
                                 "dataset": page["dataset"], "criterion": page["criterion"],
                                 "condition": r["condition"], "score": float(r["score"])})
    # one value per (listener, session, page, condition); the last one wins
    dedup = {(r["pid"], r["session"], r["page_id"], r["condition"]): r for r in rows}
    return list(dedup.values()), parts


def holm(pvals):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    adj, running = [0.0] * len(pvals), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvals) - rank) * pvals[i]))
        adj[i] = running
    return adj


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
    ap.add_argument("--mushra")
    ap.add_argument("--participants")
    ap.add_argument("--json", nargs="*")
    ap.add_argument("--manifest", default="web/manifest.json")
    ap.add_argument("--max-repeat-diff", type=float, default=20.0)
    a = ap.parse_args()
    from scipy import stats

    manifest = json.load(open(a.manifest, encoding="utf-8"))
    mid_ok = {t["id"] for t in manifest["trials"] if t.get("mid_anchor_screening")}
    rows, parts = load_rows(a)

    pages = defaultdict(dict)        # (pid, session, page_id) -> {condition: score}
    meta = {}
    for r in rows:
        if r["kind"] == "training":
            continue
        k = (r["pid"], r["session"], r["page_id"])
        pages[k][r["condition"]] = r["score"]
        meta[k] = r

    listeners = sorted({(k[0], k[1]) for k in pages})
    dropped, report = {}, []
    for lid in listeners:
        test = [k for k in pages if (k[0], k[1]) == lid and meta[k]["kind"] == "test"]
        p = parts.get(lid, {})
        n = len(test)
        ref_low = sum(pages[k].get("reference", 100) < 90 for k in test)
        mid_pages = [k for k in test if meta[k]["trial_id"] in mid_ok]
        mid_high = sum(pages[k].get("anchor_lp7000", 0) > 90 for k in mid_pages)
        diffs = []
        for k in pages:
            if (k[0], k[1]) == lid and meta[k]["kind"] == "repeat":
                orig = pages.get((k[0], k[1], k[2][: -len("_repeat")]))
                if orig:
                    diffs += [abs(pages[k][c] - orig[c]) for c in pages[k] if c != "reference" and c in orig]
        rep = statistics.fmean(diffs) if diffs else float("nan")
        reason = None
        if str(p.get("lr_passed", "TRUE")).upper() not in ("TRUE", "1"):
            reason = "failed L/R check"
        elif n and ref_low > 0.15 * n and ref_low >= 2:
            reason = f"hidden reference < 90 on {ref_low}/{n} pages"
        elif mid_pages and mid_high > 0.15 * len(mid_pages) and mid_high >= 2:
            reason = f"mid anchor > 90 on {mid_high}/{len(mid_pages)} eligible pages"
        if reason:
            dropped[lid] = reason
        report.append((lid, n, ref_low, f"{mid_high}/{len(mid_pages)}", rep,
                       reason or ("flag: repeats differ" if rep > a.max_repeat_diff else "ok")))

    print("listener / session        pages  ref<90  mid>90   repeat|Δ|  status")
    for (pid, s), n, rl, mh, rep, st in report:
        print(f"{pid:18s} s{s}   {n:6d} {rl:7d} {mh:>7s} {rep:10.1f}  {st}")
    for s in (1, 2):
        kept = [l for l in listeners if l[1] == s and l not in dropped]
        print(f"session {s}: {len(kept)} listeners kept, {sum(1 for l in dropped if l[1] == s)} excluded")

    for session, title in ((1, "PRIMARY: session 1, overall quality"), (2, "EXPLORATORY: session 2, attributes")):
        crits = sorted({meta[k]["criterion"] for k in pages if k[1] == session})
        for crit in crits:
            # per-listener means per dataset and condition
            per = defaultdict(lambda: defaultdict(list))
            for k, sc in pages.items():
                if k[1] != session or (k[0], k[1]) in dropped or meta[k]["kind"] != "test" \
                        or meta[k]["criterion"] != crit:
                    continue
                for c, v in sc.items():
                    per[(meta[k]["dataset"], k[0])][c].append(v)
            if not per:
                continue
            print(f"\n=== {title} · {crit}")
            datasets = sorted({d for d, _ in per})
            tests = []
            for ds in datasets:
                lm = {pid: {c: statistics.fmean(v) for c, v in cs.items()} for (d, pid), cs in per.items() if d == ds}
                print(f"\n  {ds} (listener means)")
                for c in CONDS:
                    print(f"    {c:22s} {mean_ci([m[c] for m in lm.values() if c in m])}")
                sysr = [v for (d, _), cs in per.items() if d == ds for c in SYSTEMS for v in cs.get(c, [])]
                if sysr:
                    print(f"    ceiling check: {100 * sum(v >= 80 for v in sysr) / len(sysr):.0f}% of system ratings >= 80")
                for base in BASELINES:
                    pairs = [(m["proposed_crm_v2"], m[base]) for m in lm.values()
                             if "proposed_crm_v2" in m and base in m]
                    d = [x - y for x, y in pairs]
                    if len(d) >= 2 and any(d):
                        p = stats.wilcoxon([x for x, _ in pairs], [y for _, y in pairs]).pvalue
                    else:
                        p = float("nan")
                    tests.append((ds, base, d, p))
            ps = [t[3] for t in tests]
            valid = [i for i, p in enumerate(ps) if not math.isnan(p)]
            adj = holm([ps[i] for i in valid])
            padj = {i: adj[j] for j, i in enumerate(valid)}
            print("\n  CRM - baseline, paired over listeners (Wilcoxon signed-rank, Holm-adjusted)")
            for i, (ds, base, d, p) in enumerate(tests):
                md = statistics.median(d) if d else float("nan")
                print(f"    {ds:12s} vs {base:10s} median diff {md:+6.1f}  mean {mean_ci(d):>22s}  "
                      f"p = {p:.4f}  p_holm = {padj.get(i, float('nan')):.4f}")


if __name__ == "__main__":
    main()
