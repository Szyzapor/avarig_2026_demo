# Listening test v2 (webMUSHRA), revision 2

> **Superseded for stimuli by version 3** (`avarig_2026_listening_test_v3.zip`): consistent
> baseline alignment on Argentum, loudness measured with ffmpeg ebur128, `zhu2022` retrained so that
> it no longer loses the band above 7 kHz, no mid anchor, and a practice clip from a recording outside
> the test. See the root README, section "Online MUSHRA test", for the details and for the known
> system differences to report.

A MUSHRA follow-up to the AES 2026 (AVARIG) poster demo. It compares the
retrained **Proposed CRM** with the Zhu et al. 2022 and A2B (Gebru et al. 2025)
baselines on the same excerpts, in two sessions:

| Session | Config | Pages | Time |
|---|---|---|---|
| 1 | `session1_overall.yaml` | 2 training + 12 trials + 2 repeated trials, overall quality | about 25-30 min |
| 2 | `session2_attributes.yaml` | 1 training + 4 SAQI attributes x 6 trials | about 35 min |

Revision 2 answers the review in issue #3. What changed and why is listed in
[Changes after review](#changes-after-review-issue-3).

## Stimuli

Every page has the reference and six conditions:

| Condition | What it is |
|---|---|
| `reference` | hidden reference (identical to the reference) |
| `proposed_crm_v2` | retrained proposed model (`popr9_mirror_rot_level`): corrected training data, per-file time/polarity alignment, unified FOA conventions, loss penalising polarity and level errors |
| `zhu2022` | Zhu et al. 2022 re-implementation |
| `a2b_btpab` | A2B (Gebru et al. 2025), `btpab` checkpoint. It was trained on the Zhu dataset, so it is in-domain on the Zhu trials |
| `anchor_lp3500` | reference low-passed at 3.5 kHz (BS.1534-3 low anchor) |
| `anchor_foa_cardioid` | FOA rendered with two virtual cardioids at ±90°, no HRTF |

Trials (10 s each, 48 kHz, 24-bit):

* 6 x Zhu (ByteDance) test set: `zhu_001`-`004` (discussed at AVARIG), `zhu_005`, `zhu_006`.
* 6 x Argentum hold-out (recordings the proposed model never saw in
  training): `argentum_pg_003` (choir), `005` and `015` (Laudate Dominum),
  `019` (outdoor), `021` (concert), `024` (piano).
* Training pages: `zhu_009` and `argentum_pg_013`. These clips are not used
  in the test.
* Repeated in session 1: `zhu_002` and `argentum_pg_003`.
* Session 2 uses `zhu_001`, `003`, `005` and `argentum_pg_003`, `005`, `021`.

Processing:

* **Level:** every file is at -23.0 LUFS (ITU-R BS.1770). If any condition of
  a trial would peak above -1 dBFS, the whole trial is lowered by the same
  amount (`trial_gain_db` in the manifest). No trial needed that here, so all
  files are at -23.0 LUFS with peaks at or below -2.9 dBFS.
* **Time and polarity:** each condition is aligned to the reference on the
  full 30 s demo clip, and the 10 s excerpt is cut afterwards. The models use
  band-passed (100-4000 Hz) cross-correlation. The FOA anchor uses the measured
  FOA-to-binaural lag and polarity of the recording (`alignment_ref.py` table),
  because its correlation with the binaural reference is too weak for a
  reliable cross-correlation peak. On Argentum the anchor then matches the
  reference to within 0.1 ms; on Zhu the 1-4 kHz band peaks at 0 ms, while
  below 1 kHz the cardioid pair and the head recording differ in phase, so no
  single delay fits all bands. `manifest.json` records lag, polarity,
  correlation, method, gain, final loudness and peak for every file.
* **Bit depth:** the baselines are rendered in 32-bit float from the FOA source
  with 2 s of context on each side, then written as 24-bit PCM like everything
  else.
* **File names** are opaque hashes (`audio/<16 hex>.wav`), and page titles show
  only the criterion. The stimulus keys in the config (and therefore in the
  results) are the condition names above. `manifest.json` maps files to
  trials.

## Running with webMUSHRA

1. Get webMUSHRA (https://github.com/audiolabs/webMUSHRA) and serve it **with
   PHP**. Results are written by `service/write.php` to
   `results/foa2bin_v2_session1/mushra.csv` and
   `results/foa2bin_v2_session2/mushra.csv`.
2. Unzip `avarig_2026_listening_test_v2_rev2.zip` and copy the
   `listening_test_v2/` folder to `webMUSHRA/configs/listening_test_v2/`. The
   stimulus paths in the configs are `configs/listening_test_v2/audio/...`.
3. Send participants two links:
   `http://<host>/?config=listening_test_v2/session1_overall.yaml` and then
   `http://<host>/?config=listening_test_v2/session2_attributes.yaml`.

Instructions and attribute definitions are in Polish and English on the intro
page and on every rating page. The attribute wording paraphrases SAQI
(Lindau et al. 2014) and the BS.1534-3 instructions. Each finish page asks for
a self-chosen **participant code** (the same in both sessions, so the two CSV
files can be joined). Session 1 also asks for age range, hearing, music,
audio and spatial-audio experience, previous listening tests, headphone type
and model, listening environment, and browser/computer. Session 2 asks again
for code, headphones and environment.

### Limits of stock webMUSHRA

The configs run on unmodified webMUSHRA, which has a few limits:

* **No PHP means no data.** Every finish page now sets `showErrors: true`, so
  the participant sees the error and is told to keep the page open. Saving a
  JSON copy in the browser needs a webMUSHRA code change.
* **Sample rate.** webMUSHRA stops if the audio device does not run at the
  stimulus rate (48 kHz). The intro asks participants to set 48 kHz. All
  trials are 48 kHz now, because the 44.1 kHz a2b_2mp trials are gone.
* **"Next" is never locked and every slider starts at 100.** This is handled
  by the screening rule below. Enforcing it in the page needs a code change.
* **Browser and sample rate** are not recorded automatically. The
  questionnaire asks for browser and computer instead.

The reviewer's hosted copy already has the code-side changes: generated
participant ID, JSON fallback without PHP, "Overall · 3 / 12" titles, and a
layout that fits a 1080p window. Merging them with these configs is the
natural next step.

## Screening and analysis (fixed before data collection)

`analyze_results.py` applies these rules and prints mean ± 95% CI per
condition, criterion and dataset:

1. Training pages are not analysed.
2. A page is invalid if all six sliders are still at 100, all six ratings are
   equal, or the listener spent less than 20 s on it (twice the stimulus
   length).
3. A listener is excluded if they rate the hidden reference below 90 on more
   than 15% of their valid test pages (ITU-R BS.1534-3, §4.1.2).
4. The two repeated pages measure reliability: the mean absolute difference to
   the first rating (five conditions, without the hidden reference). Listeners
   above 20 points are flagged and reported, not dropped automatically.
   Repeats are not part of the means.

```bash
python analyze_results.py results/foa2bin_v2_session1/mushra.csv \
                          results/foa2bin_v2_session2/mushra.csv
```

For reporting (BS.1534-3 §10.2), the questionnaire covers listener
experience, hearing and reproduction equipment. Number and selection of
assessors and the screening outcome come from the script output.

## Changes after review (issue #3)

| Review point | Change |
|---|---|
| `anchor_lp3500` is almost the reference on dark clips (HF above 3.5 kHz at -43/-39/-30 dB on argentum_pg_002/008/001) | Argentum clips are now chosen so that reference energy above 3.5 kHz is at least -31 dB of total (range -31 to -24 dB; Zhu -26 to -16 dB). Most of the hold-out corpus (piano recital, Sopot pier, Respighi, Ravel) is below -40 dB and was dropped for this reason. |
| a2b_2mp: FOA anchor 10-15 dB to the left, baseline ILD does not follow the reference | Confirmed, and the cause is the input. The a2b_2mp FOA is not consistent B-format: no channel permutation, W gain or yaw rotation gives an ILD that follows the reference on all clips (best mean r = 0.37 over 8 clips; per-clip best conventions disagree). The proposed model saw a2b_2mp in training and learned its mapping; the baselines and the FOA anchor assume ACN/SN3D. **The a2b_2mp trials are removed** and replaced by two more Zhu and two more Argentum trials. |
| Coarse quantisation on the baselines (~11 effective bits) | Cause: the baseline renderer wrote 16-bit PCM, which was then raised to -23 LUFS. The baselines are now rendered in float and written at 24 bit; all files use the full 24-bit grid. |
| `anchor_foa_cardioid` not time-aligned (+18.6 ms on argentum_pg_003, ~2.7 ms on others, 3-4 ms on Zhu) | The anchor is now shifted by the measured FOA-to-binaural lag and polarity of each recording, the same relation the model renders are aligned to (Argentum: +137 or -887 samples; Zhu: about -87 samples with inverted polarity). |
| README claims lag/polarity in `manifest.json` | They are there now, per file, with the method used. |
| "Every stimulus is normalised to -23 LUFS" vs -26.7/-25.4 dB where the peak limit binds | Wording fixed (see Processing). In this revision no trial hits the limit. |
| Intro does not say the criterion changes and clips are rated several times | Session 2 intro says it explicitly; the criterion is in every page title and above the sliders. |
| Results need PHP, participant not told on failure | `showErrors: true` on the finish pages; the instruction tells the participant to keep the page open. See limits above. |
| Next never locked, sliders start at 100 | Screening rule 2, fixed before data collection, plus "move every slider" on each page. |
| File names and page titles reveal systems and datasets | Opaque file names in a flat `audio/` folder, titles show only the criterion. |
| 60 pages, 75-110 min | Two sessions of about 30 and 35 minutes. |
| No training phase (BS.1534-3 Att. 1) | Training pages at the start of each session, excluded from analysis. |
| No replicated ratings (§4.1) | Two repeated trials in session 1, reported as reliability. |
| Post-screening rule (§4.1.2) | Implemented in `analyze_results.py` (rule 3). |
| Questionnaire too thin for §8/§10.2 | Extended questionnaire (see above). |

## Provenance

Built by `code/build_listening_test_v2r.py` in the research working copy
(`Argentum_popr9`) from demo audio package v2 (`avarig_2026_demo_audio`) and
the FOA sources:

```
PYTHONPATH=code .venv/bin/python code/build_listening_test_v2r.py --out listening_test_v2r
```
