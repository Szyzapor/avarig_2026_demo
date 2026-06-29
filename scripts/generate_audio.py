#!/usr/bin/env python3
"""Generate every demo audio file from a small set of FOA recordings.

The script picks a few representative segments from each source dataset,
crops them to a fixed duration, renders them with each of the three
rendering systems (Proposed CRM, Zhu et al., A2B), and writes the
resulting WAV files into ``audio/<dataset_id>/<clip_id>/``. It also
writes the corresponding ground-truth binaural reference taken from the
same time-aligned region of the paired binaural file.

Configuration lives in ``configs/clips.yaml``. Each entry names a source
dataset, the FOA file (or files), the paired binaural file, and a list
of (start_s, duration_s) excerpts. The script reads the configuration,
renders every excerpt with every model, and finally writes
``configs/audio_index.json`` which the Streamlit GUI consumes.

The script depends on the trained checkpoints and on the model wrappers
shipped with ``foa2binaural-eval``. Set the environment variable
``FOA2BIN_EVAL`` to the path of that repository if it does not live as a
sibling of this one. Checkpoint paths are read from environment variables
``CRM_CHECKPOINT``, ``ZHU_CHECKPOINT``, ``A2B_CHECKPOINT_<DATASET>``;
sensible defaults are provided below.

Usage:
    python scripts/generate_audio.py --duration 8
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import soundfile as sf
import torch

_REPO = Path(__file__).resolve().parents[1]

# Default sibling of this repo. The wrappers from `foa2binaural-eval`
# (CRM, Zhu, A2B) are reused so the demo always renders with the exact
# code paths used in the paper evaluation.
_DEFAULT_EVAL = Path(os.environ.get("FOA2BIN_EVAL",
                                    _REPO.parent / "foa2binaural-eval"))


# ---------------------------------------------------------------- defaults

# Per-dataset filename pairing rules. The script enumerates FOA files in
# ``foa_root`` and rewrites the basename with the pair-function to obtain
# the matching binaural file in ``bin_root``. ``foa_glob`` filters the
# FOA listing so we do not pick up unrelated WAVs in the same directory.
PAIRING_RULES = {
    "zhu":         {"foa_glob": "AmbiX-*.wav",
                    "pair_fn":  lambda n: n.replace("AmbiX-", "Binaural-")},
    "a2b_2mp":     {"foa_glob": "*_ambisonics.wav",
                    "pair_fn":  lambda n: n.replace("_ambisonics.wav", "_binaural.wav")},
    "argentum_pg": {"foa_glob": "FOA_*.wav",
                    "pair_fn":  lambda n: n.replace("FOA_", "BIN_", 1)},
    "echo_project": {"foa_glob": "*.wav",
                     "pair_fn":  lambda n: n},  # filled in once layout is known
}


# Clip catalogue used when no YAML config is supplied. Only the dataset
# metadata is hard-coded; the actual files and excerpt offsets are
# discovered at runtime by :func:`_auto_discover` so that adding new
# recordings to the source directory is enough to make them appear here.
DEFAULT_CLIPS = {
    "datasets": [
        {
            "id": "zhu",
            "label": "Zhu (ByteDance)",
            "description": "Outdoor music, 48 kHz first-order ambisonics.",
            "a2b_checkpoint_id": "btpab",
            "foa_root": "/home/smck/Argentum_new/datasets/dataset_zhu/ambisonic-binaural/test/ambisonic",
            "bin_root": "/home/smck/Argentum_new/datasets/dataset_zhu/ambisonic-binaural/test/binaural",
            "data_sr": 48000,
        },
        {
            "id": "a2b_2mp",
            "label": "Meta A2B 2-MP",
            "description": "Meta capture, 44.1 kHz first-order ambisonics.",
            "a2b_checkpoint_id": "btpab",   # cross-dataset, no native 4ch ckpt
            "foa_root": "/home/smck/Argentum_new/datasets/dataset_a2b_2mp/test/ambisonic",
            "bin_root": "/home/smck/Argentum_new/datasets/dataset_a2b_2mp/test/binaural",
            "data_sr": 44100,
        },
        {
            "id": "argentum_pg",
            "label": "Argentum PG (Gdansk Tech)",
            "description": "Concert hall recordings, 48 kHz first-order ambisonics.",
            "a2b_checkpoint_id": "btpab",
            "foa_root": "/home/smck/Argentum_new/datasets/dataset_argentum/NAS_Argentum/ambisonic",
            "bin_root": "/home/smck/Argentum_new/datasets/dataset_argentum/NAS_Argentum/binaural",
            "data_sr": 48000,
        },
        # Echo Project placeholder. Drop the FOA / binaural WAVs into the
        # directories listed here once they are available; the dataset
        # block will then appear in the GUI automatically.
        {
            "id": "echo_project",
            "label": "Echo Project (optional)",
            "description": "Placeholder; add files once FOA recordings are available.",
            "a2b_checkpoint_id": "btpab",
            "foa_root": "",
            "bin_root": "",
            "data_sr": 48000,
        },
    ]
}


@dataclass
class Excerpt:
    foa_path: Path
    bin_path: Path
    start_s: float
    duration_s: float
    dataset_sr: int


# ---------------------------------------------------------------- helpers

def _ensure_eval_on_path(eval_root: Path) -> None:
    """Make the foa2binaural-eval source importable."""
    if not (eval_root / "src" / "models" / "__init__.py").exists():
        raise FileNotFoundError(
            f"foa2binaural-eval not found at {eval_root}. "
            "Set FOA2BIN_EVAL to its repository root."
        )
    if str(eval_root) not in sys.path:
        sys.path.insert(0, str(eval_root))


def _slice_foa_to_temp(src: Path, start_s: float, duration_s: float) -> Tuple[torch.Tensor, int]:
    """Load and crop a FOA WAV; return a ``[C, L]`` tensor and the file sr."""
    info = sf.info(str(src))
    sr = info.samplerate
    start = int(start_s * sr)
    stop = int((start_s + duration_s) * sr)
    data, _ = sf.read(str(src), start=start, stop=stop, dtype="float32", always_2d=True)
    # Keep only the first four channels if a higher-order file is supplied.
    data = data[:, :4]
    foa = torch.from_numpy(data.T.copy())
    return foa, sr


def _save_wav(path: Path, audio: torch.Tensor, sr: int) -> None:
    """Write a ``[C, L]`` tensor as a WAV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), audio.cpu().numpy().T, sr)


