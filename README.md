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

## Online MUSHRA test (GitHub Pages)

`web/` is the listening test used for the paper results: a MUSHRA test
(ITU-R BS.1534-3 style) that runs as a static site on GitHub Pages, at
https://szyzapor.github.io/avarig_2026_demo/. The earlier online MOS test
(5-point scale, no hidden reference or anchors) is kept on branch
`online-mos-v2.2` (audio package v2.2; `online-mos-v2.1` keeps the earlier audio).

**Stimuli** (version 3.1, `listening_test_v2/ARGENTUM_RECORDINGS.md` lists the
Argentum recordings by role):

* 12 trials of 10 s: 6 Zhu, 6 Argentum hold-out. a2b_2mp is left out because
  its FOA is not consistent B-format.
* 6 conditions per trial: hidden reference, `proposed_crm_v2`, `zhu2022`,
  `a2b_btpab`, `anchor_lp3500` (low anchor) and `anchor_foa_cardioid`.
  There is no mid anchor: a 7 kHz low-pass would sound like the reference on
  8 of the 12 clips.
* `zhu2022` is our re-implementation retrained in version 3
  (`Zhu/train_hfmask.py`, checkpoint `binaural_rendering_100_hfmask.pt`).
  The original version was 8-23 dB too quiet above 7 kHz. Its output
  magnitude is sigmoid(mask) x |W|, so it could not exceed the omni channel,
  but in the Zhu training data the binaural is louder than W in 34% of the
  time-frequency bins at 7-10 kHz and in about half above 10 kHz. Its loss
  (L1 on the waveform and on the complex spectrum, equation 7 of the paper)
  also averages the poorly predictable high band towards zero. The retrained
  model allows a mask up to 4 (+12 dB over |W|) and adds a multi-resolution
  log-magnitude loss (weight 1). Data, architecture and the other
  hyperparameters are unchanged. A variant with weight 0.1 was also trained,
  and the choice was made on the 9 Zhu test files that are not in the
  listening test:

  | Model | Level vs reference at 7 / 10-16 kHz | Waveform corr. | ILD r |
  |---|---|---|---|
  | original | -13.7 / -20.6 dB | 0.936 | 0.64 |
  | retrained, weight 1 (used) | +0.9 / -0.9 dB | 0.904 | 0.69 |
  | retrained, weight 0.1 | -4.6 / -6.1 dB | 0.939 | 0.64 |

  On the 6 Zhu test clips the used model is within ±1.2 dB of the reference
  above 2 kHz. Measured per band on the 25 + 25 demo clips (`verify` set),
  ILD agreement with the reference moves as follows:

  | ILD band | Zhu clips, original -> retrained | Argentum clips, original -> retrained |
  |---|---|---|
  | 200-1000 Hz | 0.77 -> 0.59 | 0.56 -> 0.38 |
  | 1-4 kHz | 0.68 -> 0.67 | 0.31 -> 0.46 |
  | 4-10 kHz | 0.76 -> 0.85 | 0.20 -> 0.48 |

  So the retrained model follows the reference better above 1 kHz and worse
  below 1 kHz, where ILD is small and localisation rests mainly on ITD.
  Report it as a re-implementation with these two changes, including this
  trade-off. Files are 48 kHz /
  24-bit, served as lossless FLAC. The Zhu reference and anchors derive from
  16-bit source recordings.
* Loudness: every file is at -23.0 LUFS as measured by ffmpeg `ebur128` (the
  BS.1770 reference implementation), at most 0.1 dB apart on a page. Revision 2
  used an internal meter that differed from it by up to 0.5 dB.
* Time and polarity: `proposed_crm_v2` is aligned by cross-correlation on the
  30 s clip, and the FOA anchor by the measured FOA-to-binaural lag of the
  recording.
* Baselines on Argentum: the cross-correlation with the reference has two
  near-equal peaks about 45 samples apart, with opposite signs, and picked
  either one per clip. Version 3 instead transfers each baseline's intrinsic
  delay and polarity, measured on the Zhu clips: -84/-85 samples with
  inverted polarity for both models on all 6 clips. Combined with the FOA-to-binaural
  table, this gives one consistent shift per recording (+802 or -222 samples,
  inverted). Baselines on Zhu are aligned by cross-correlation, which is
  unambiguous there.
* Practice clips `zhu_009` and `argentum_pg_006`. The Argentum practice clip
  comes from a recording that is not in the test.

**Known differences between systems.** These are measured, not fixable by
re-rendering, and should be reported with the results:

* Argentum is in-domain for the proposed model only. Its binaural references
  are rendered from the same ZM-1 recordings: the multiple coherence between
  FOA and binaural is 1.00 up to 500 Hz, against 0.65-0.88 for the Zhu
  dummy-head recordings. The proposed model was trained on 40 other
  recordings from this chain. The baselines were trained on Zhu only.
  Report Argentum separately, as the proposed model's training domain, and
  treat Zhu as the fair comparison. On Zhu all three systems were trained on
  Zhu train, and A2B (`btpab`) is in-domain there.
* A2B does not follow source direction on Argentum. Its ILD (1-4 kHz) does
  not track the reference (r about 0, against 0.64-0.93 on Zhu). This is not
  an input-convention error: none of the 24 permutations and sign changes of
  the directional channels, N3D scaling, or an EQ to the Zhu microphone's
  directional profile gives r above 0.14, and on Zhu the convention in use is
  the best. The ZM-1 FOA has strongly reduced directional channels below
  500 Hz (Y+Z+X at 0.06-0.35 x W at 63-250 Hz, against 0.8-1.7 x W for the
  Zhu microphone), a microphone mismatch the Zhu-trained models do not
  generalise over. Zhu2022 follows direction partly (r 0.2-0.55).
