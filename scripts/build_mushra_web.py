#!/usr/bin/env python3
"""Pack the MUSHRA stimulus package for the static site (web/).

Input is a package built by ``code/build_listening_test_v2r.py --mid-anchor``
(``manifest.json`` + ``audio/<hash>.wav``, all 48 kHz / 24-bit, aligned and at
-23 LUFS). Output:

* ``web/audio/<hash>.flac``: the same samples, 24-bit FLAC (lossless),
* ``web/manifest.json``: trials (dataset, clip, role, files per condition) and,
  per trial, whether the 7 kHz mid anchor removes enough energy (at least
  ``--mid-anchor-min-db``) to be used for listener screening.

    python scripts/build_mushra_web.py ~/listening_test_v2r_mushra_web
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("package")
    ap.add_argument("--out", default=str(_REPO / "web"))
    ap.add_argument("--mid-anchor-min-db", type=float, default=-30.0,
                    help="mid anchor counts for screening only if (ref - anchor) energy >= this, rel. to ref")
    a = ap.parse_args()
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found")

    pkg, out = Path(a.package), Path(a.out)
    audio = out / "audio"
    if audio.exists():
        shutil.rmtree(audio)
    audio.mkdir(parents=True)
    src = json.loads((pkg / "manifest.json").read_text())

    try:
        import numpy as np
        import soundfile as sf
    except ImportError:
        np = sf = None

    trials = []
    for t in src:
        files = {}
        for cond, info in t["stimuli"].items():
            wav = pkg / info["file"]
            flac = audio / (wav.stem + ".flac")
            subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-y", "-i", str(wav),
                            "-c:a", "flac", "-compression_level", "8",
                            "-sample_fmt", "s32", "-bits_per_raw_sample", "24", str(flac)],
                           check=True, capture_output=True)
            files[cond] = f"audio/{flac.name}"
        entry = {"id": f"{t['dataset']}__{t['clip']}", "dataset": t["dataset"], "clip": t["clip"],
                 "role": t["role"], "files": files}
        if np is not None and "anchor_lp7000" in t["stimuli"]:
            ref, _ = sf.read(str(pkg / t["stimuli"]["reference"]["file"]))
            mid, _ = sf.read(str(pkg / t["stimuli"]["anchor_lp7000"]["file"]))
            removed = float(10 * np.log10(((ref - mid) ** 2).sum() / (ref ** 2).sum()))
            entry["mid_anchor_removed_db"] = round(removed, 1)
            entry["mid_anchor_screening"] = removed >= a.mid_anchor_min_db
        trials.append(entry)
        print(f"  {entry['id']:30s} {entry['role']:8s} mid-anchor removed "
              f"{entry.get('mid_anchor_removed_db', '?')} dB -> screening {entry.get('mid_anchor_screening')}")

    with wave.open(str(pkg / src[0]["stimuli"]["reference"]["file"])) as w:
        sr = w.getframerate()
    manifest = {"package": pkg.name, "sample_rate": sr, "conditions": list(src[0]["stimuli"]),
                "mid_anchor_min_db": a.mid_anchor_min_db, "trials": trials}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    size = sum(f.stat().st_size for f in audio.glob("*.flac")) / 1e6
    print(f"{len(trials)} trials, {len(list(audio.glob('*.flac')))} files, {size:.0f} MB -> {audio}")


if __name__ == "__main__":
    main()
