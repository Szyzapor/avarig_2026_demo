#!/usr/bin/env python3
"""Build the audio + manifest for the static (GitHub Pages) listening test.

Reads the clip catalogue (``configs/audio_index.json``) and the rendered WAVs
from the audio root, then for every selected clip writes a short, loudness-
matched FLAC excerpt of each version into ``web/audio/`` and a matching
``web/manifest.json`` that the browser app consumes.

Processing per clip (all done with ffmpeg; no Python dependencies):

* crop ``--duration`` seconds starting at ``--offset`` within the 30 s demo clip,
* optionally invert the polarity of the CRM rendering (``--fix-crm-polarity``).
  Only needed for the v1 package (popr_7 output both channels inverted); the
  v2 package is already time- and polarity-aligned to the reference,
* gain-match every version to ``--lufs`` integrated loudness (EBU R128) so the
  rating is not biased by level differences between systems; if that would put
  any version's true peak above ``--max-peak`` dBTP, the whole clip (all
  versions) is lowered by the same amount so relative levels stay matched,
* short fade-in/out so looping playback does not click,
* encode as 24-bit FLAC (lossless; decodable by Chrome, Firefox, Safari, Edge).

File names are opaque hashes so the system identity does not show up in the
audio URL. (The manifest still maps them to systems - a static site cannot
hide that from a determined visitor.)

Usage:
    DEMO_AUDIO_ROOT=~/avarig_demo_audio python scripts/build_web.py \
        --clips-per-dataset 10 --duration 12
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_REPO = Path(__file__).resolve().parents[1]
_DEFAULT_ROOT = os.environ.get("DEMO_AUDIO_ROOT", str(_REPO / "audio"))

VERSIONS = ("reference", "crm", "zhu", "a2b")
FADE_S = 0.05

DEFAULT_DATASETS = ("zhu", "a2b_2mp", "argentum_pg")


def _ffmpeg(args: List[str]) -> str:
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", *args],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"ffmpeg failed: {' '.join(args)}\n{proc.stderr[-2000:]}")
    return proc.stderr


def _pre_filter(offset: float, duration: float, invert: bool) -> str:
    chain = [f"atrim=start={offset}:duration={duration}", "asetpts=PTS-STARTPTS"]
    if invert:
        chain.append("volume=-1")
    return ",".join(chain)


def measure(wav: Path, offset: float, duration: float, invert: bool) -> Tuple[float, float]:
    """Return (integrated LUFS, true peak dBTP) of the cropped excerpt."""
    log = _ffmpeg(["-i", str(wav), "-af",
                   _pre_filter(offset, duration, invert) + ",ebur128=peak=true",
                   "-f", "null", "-"])
    summary = log[log.rfind("Summary:"):]
    lufs = float(re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", summary).group(1))
    peak = float(re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summary).group(1))
    return lufs, peak


def encode(wav: Path, out: Path, offset: float, duration: float, invert: bool,
           gain_db: float) -> None:
    fade_out = max(0.0, duration - FADE_S)
    af = (_pre_filter(offset, duration, invert)
          + f",volume={gain_db:.3f}dB"
          + f",afade=t=in:d={FADE_S},afade=t=out:st={fade_out:.3f}:d={FADE_S}")
    out.parent.mkdir(parents=True, exist_ok=True)
    _ffmpeg(["-y", "-i", str(wav), "-af", af, "-sample_fmt", "s32", "-bits_per_raw_sample", "24",
             "-c:a", "flac", "-compression_level", "8", str(out)])


def _opaque(salt: str, *parts: str) -> str:
    return hashlib.sha1("/".join((salt, *parts)).encode()).hexdigest()[:12]


def _spread_order(clips: List[dict]) -> List[dict]:
    """Order the catalogue so that any prefix is spread evenly over it
    (bit-reversal style), preferring distinct source recordings first."""
    order, seen, k = [], set(), 1
    while len(order) < len(clips):
        for i in range(k):
            idx = int((2 * i + 1) * len(clips) / (2 * k)) if k > 1 else 0
            if idx not in seen:
                seen.add(idx)
                order.append(clips[idx])
        k *= 2
        if k > 4 * len(clips):
            order += [c for i, c in enumerate(clips) if i not in seen]
            break
    return order


def main(argv: Optional[List[str]] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audio-root", default=_DEFAULT_ROOT)
    ap.add_argument("--catalog", default=str(_REPO / "configs" / "audio_index.json"))
    ap.add_argument("--out", default=str(_REPO / "web"))
    ap.add_argument("--datasets", nargs="+", default=list(DEFAULT_DATASETS),
                    help="dataset ids to include (default: all)")
    ap.add_argument("--clips-per-dataset", type=int, default=10)
    ap.add_argument("--duration", type=float, default=12.0, help="excerpt length (s)")
    ap.add_argument("--offset", type=float, default=9.0,
                    help="excerpt start within the 30 s demo clip (s)")
    ap.add_argument("--lufs", type=float, default=-23.0, help="target loudness")
    ap.add_argument("--min-ref-lufs", type=float, default=-45.0,
                    help="skip excerpts whose reference is quieter than this")
    ap.add_argument("--max-peak", type=float, default=-1.0, help="true-peak ceiling (dBTP)")
    ap.add_argument("--fix-crm-polarity", action=argparse.BooleanOptionalAction,
                    default=False,
                    help="invert the CRM output (v1 audio package only)")
    ap.add_argument("--salt", default="avarig2026")
    args = ap.parse_args(argv)

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")
    root = Path(args.audio_root).expanduser()
    out = Path(args.out)
    audio_out = out / "audio"
    if audio_out.exists():
        shutil.rmtree(audio_out)

    with open(args.catalog, encoding="utf-8") as fp:
        catalog = json.load(fp)

    manifest: Dict = {
        "build": {
            "duration_s": args.duration, "offset_s": args.offset,
            "target_lufs": args.lufs, "max_true_peak_dbtp": args.max_peak,
            "crm_polarity_inverted": args.fix_crm_polarity,
        },
        "datasets": [],
    }
    levels: List[dict] = []

    for ds in catalog["datasets"]:
        if ds["id"] not in args.datasets:
            continue
        playable = [c for c in ds["clips"]
                    if all((root / c["renderings"].get(v, "")).is_file() for v in VERSIONS)]
        if not playable:
            print(f"[skip] {ds['id']}: no complete clips under {root}")
            continue
        # The dataset name is not shown to listeners; it only tags the ratings.
        ds_entry = {"id": ds["id"], "clips": []}
        for clip in _spread_order(playable):
            if len(ds_entry["clips"]) >= args.clips_per_dataset:
                break
            ref = measure(root / clip["renderings"]["reference"], args.offset,
                          args.duration, False)
            if ref[0] < args.min_ref_lufs:
                print(f"[skip] {clip['id']}: reference too quiet ({ref[0]:.1f} LUFS)")
                continue
            meas = {"reference": ref}
            for v in VERSIONS[1:]:
                meas[v] = measure(root / clip["renderings"][v], args.offset,
                                  args.duration, v == "crm" and args.fix_crm_polarity)
            gains = {v: args.lufs - meas[v][0] for v in VERSIONS}
            # Shared headroom correction keeps the versions loudness-matched.
            over = max(meas[v][1] + gains[v] for v in VERSIONS) - args.max_peak
            if over > 0:
                gains = {v: g - over for v, g in gains.items()}
            files = {}
            for v in VERSIONS:
                name = _opaque(args.salt, ds["id"], clip["id"], v) + ".flac"
                encode(root / clip["renderings"][v], audio_out / ds["id"] / name,
                       args.offset, args.duration,
                       v == "crm" and args.fix_crm_polarity, gains[v])
                files[v] = f"audio/{ds['id']}/{name}"
                levels.append({"dataset": ds["id"], "clip": clip["id"], "version": v,
                               "lufs_in": meas[v][0], "peak_in": meas[v][1],
                               "gain_db": round(gains[v], 2)})
            ds_entry["clips"].append({"id": clip["id"], "files": files})
            print(f"[ok] {clip['id']}: gains "
                  + " ".join(f"{v}={gains[v]:+.1f}" for v in VERSIONS)
                  + (f" (headroom -{over:.1f} dB)" if over > 0 else ""))
        ds_entry["clips"].sort(key=lambda c: c["id"])
        manifest["datasets"].append(ds_entry)

    with open(out / "manifest.json", "w", encoding="utf-8") as fp:
        json.dump(manifest, fp, indent=1, ensure_ascii=False)
    with open(_REPO / "configs" / "web_levels.json", "w", encoding="utf-8") as fp:
        json.dump(levels, fp, indent=1)
    size = sum(f.stat().st_size for f in audio_out.rglob("*.flac")) / 1e6
    n = sum(len(d["clips"]) for d in manifest["datasets"])
    print(f"\n{n} clips, {n * len(VERSIONS)} files, {size:.0f} MB -> {audio_out}")


if __name__ == "__main__":
    main()
