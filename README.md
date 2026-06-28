# AES 2026 listening demo · FOA → Binaural

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC--BY--NC--4.0-blue.svg)](LICENSE)

Streamlit GUI for blind MOS rating of three FOA-to-binaural rendering systems.
Companion to:

> S. Zaporowski and B. Mroz, *Complex Ratio Mask Ambisonics-to-Binaural
> Rendering with Intensity Vector Features and Perceptual Multi-Objective
> Optimization*, AES 2026 International Conference on Audio for Virtual and
> Augmented Reality and Immersive Games, Paris.

For every clip the visitor listens to four versions:

* **Reference** — the ground-truth binaural recording from the dataset,
* **Proposed CRM**, **Zhu et al. 2022**, **A2B (Gebru et al. 2025)** — the
  three rendering systems compared in the paper.

The three systems are labelled **A**, **B**, **C** in a randomised order so
the rating is not biased by the model name; the GUI reveals the assignment
after the rating is recorded.

![GUI screenshot](docs/screenshots/screenshot.png)

---

## What is in the repository

```
avarig_2026_listening_demo/
├── app.py                       # Streamlit GUI
├── scripts/generate_audio.py    # Offline audio rendering
├── src/demo/
│   ├── catalog.py               # Reads configs/audio_index.json
│   ├── ratings.py               # CSV persistence for MOS ratings
│   └── style.py                 # Streamlit styling
├── configs/
│   └── audio_index.json         # Auto-generated catalogue
├── audio/                       # Generated WAVs (gitignored)
│   ├── zhu/<clip>/{reference,crm,zhu,a2b}.wav
│   ├── a2b_2mp/<clip>/...
│   └── argentum_pg/<clip>/...
├── ratings/                     # CSV files written by the GUI (gitignored)
├── docs/
├── LICENSE
├── requirements.txt
└── README.md
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

Python 3.10 or later. The PyTorch wheel only matters for
`scripts/generate_audio.py`; the GUI itself runs on Streamlit and
`soundfile` only.

## Quick start

```bash
# 1. (one time) render the demo clips with all three systems.
#    Requires the foa2binaural-eval repository to be reachable; set
#    FOA2BIN_EVAL when it does not sit as a sibling of this repo.
python scripts/generate_audio.py --duration 8

# 2. launch the GUI.
streamlit run app.py
```

The GUI opens in the default browser at `http://localhost:8501`. The
poster-session laptop should be in airplane mode for privacy; Streamlit
works entirely offline.

## Generating the audio

`scripts/generate_audio.py` selects a small set of representative FOA
excerpts from each source dataset, runs the three trained models on every
excerpt, and writes the resulting WAVs into `audio/<dataset>/<clip>/`.

The default clip catalogue covers:

| Dataset | Source | Sampling rate |
|---|---|---|
| `zhu` | Zhu (ByteDance) test set | 48 kHz |
| `a2b_2mp` | Meta A2B 2-MP test set | 44.1 kHz |
| `argentum_pg` | Argentum HOA corpus (concert hall recordings) | 48 kHz |
| `echo_project` | Placeholder; add files when available | — |

To change the catalogue, copy `DEFAULT_CLIPS` from
`scripts/generate_audio.py` into `configs/clips.yaml`, edit the file paths
and excerpt offsets, then run

```bash
python scripts/generate_audio.py --config configs/clips.yaml --duration 8
```

Environment variables override the checkpoint paths:

```bash
export CRM_CHECKPOINT=/path/to/binaural_rendering_popr7_Zhu_PG.pt
export ZHU_CHECKPOINT=/path/to/binaural_rendering_100.pt
export FOA2BIN_EVAL=/path/to/foa2binaural-eval
```

## Adding Echo Project (or any other source)

Once you have a paired FOA / binaural recording from Echo Project locally:

1. Copy the WAVs to a directory of your choice.
2. Open `scripts/generate_audio.py`, locate the `echo_project` entry in
   `DEFAULT_CLIPS`, set `foa_root`, `bin_root` and add at least one
   `files` entry with a list of `excerpts`.
3. Rerun `python scripts/generate_audio.py`.
4. Refresh the GUI (press `R` in Streamlit).

The dataset block in the sidebar appears automatically once it contains
at least one clip with a rendered reference.

## Using the GUI

* Type your initials in the sidebar; ratings are autosaved to
  `ratings/ratings_<initials>.csv`. Each row records `dataset`, `clip_id`,
  `system` (true system name, not the blind label), `mos`, and an
  optional comment.
* The session identifier in the sidebar groups ratings made during one
  sitting (useful when several visitors share a laptop).
* `Reveal which system is which` shows the mapping between **A / B / C**
  and the underlying systems. Use it after rating, not before.
* `Download my ratings as CSV` exports the current CSV from disk.

The reference player can be hidden if you prefer a fully blind protocol
without the ground truth.

## MOS scale

The scale follows ITU-R BS.1116 / P.800:

| Score | Verdict |
|---|---|
| 5 | Excellent — imperceptible difference |
| 4 | Good — perceptible but not annoying |
| 3 | Fair — slightly annoying |
| 2 | Poor — annoying |
| 1 | Bad — very annoying |

We ask raters to consider both **timbral fidelity** and **spatial accuracy**
(localisation, externalisation, width) in a single score.

## Privacy and data handling

* Ratings stay on the local laptop. There is no network call from the GUI.
* The CSV file is keyed by rater initials; visitors can refuse to enter a
  name and the GUI then shows a reminder.
* Source audio recordings carry the licenses of their original datasets
  (CC BY-NC-SA for Argentum HOA, Zhu's own license, Meta A2B terms).
  Treat the generated WAVs accordingly.

## Citing this work

```bibtex
@inproceedings{zaporowski2026crm,
    author    = {Zaporowski, Szymon and Mr\'oz, Bart\l{}omiej},
    title     = {Complex Ratio Mask Ambisonics-to-Binaural Rendering with
                 Intensity Vector Features and Perceptual Multi-Objective Optimization},
    booktitle = {AES 2026 International Conference on Audio for Virtual and
                 Augmented Reality and Immersive Games},
    address   = {Paris, France},
    year      = {2026},
    month     = jun
}
```

## License

Code: Creative Commons Attribution NonCommercial 4.0 International. See
[LICENSE](LICENSE). Audio licenses follow the source datasets.

## Acknowledgements

Supported by the Polish national research budget under the Excellence
Initiative – Research University grant number 20/1/2023/IDUB/I3b/Ag.
