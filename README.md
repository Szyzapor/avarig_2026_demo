# AES 2026 listening demo · FOA → Binaural

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC--BY--NC--4.0-blue.svg)](LICENSE)

Streamlit GUI for blind MOS rating of three FOA-to-binaural rendering systems.
Companion to:

> S. Zaporowski and B. Mroz, *Complex Ratio Mask Ambisonics-to-Binaural
> Rendering with Intensity Vector Features and Perceptual Multi-Objective
> Optimization*, AES 2026 International Conference on Audio for Virtual and
> Augmented Reality and Immersive Games, Paris.

For every clip the visitor listens to four versions:

* **Reference** - the ground-truth binaural recording from the dataset,
* **Proposed CRM**, **Zhu et al. 2022**, **A2B (Gebru et al. 2025)** - the
  three rendering systems compared in the paper.

The three systems are labelled **A**, **B**, **C** in a randomised order so
the rating is not biased by the model name; the GUI reveals the assignment
after the rating is recorded.

![GUI screenshot](docs/screenshots/screenshot.png)

---

## Online listening test (GitHub Pages)

`web/` holds a static version of the test that runs on GitHub Pages with no
server. Each participant:

1. agrees to take part (anonymous; 18+),
2. fills in a short questionnaire: age range, gender (optional), playback
   device and headphone model, noise cancelling, listening environment,
   hearing impairment, music experience, audio-engineering experience,
   familiarity with spatial audio, earlier listening tests,
3. sets the volume and passes a left/right headphone check,
4. rates `clipsPerDataset` random clips from each dataset (default 5 x 2 = 10
   trials, about 15 minutes). Every trial has the reference and three blind
   versions A/B/C in a fresh random order, played on the same gapless
   shared-timeline player as the Streamlit GUI. A version can be rated only
   after it has been played for `minListenSeconds`,
5. can leave a final comment.

Answers go to a Google Sheet through a Google Apps Script web app, one event
per step, so a participant who quits half-way still leaves their finished
trials. Progress is kept in `localStorage`, so reloading the page resumes the
session. Without an endpoint, or if sending fails, the last page offers a
JSON download instead.

### Build the audio

```bash
DEMO_AUDIO_ROOT=~/avarig_demo_audio python scripts/build_web.py \
    --datasets zhu argentum_pg --clips-per-dataset 15
```

This writes `web/audio/**.flac` (24-bit) and `web/manifest.json` (about
234 MB for 15 clips x 2 datasets x 12 s). ffmpeg is the only dependency.

`a2b_2mp` is left out on purpose. Its FOA is not consistent B-format, while
the Zhu and A2B baselines expect ACN/SN3D input, so the comparison on that
set is unfair to them. The formal listening test makes the same choice. The
script:

* crops seconds 9-21 of each 30 s demo clip,
* gain-matches every version to -23 LUFS (EBU R128), with one shared
  correction per clip if needed to keep the true peak below -1 dBTP.
  Without this the systems differed by up to 20 dB, which biases the ratings,
* leaves polarity alone: the v2 audio package is already time- and
  polarity-aligned to the reference (`--fix-crm-polarity` inverts CRM, which
  is only needed for the old v1 package),
* skips excerpts whose reference is quieter than -45 LUFS,
* gives the files hashed names so the system is not visible in the URL.

Applied gains are logged to `configs/web_levels.json`. Use `--datasets` to
leave a dataset out.

### Set up response collection

1. Create a Google Sheet, then open **Extensions > Apps Script**.
2. Paste in [`apps_script/Code.gs`](apps_script/Code.gs) and save.
3. **Deploy > New deployment > Web app**, set *Execute as: Me* and *Who has
   access: Anyone*, then copy the `/exec` URL.
4. Put the URL into `web/config.js` as `endpoint`.

The script creates three sheets: `participants` (one row per person),
`ratings` (one row per person x clip x system, including the true system, the
blind label and listening time per version) and `sessions` (final comment and
total time). Survey answers are stored as language-independent codes (for
example `dev_over_open` or `mus_hobby`). Their wording is in `web/i18n.js`.

### Publish

In the GitHub repository, set **Settings > Pages > Source** to
**GitHub Actions**. The workflow `.github/workflows/pages.yml` deploys `web/`
on every push to `main` that touches it. To test locally:

```bash
python -m http.server -d web 8000   # open http://localhost:8000
```

### Analyse

Download the `ratings` and `participants` sheets as CSV, then run:

```bash
python scripts/analyze_web_ratings.py ratings.csv participants.csv
```

The script prints MOS ± 95% CI per system, per dataset and per questionnaire
group. Participants who failed the L/R check or listened on loudspeakers are
left out (`--all` keeps them).

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
│   └── audio_index.json         # Catalogue; paths are relative to audio root
├── audio/                       # Local fallback for the audio root (gitignored)
│   └── (place WAVs here, or set DEMO_AUDIO_ROOT to point elsewhere)
# audio root contents (downloaded separately or regenerated by the script):
#   <audio_root>/zhu/<clip>/{reference,crm,zhu,a2b}.wav
#   <audio_root>/a2b_2mp/<clip>/...
#   <audio_root>/argentum_pg/<clip>/...
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

The audio files (about 2.3 GB compressed, 300 WAVs total) are distributed
separately because they are too large for a Git repository. Two options:

The current audio package is **v2.1** (2026-10-05):

* `crm` is the retrained model `popr9_mirror_rot_level` (corrected training
  data); `zhu` and `a2b` use the same checkpoints as before,
* `zhu/` and `a2b_2mp/` use the same 25 + 25 excerpts as v1,
* `argentum_pg/` has 25 new excerpts taken only from hold-out recordings that
  the proposed model never saw in training (v1 used training recordings),