* Both baselines add +5 to +10 dB around 63 Hz on Argentum, most likely
  learned from the low-frequency wind and handling noise in the Zhu binaural
  targets.
* The FOA anchor is closer to the reference than both baselines on Argentum,
  so it is a condition there, not an anchor. It is never used for screening.

**Sessions** (same page, `?session=1` or `?session=2`):

| Session | Pages | Time | Role |
|---|---|---|---|
| 1 | 2 practice + 12 trials (random order) + 2 repeats in a separate final block, overall quality | about 25-30 min | primary result |
| 2 | 1 practice + 4 attribute blocks x 6 trials (block order from a balanced Latin square per participant) + 1 repeat in a later block | about 35 min | exploratory |

Each session runs: information and consent (contact address from
`config.js`), then a questionnaire. Session 1 asks for age range, hearing,
headphones and model, environment, and music, audio and spatial-audio
experience; session 2 only asks for headphones, model and environment.
**Bluetooth headphones and loudspeakers are screened out** before the test.
Then come the volume setting, the left/right check (must pass, or two failed
rounds are recorded), instructions, practice and the rating pages.

On every rating page the reference and six numbered versions (new random
order per page) play on one gapless shared timeline (keys 0-7, Space). Each
slider starts unrated and unlocks after its version has been heard for 2 s.
**Next unlocks only when every version has been heard and every slider set.**
The page title shows only the criterion and progress (`?debug=1` adds the
trial id).

**Participants** get a code from the URL (`?pid=...`, use per-person links)
or a generated 8-character one that is written into the URL, so a reload
resumes the session. The final page shows the code and the session 2 link
with the same code, and always offers the results as a JSON download.

### Results collection

Results go page by page to a Google Apps Script web app that writes a
Google Sheet (`apps_script/Code.gs`, sheets `participants`, `mushra` with one
row per condition, and `sessions`, de-duplicated by event id):

1. Create a Google Sheet, then open **Extensions > Apps Script**, paste
   `Code.gs` and save.
2. **Deploy > New deployment > Web app**, set *Execute as: Me* and *Who has
   access: Anyone*.
3. Put the `/exec` URL into `web/config.js` (`endpoint`) together with
   `contactEmail`, then push to `main`. The Pages workflow redeploys.

Until `endpoint` is set nothing is collected centrally; participants can
only download their JSON.

### Analysis (fixed before data collection)

```bash
python scripts/analyze_mushra.py --mushra mushra.csv --participants participants.csv \
    [--json downloads/*.json]
```

* Listeners are excluded if they failed the L/R check, or rated the hidden
  reference below 90 on more than 15% of test pages and on at least 2 pages
  (BS.1534-3 §4.1.2). The mid-anchor rule is not applied, because there is
  no mid anchor, and the FOA anchor is never used for screening.
* Repeats give a reliability measure: mean |difference| to the original,
  flagged above 20 points. Practice pages are never analysed.
* Primary: per-listener means per dataset, mean ± 95% CI across listeners,
  and paired Wilcoxon signed-rank tests of CRM against each baseline within
  each dataset (4 tests, Holm correction). Session 2 uses the same method per
  attribute and is reported as exploratory.
* Ceiling check: the share of system ratings at or above 80.

### Rebuilding the stimuli

```bash
# in the research working copy (Argentum_popr9)
PYTHONPATH=code .venv/bin/python code/build_listening_test_v2r.py --out listening_test_v3_1 \
    --training zhu=zhu_009,argentum_pg=argentum_pg_006 \
    --baseline-alignment model-offset --loudness ffmpeg \
    --raw-cache listening_test_v3_raw \
    --zhu-checkpoint /home/smck/Argentum/Zhu/models/binaural_rendering_100_hfmask.pt \
    --demo-root /home/smck/Argentum/avarig_2026_demo_audio_v2_1 --webmushra-style v3.1
# here
python scripts/build_mushra_web.py <path>/listening_test_v3_1
```

### Before launch

* Set `endpoint` and `contactEmail` in `web/config.js`.
* Run a 3-5 listener pilot. Check session time, score spread, whether the
  low anchor is clearly audible, and the
  `audio_sample_rate` logged per participant (the player resamples, so 44.1
  kHz devices work, but it is worth knowing).
* Limits to report: an online, unsupervised, mixed panel deviates from
  BS.1534-3 §4.1/§8. Aim for about 20 listeners after screening. The six Zhu
  clips are consecutive files of one session and the Argentum clips come
  from 5 recordings, so report results per dataset. A2B is in-domain on Zhu.

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

The current audio package is **v2.2** (2026-10-09):

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
* v2.2: `zhu` is re-rendered with the retrained re-implementation (see
  "Online MUSHRA test"), and loudness is measured with ffmpeg ebur128 (all
  versions of a clip within 0.1 dB),
* on `a2b_2mp` the baseline renderings get a non-standard FOA input (see
  above), so treat them as indicative only.

`configs/audio_index.json` in this repository matches v2.2 (same clips as
v2). v2 is built by `code/build_demo_package.py` and v2.1/v2.2 by
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

## Using the GUI (poster demo)

Paper results come from the online MUSHRA test above, not from this GUI.


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

It uses only ratings made on audio package v2.2 and the two rated datasets,
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