def _render_with_renderers(
    foa: torch.Tensor,
    sr: int,
    crm,
    zhu,
    a2b,
) -> Dict[str, torch.Tensor]:
    """Render the cropped FOA with each available renderer.

    The eval-framework renderers honour their own ``input_sr`` attribute,
    so we set it explicitly to the file sample rate before calling
    :meth:`predict`. Returned tensors are channel-first ``[2, L]``.
    """
    out: Dict[str, torch.Tensor] = {}
    for name, renderer in (("crm", crm), ("zhu", zhu), ("a2b", a2b)):
        if renderer is None:
            continue
        try:
            renderer.input_sr = sr
        except Exception:
            pass
        l, r = renderer.predict(foa)
        out[name] = torch.stack([l.cpu().detach(), r.cpu().detach()])
    return out


def _build_renderers(eval_root: Path, dataset_a2b_id: str):
    """Instantiate the CRM, Zhu and A2B wrappers from ``foa2binaural-eval``."""
    from src.models.proposed_crm import ProposedCRMRenderer  # type: ignore
    from src.models.zhu_baseline import ZhuBaselineRenderer  # type: ignore
    from src.models.a2b_baseline import A2BBaselineRenderer  # type: ignore

    code_dir = eval_root.parent / "code"

    crm_ckpt = Path(os.environ.get(
        "CRM_CHECKPOINT",
        eval_root.parent / "models" / "binaural_rendering_popr7_Zhu_PG.pt"
    ))
    zhu_ckpt = Path(os.environ.get(
        "ZHU_CHECKPOINT",
        eval_root.parent / "Zhu" / "models" / "binaural_rendering_100.pt"
    ))
    zhu_code = eval_root.parent / "Zhu" / "train.py"

    a2b_dir = (code_dir / "_A2B_repo" / "pretrained_models" / dataset_a2b_id
               / "checkpoints" / "last.ckpt")
    a2b_repo = code_dir / "_A2B_repo"

    crm = ProposedCRMRenderer(
        checkpoint=str(crm_ckpt), code_dir=str(code_dir), device="cpu",
    ) if crm_ckpt.exists() else None
    zhu = ZhuBaselineRenderer(
        checkpoint=str(zhu_ckpt), zhu_code=str(zhu_code), device="cpu",
    ) if zhu_ckpt.exists() else None
    a2b = A2BBaselineRenderer(
        checkpoint=str(a2b_dir), a2b_repo=str(a2b_repo), device="cpu",
    ) if a2b_dir.exists() else None
    return crm, zhu, a2b