* every version is time- and polarity-aligned to the reference and
  loudness-matched to -23 LUFS (BS.1770) with a shared -1 dBFS peak limit,
* v2.1: `zhu` and `a2b` are re-rendered in 32-bit float. In v2 they were
  16-bit and, once raised to -23 LUFS, carried a coarse quantisation grid
  that only the baselines had. The `a2b_2mp` references are re-read from the
  float source files. All files are 24-bit. Zhu source recordings are 16-bit,
  so their references keep that grid (quantisation floor about -109 dBFS).
* on `a2b_2mp` the baseline renderings get a non-standard FOA input (see
  above), so treat them as indicative only.

`configs/audio_index.json` in this repository matches v2.1 (same clips as
v2). v2 is built by `code/build_demo_package.py` and v2.1 by
`code/rerender_demo_baselines.py` in the popr_9 working copy, and
`code/verify_demo_package.py` checks the result, not by
`scripts/generate_audio.py` (that script still renders the v1 setup).

### Option A: download the pre-generated audio package

1. Get the audio archive (SharePoint link distributed by the authors).
2. Extract it anywhere on disk, for example to `~/avarig_demo_audio`.
3. Point the GUI at it via the `DEMO_AUDIO_ROOT` environment variable:

```bash
DEMO_AUDIO_ROOT=~/avarig_demo_audio streamlit run app.py
```

### Option B: regenerate the audio locally

Requires the trained checkpoints and the `foa2binaural-eval` repository
(set `FOA2BIN_EVAL` when it does not sit as a sibling of this repo).

```bash
# Defaults to 25 clips per dataset at 30 seconds each (~75 clips total).
python scripts/generate_audio.py --duration 30 --target 25

# The script writes into ./audio/ next to the script; the GUI looks there
# by default so no DEMO_AUDIO_ROOT is needed in this case.
streamlit run app.py
```

The GUI opens in the default browser at `http://localhost:8501`. The
poster-session laptop should be in airplane mode for privacy; Streamlit
works entirely offline.

## Generating the audio

`scripts/generate_audio.py` auto-discovers paired FOA / binaural files in
each source dataset, picks up to `--target` excerpts of `--duration`
seconds each (defaults: 25 excerpts at 30 s, so ~75 clips total across the
three datasets), runs the three trained models on every excerpt, and
writes the resulting WAVs into `audio/<dataset>/<clip>/`.

The default clip catalogue covers:

| Dataset | Source | Sampling rate | Pairing rule |
|---|---|---|---|
| `zhu` | Zhu (ByteDance) test set | 48 kHz | `AmbiX-*.wav` ↔ `Binaural-*.wav` |
| `a2b_2mp` | Meta A2B 2-MP test set | 44.1 kHz | `*_ambisonics.wav` ↔ `*_binaural.wav` |
| `argentum_pg` | Argentum HOA corpus (v2: hold-out recordings only) | 48 kHz | `FOA_*.wav` ↔ `BIN_*.wav` |
| `echo_project` | Placeholder; add files when available | - | - |

Auto-discovery picks one centred excerpt per source file first, then loops
back to add a second excerpt near the start and a third around the 3/4
mark until the target is reached or every file has been visited three
times. Re-running the script with the same source directory yields the
same clip ordering.

To override the source paths, copy `DEFAULT_CLIPS` from
`scripts/generate_audio.py` into `configs/clips.yaml`, edit the roots,
then run

```bash
python scripts/generate_audio.py --config configs/clips.yaml \
    --duration 30 --target 25
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

## Using the GUI (collecting ratings)

* Type your name or initials at the top and fill in **About you** (age range,
  hearing, headphones, environment, music / audio / spatial-audio experience,
  previous listening tests). Ratings are saved only once both are done.
* Ratings autosave to `ratings/ratings_<YYYY-MM-DD--HHMM>_<name>.csv`. Each row
  records `dataset`, `clip_id`, `system` (true name), `blind_label`, `mos`,
  the optional comment and `audio_version` (the audio package the clip was
  played from, read from the package README). The profile goes to
  `ratings/participants_<...>_<name>.csv`, keyed by session.
* Only `zhu` and `argentum_pg` are offered for rating. `a2b_2mp` is left out
  because its FOA is not standard B-format for the baselines. For a demo-only
  run use `DEMO_DATASETS=zhu,a2b_2mp,argentum_pg streamlit run app.py`.
* **Reveal system names** shows the A / B / C mapping and locks the sliders
  while it is on, so a revealed name never reaches a stored score.
* The session identifier groups ratings made in one sitting (useful when
  several visitors share a laptop). Re-rating overwrites the earlier score.
* `Download my ratings as CSV` exports the current CSV from disk.

Analyse the collected files with:

```bash
python scripts/analyze_demo_ratings.py ratings/
```

It uses only ratings made on audio package v2.1 and the two rated datasets,
drops sessions without a complete profile or with identical ratings
throughout, and prints MOS ± 95% CI per system (overall, per dataset, per
profile group) plus paired CRM - baseline differences. Ratings collected
before this version (no `audio_version` column) were made on other audio
and are reported separately, not pooled.

The reference player can be hidden if you prefer a fully blind protocol
without the ground truth.

## MOS scale

The scale follows ITU-R BS.1116 / P.800:

| Score | Verdict |
|---|---|
| 5 | Excellent - imperceptible difference |
| 4 | Good - perceptible but not annoying |
| 3 | Fair - slightly annoying |
| 2 | Poor - annoying |
| 1 | Bad - very annoying |

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
