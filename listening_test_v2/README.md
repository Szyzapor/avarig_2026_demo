# Listening test v2 (webMUSHRA), stimuli version 3.1

MUSHRA test (ITU-R BS.1534-3 style) comparing the retrained **Proposed CRM** with the Zhu et al.
2022 re-implementation and A2B (Gebru et al. 2025). The audio (84 WAV files) is distributed as
`avarig_2026_listening_test_v3_1.zip`; this folder holds the configs, the manifest and the analysis.
The same stimuli run on the GitHub Pages version (`web/`, see the root README).

## Contents

| File | Purpose |
|---|---|
| `session1_overall.yaml` | session 1: 2 practice pages, 12 trials (random order), then 2 repeated trials in their own random block; overall quality. Primary result. About 25-30 min. |
| `session2_attributes_{A,B,C,D}.yaml` | session 2: 1 practice page, 4 SAQI attribute blocks of 6 trials. Each file is one row of a balanced Latin square of the attribute order, and each has one repeated page (a block-1 page placed in block 3). Assign the files to participants in rotation. Exploratory. About 35 min. |
| `manifest.json` | per file: trial, condition, alignment method, lag, polarity, correlation with the reference, gain, final loudness (ffmpeg ebur128), true peak, source bit depth; per trial: the zhu2022 checkpoint used |
| `analyze_results.py` | screening and analysis, fixed in advance (see its docstring) |
| `ARGENTUM_RECORDINGS.md` | Argentum recordings by role: training, validation, hold-out |

## Stimuli

* **Trials:** 12 trials of 10 s, 48 kHz / 24-bit:
  * 6 Zhu: `zhu_001`-`006`,
  * 6 Argentum hold-out: `argentum_pg_003`, `005`, `015`, `019`, `021`, `024`.

  Practice clips are `zhu_009` and `argentum_pg_006`; the Argentum practice clip comes from a
  recording that is not in the test.
* **Conditions:** hidden reference, `proposed_crm_v2`, `zhu2022` (retrained, see below),
  `a2b_btpab`, `anchor_lp3500`, `anchor_foa_cardioid`. There is no mid anchor.
* **Loudness:** -23.0 LUFS as measured by ffmpeg ebur128, at most 0.1 dB apart on a page.
* **Alignment:** `proposed_crm_v2` by cross-correlation on the 30 s clip; the FOA anchor by the
  measured FOA-to-binaural lag; baselines on Zhu by cross-correlation; baselines on Argentum by
  their intrinsic delay and polarity measured on Zhu (-84/-85 samples, inverted) combined with
  the FOA-to-binaural table.
* **zhu2022 retrained** (`Zhu/train_hfmask.py`): mask up to 4 (+12 dB over |W|) and a
  multi-resolution log-magnitude loss. The original was 8-23 dB too quiet above 7 kHz.

The root README of the repository, section "Known differences between systems", lists what
re-rendering does not change and what should be reported with the results.

## Running

The configs need a webMUSHRA that stores results centrally and gives each participant a
per-person id (`?pid=...`). The questionnaire no longer asks for a self-made code.

Stock webMUSHRA:
* saves results only through `service/write.php` (PHP);
* does not lock "Next";
* stops if the audio device does not run at 48 kHz.

`analyze_results.py` screens untouched pages, and the intro asks for 48 kHz. Copy this folder
together with the unzipped `audio/` to `webMUSHRA/configs/listening_test_v2/` (stimulus paths
are `configs/listening_test_v2/audio/...`).

## Provenance

Built with `code/build_listening_test_v2r.py` in the research working copy (`Argentum_popr9`):

```
PYTHONPATH=code .venv/bin/python code/build_listening_test_v2r.py --out listening_test_v3_1 \
    --training zhu=zhu_009,argentum_pg=argentum_pg_006 \
    --baseline-alignment model-offset --loudness ffmpeg --raw-cache listening_test_v3_raw \
    --zhu-checkpoint /home/smck/Argentum/Zhu/models/binaural_rendering_100_hfmask.pt \
    --webmushra-style v3.1
```

Reference and CRM excerpts are taken from demo audio package v2.1 (normalised with ffmpeg).