def _read_bin_excerpt(bin_path: Path, start_s: float, duration_s: float) -> Tuple[torch.Tensor, int]:
    """Load the matching binaural reference slice."""
    info = sf.info(str(bin_path))
    sr = info.samplerate
    start = int(start_s * sr)
    stop = int((start_s + duration_s) * sr)
    data, _ = sf.read(str(bin_path), start=start, stop=stop, dtype="float32", always_2d=True)
    data = data[:, :2]
    return torch.from_numpy(data.T.copy()), sr


# ---------------------------------------------------------------- main

def _load_config(path: Optional[str]) -> dict:
    if not path:
        return DEFAULT_CLIPS
    with open(path, "r", encoding="utf-8") as fp:
        import yaml  # local import; yaml only needed when a config is supplied
        return yaml.safe_load(fp)


def _auto_discover(ds_cfg: dict, duration: float, target: int) -> List[dict]:
    """Build the (foa, bin, start_s) excerpt list for one dataset by scanning disk.

    For every paired FOA / binaural file:

    * one excerpt centred in the file (long enough margin from both ends) is
      always taken first,
    * a second excerpt near the start (offset 5 s) is taken on the second
      pass if the target count is not yet reached and the file is long
      enough,
    * a third excerpt three-quarters of the way through is added on a
      third pass when needed.

    The order is deterministic so re-running the script produces the same
    clip identifiers as long as the source directories are unchanged.
    """
    foa_root = Path(ds_cfg.get("foa_root", ""))
    bin_root = Path(ds_cfg.get("bin_root", ""))
    if not foa_root or not bin_root or not foa_root.is_dir():
        return []

    rules = PAIRING_RULES.get(ds_cfg["id"], {})
    foa_glob = rules.get("foa_glob", "*.wav")
    pair_fn = rules.get("pair_fn", lambda n: n)

    pairs: List[Tuple[Path, Path, float]] = []
    for foa in sorted(foa_root.glob(foa_glob)):
        bin_path = bin_root / pair_fn(foa.name)
        if not bin_path.exists():
            continue
        try:
            duration_s = sf.info(str(foa)).duration
        except Exception:
            continue
        if duration_s < duration + 4.0:
            continue  # too short to carry one comfortable excerpt
        pairs.append((foa, bin_path, duration_s))

    if not pairs:
        return []

    excerpts: List[dict] = []
    seen: set = set()  # (filename, start_s) dedup

    def _push(foa: Path, bin_path: Path, start_s: float) -> bool:
        key = (foa.name, round(start_s, 2))
        if key in seen:
            return False
        seen.add(key)
        excerpts.append({"foa": foa.name, "bin": bin_path.name,
                         "start_s": float(start_s)})
        return len(excerpts) >= target

    # Pass 1: centred excerpt.
    for foa, bin_path, file_dur in pairs:
        start = max(2.0, (file_dur - duration) / 2.0)
        if _push(foa, bin_path, start):
            return excerpts

    # Pass 2: extra excerpt near the start of each file.
    for foa, bin_path, file_dur in pairs:
        if file_dur < duration + 8.0:
            continue
        if _push(foa, bin_path, 5.0):
            return excerpts

    # Pass 3: extra excerpt three-quarters in.
    for foa, bin_path, file_dur in pairs:
        start = max(2.0, 0.75 * file_dur - duration / 2.0)
        if start + duration > file_dur - 2.0:
            continue
        if _push(foa, bin_path, start):
            return excerpts

    return excerpts


