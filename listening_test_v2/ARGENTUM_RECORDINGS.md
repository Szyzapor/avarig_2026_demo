# Argentum recordings by role (proposed model popr9_mirror_rot_level)

Generated from `code/aligned_data.py` (Argentum_popr9): pair table `alignment/argentum_parts.json`, hold-out set `ARGENTUM_HOLDOUT`, train/validation split by recording group with `val_fraction=0.1, seed=42` (defaults of `build_train_val`). The checkpoint was fine-tuned from `popr9_aligned_mirror_rot`, trained with the same split; its training log confirms 40 training / 3 validation Argentum groups. The model was also trained on Zhu train, Urban and A2B-2MP data. "Parts" are the cut segments of each recording; "excluded" parts failed the alignment check and were never used.

## Training

| Recording | Usable parts | Excluded parts | Usable duration |
|---|---|---|---|
| ZM1_CDebussy-Wrzosy | 7 | 1 | 3.5 min |
| ZM1_CDebussyFeux | 10 | 0 | 5.0 min |
| ZM1_CharityConcert01 | 15 | 0 | 7.5 min |
| ZM1_CharityConcert02 | 12 | 0 | 6.0 min |
| ZM1_CharityConcert04 | 11 | 0 | 5.5 min |
| ZM1_CharityConcert05 | 28 | 0 | 14.0 min |
| ZM1_CharityConcert06 | 16 | 0 | 8.0 min |
| ZM1_ChoirConcert | 314 | 0 | 157.0 min |
| ZM1_ChopinRecital1 | 50 | 0 | 25.0 min |
| ZM1_Concert | 174 | 0 | 87.0 min |
| ZM1_EGrieg-LetniWieczor | 6 | 0 | 3.0 min |
| ZM1_EmigrahGra | 20 | 0 | 10.0 min |
| ZM1_FChopinRevolutionary | 6 | 0 | 3.0 min |
| ZM1_FLisztPaganiniVariations | 11 | 0 | 5.5 min |
| ZM1_Franck | 38 | 1 | 19.0 min |
| ZM1_FranckSonata | 32 | 0 | 16.0 min |
| ZM1_JHaydnSonata1 | 14 | 0 | 7.0 min |
| ZM1_JHaydnSonata2 | 14 | 0 | 7.0 min |
| ZM1_JJunek-BogoroditseDevo | 8 | 0 | 4.0 min |
| ZM1_JMaklakiewicz-Kołysanka | 6 | 0 | 3.0 min |
| ZM1_JSBachPreludeFuge1 | 27 | 0 | 13.5 min |
| ZM1_JSBachPreludeFuge2 | 9 | 0 | 4.5 min |
| ZM1_JSBachPreludeFugeC | 9 | 0 | 4.5 min |
| ZM1_JubileeConcert | 136 | 0 | 68.0 min |
| ZM1_MNymanChanson | 17 | 0 | 8.5 min |
| ZM1_MNymanEsWar | 11 | 0 | 5.5 min |
| ZM1_MNymanPsalm | 9 | 0 | 4.5 min |
| ZM1_MRavelMiroirs | 8 | 0 | 4.0 min |
| ZM1_PARTYcz1 | 16 | 0 | 8.0 min |
| ZM1_PARTYcz2 | 24 | 0 | 12.0 min |
| ZM1_PARTYcz4 | 16 | 0 | 8.0 min |
| ZM1_PGrainger-BridalLullaby | 7 | 0 | 3.5 min |
| ZM1_PMykietynPrelude | 6 | 0 | 3.0 min |
| ZM1_Prokofiev | 34 | 0 | 17.0 min |
| ZM1_SRachmaninovPrelude | 12 | 0 | 6.0 min |
| ZM1_VMiskinis-OSalutarisHostia | 7 | 0 | 3.5 min |
| ZM1_Widno | 29 | 0 | 14.5 min |
| ZM1_band | 17 | 0 | 8.5 min |
| ZM1_scena1 | 7 | 0 | 3.5 min |
| ZM1_scena2 | 2 | 0 | 1.0 min |

40 recordings, 9.96 h usable.

## Validation (checkpoint selection only)

| Recording | Usable parts | Excluded parts | Usable duration |
|---|---|---|---|
| ZM1_CDebussyCanope | 8 | 0 | 4.0 min |
| ZM1_LvBeethovenSonata | 41 | 0 | 20.5 min |
| ZM1_PassionConcert | 160 | 0 | 80.0 min |

3 recordings, 1.74 h usable.

## Hold-out (never used in training or validation; listening-test clips come only from here)

| Recording | Usable parts | Excluded parts | Usable duration |
|---|---|---|---|
| ZM1_CharityConcert03 | 12 | 0 | 6.0 min |
| ZM1_ChopinRecital2 | 30 | 1 | 15.0 min |
| ZM1_IDenisova-CherubicHymn | 9 | 0 | 4.5 min |
| ZM1_JHaydnSonata3 | 9 | 0 | 4.5 min |
| ZM1_MRaczynski-LaudateDominum | 7 | 0 | 3.5 min |
| ZM1_MRavelValse | 27 | 0 | 13.5 min |
| ZM1_ORespighi-Notturno | 13 | 0 | 6.5 min |
| ZM1_PARTYcz3 | 18 | 0 | 9.0 min |
| ZM1_SopotPier | 23 | 0 | 11.5 min |

9 recordings, 1.23 h usable.

## Not used (no usable parts)

| Recording | Usable parts | Excluded parts | Usable duration |
|---|---|---|---|

0 recordings, 0.00 h usable.