def _generate_dataset(
    ds_cfg: dict,
    duration: float,
    target: int,
    out_root: Path,
    eval_root: Path,
) -> List[dict]:
    """Render every excerpt of one dataset and return its catalogue entries."""
    foa_root = Path(ds_cfg.get("foa_root", ""))
    bin_root = Path(ds_cfg.get("bin_root", ""))
    excerpts = ds_cfg.get("excerpts")  # optional explicit override
    if excerpts is None:
        excerpts = _auto_discover(ds_cfg, duration, target)
    if not foa_root or not excerpts:
        print(f"[skip] {ds_cfg['id']}: no source recordings or no excerpts to render")
        return []

    print(f"  discovered {len(excerpts)} excerpts for {ds_cfg['id']}")

    crm, zhu, a2b = _build_renderers(eval_root, ds_cfg.get("a2b_checkpoint_id", "btpab"))
    if all(r is None for r in (crm, zhu, a2b)):
        print(f"[skip] {ds_cfg['id']}: no renderers available")
        return []

    # Wipe any stale clip directories from a previous run so that orphaned
    # clip IDs do not linger in the catalogue.
    ds_out = out_root / ds_cfg["id"]
    if ds_out.exists():
        import shutil
        shutil.rmtree(ds_out)

    clip_entries: List[dict] = []
    for idx, ex in enumerate(excerpts, start=1):
        foa_path = foa_root / ex["foa"]
        bin_path = bin_root / ex["bin"]
        if not foa_path.exists() or not bin_path.exists():
            print(f"  [skip] {foa_path.name} or {bin_path.name} missing")
            continue

        start_s = float(ex["start_s"])
        clip_id = f"{ds_cfg['id']}_{idx:03d}"
        print(f"  [{idx:02d}/{len(excerpts)}] {clip_id}  "
              f"{foa_path.name} @ {start_s:.1f}s", flush=True)

        foa, sr = _slice_foa_to_temp(foa_path, start_s, duration)
        renders = _render_with_renderers(foa, sr, crm, zhu, a2b)
        ref, _ = _read_bin_excerpt(bin_path, start_s, duration)

        clip_dir = out_root / ds_cfg["id"] / clip_id
        _save_wav(clip_dir / "reference.wav", ref, sr)
        renderings = {"reference": f"{ds_cfg['id']}/{clip_id}/reference.wav"}
        for name, audio in renders.items():
            # Make sure the rendered output matches the reference length so
            # the players line up visually.
            ref_len = ref.shape[-1]
            if audio.shape[-1] > ref_len:
                audio = audio[..., :ref_len]
            _save_wav(clip_dir / f"{name}.wav", audio, sr)
            renderings[name] = f"{ds_cfg['id']}/{clip_id}/{name}.wav"

        clip_entries.append({
            "id": clip_id,
            "source": ex["foa"],
            "start_s": start_s,
            "duration_s": duration,
            "renderings": renderings,
        })
    return clip_entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default=None,
                        help="Path to a YAML config file; defaults to built-in clips")
    parser.add_argument("--duration", type=float, default=30.0,
                        help="Excerpt duration in seconds (default 30)")
    parser.add_argument("--target", type=int, default=25,
                        help="Approximate number of excerpts per dataset (default 25)")
    parser.add_argument("--eval-root", default=str(_DEFAULT_EVAL),
                        help="Path to the foa2binaural-eval repository")
    parser.add_argument("--out", default=str(_REPO / "audio"),
                        help="Output audio directory (default 'audio')")
    parser.add_argument("--index", default=str(_REPO / "configs" / "audio_index.json"),
                        help="Where to write the audio index JSON")
    args = parser.parse_args()

    eval_root = Path(args.eval_root)
    _ensure_eval_on_path(eval_root)

    cfg = _load_config(args.config)
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    index = {"datasets": []}
    for ds in cfg.get("datasets", []):
        print(f"\n[ {ds['id']} ] {ds.get('label', ds['id'])}")
        clips = _generate_dataset(ds, args.duration, args.target, out_root, eval_root)
        index["datasets"].append({
            "id": ds["id"],
            "label": ds.get("label", ds["id"]),
            "description": ds.get("description", ""),
            "clips": clips,
        })

    index_path = Path(args.index)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("w", encoding="utf-8") as fp:
        json.dump(index, fp, indent=2)
    print(f"\n✓ Wrote audio index to {index_path}")
    print(f"  Total clips: {sum(len(d['clips']) for d in index['datasets'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
