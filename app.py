"""Listening demo for the AES 2026 CRM Ambisonics-to-Binaural paper.

Streamlit GUI showing renderings of the same FOA recording produced by the
Proposed CRM, the Zhu et al. baseline, and the A2B (Gebru et al.) baseline,
together with the ground-truth binaural reference. Visitors at the poster
session listen to all four versions and rate each system on the ITU-style MOS
scale (1-5). The three systems are presented blind by default (System A / B / C
in randomised order) so the rating is not biased by the model name; one toggle
reveals or re-hides the real names.

Everything needed to run the test lives on the main screen: enter a name, use
Next / Prev to walk the clips, and rate. The (collapsed) sidebar only offers a
jump-to-any-clip list for convenience.

Run with:

    streamlit run app.py
"""

from __future__ import annotations

import os
import random
import sys
from pathlib import Path
from typing import Dict, List

import streamlit as st

_REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(_REPO / "src"))

from demo.catalog import (  # noqa: E402
    Catalog,
    Clip,
    Dataset,
    METHOD_LABELS,
    SYSTEMS_TO_RATE,
    load_catalog,
)
from demo.ratings import (  # noqa: E402
    Rating,
    RatingsStore,
    new_session_id,
    now_iso,
    now_stamp,
)
from demo.style import CUSTOM_CSS, MOS_SCALE, SYSTEM_COLORS  # noqa: E402
from demo.audio_player import gapless_player  # noqa: E402


CATALOG_PATH = _REPO / "configs" / "audio_index.json"
RATINGS_DIR = _REPO / "ratings"
# Audio root. Defaults to ``audio/`` next to this script for backwards
# compatibility; set DEMO_AUDIO_ROOT when the WAVs live elsewhere (for
# example after extracting them from a SharePoint share).
AUDIO_ROOT = Path(os.environ.get("DEMO_AUDIO_ROOT", _REPO / "audio")).expanduser()

# Paper QR shown in the upper-right corner (served via static serving so it is
# fetched once and not re-sent on every rerun). Regenerate static/paper_qr.png
# from the poster QR script if the URL changes.
PAPER_URL = "https://aes.org/publications/elibrary-page/?id=23351"
QR_PATH = _REPO / "static" / "paper_qr.png"


# ---------------------------------------------------------------- caching

@st.cache_resource(show_spinner=False)
def _load_catalog_cached(path_str: str, audio_root_str: str) -> Catalog:
    return load_catalog(path_str, audio_root=audio_root_str)


def _render_paper_qr() -> None:
    """Pin a QR code to the paper in the upper-right corner."""
    if not QR_PATH.exists():
        return
    st.markdown(
        f'<a class="paper-qr" href="{PAPER_URL}" target="_blank" rel="noopener" '
        f'title="Open the AES 2026 paper">'
        f'<img src="/app/static/paper_qr.png" alt="QR code to the AES 2026 paper" />'
        f'<span>Scan for the paper</span></a>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------- state

def _init_state() -> None:
    """Populate ``st.session_state`` on first run."""
    ss = st.session_state
    ss.setdefault("session_id", new_session_id())
    ss.setdefault("rater", "")
    ss.setdefault("blind_assignments", {})   # clip_id -> {label: system}
    ss.setdefault("show_ref", True)
    ss.setdefault("reveal_names", False)
    ss.setdefault("clip_pos", 0)             # index within the current dataset
    ss.setdefault("session_started", now_stamp())   # frozen for the CSV filename


def _blind_assignment(clip_id: str) -> Dict[str, str]:
    """Return a stable, per-clip shuffled mapping from blind label to system.

    The shuffle is seeded from the session id and clip id so the label order
    stays constant for the duration of the session but differs between clips.
    """
    cache = st.session_state["blind_assignments"]
    if clip_id in cache:
        return cache[clip_id]

    systems = list(SYSTEMS_TO_RATE)
    seed_int = abs(hash((st.session_state["session_id"], clip_id)))
    random.Random(seed_int).shuffle(systems)
    labels = [chr(ord("A") + i) for i in range(len(systems))]
    mapping = dict(zip(labels, systems))
    cache[clip_id] = mapping
    return mapping


# ---------------------------------------------------------------- navigation

def _nav_delta(delta: int, n: int) -> None:
    """Move the within-dataset clip pointer by ``delta`` (callback; clamps)."""
    ss = st.session_state
    ss["clip_pos"] = max(0, min(n - 1, ss.get("clip_pos", 0) + delta))


def _on_dataset_change() -> None:
    """Jump to the first clip when the dataset switch changes (callback)."""
    st.session_state["clip_pos"] = 0


def _nav_row(suffix: str, pos: int, n: int, *, dataset_switch: bool = False,
             ds_ids=None, ds_labels=None) -> None:
    prev_col, mid_col, next_col = st.columns([1, 5, 1], vertical_alignment="center")
    prev_col.button(
        "◀ Prev", key=f"prev_{suffix}", use_container_width=True,
        on_click=_nav_delta, args=(-1, n), disabled=pos == 0,
    )
    with mid_col:
        if dataset_switch:
            # The dataset switch lives between the arrows; switching it resets
            # to the first clip, the arrows step through the current dataset.
            st.radio(
                "Dataset", options=ds_ids,
                format_func=lambda x: ds_labels[x],
                key="dataset_id", horizontal=True,
                on_change=_on_dataset_change, label_visibility="collapsed",
            )
        else:
            st.markdown(
                f"<div style='text-align:center;color:#777;font-size:0.85rem;'>"
                f"Clip {pos + 1} / {n}</div>",
                unsafe_allow_html=True,
            )
    next_col.button(
        "Next ▶", key=f"next_{suffix}", use_container_width=True,
        on_click=_nav_delta, args=(1, n), disabled=pos == n - 1,
    )


# ---------------------------------------------------------------- rating

# MOS options. Index 0 is a sentinel "not rated" stop so the slider starts
# unrated (no anchored score); only 1-5 are real scores. The built-in tick bar
# is hidden (see style.py) and replaced by a custom 1..5 scale under the slider.
_MOS_UNRATED = "—"
_MOS_OPTIONS: List = [_MOS_UNRATED, 1, 2, 3, 4, 5]


def _mos_label(v) -> str:
    # Shown on the thumb: a clear "not rated" at the start, else the score.
    return "— not rated —" if v == _MOS_UNRATED else MOS_SCALE[v]


def _saved_mos(store: "RatingsStore | None", session_id: str, dataset: str,
               clip_id: str, system: str):
    """Return the MOS already saved this session for this clip+system, or None."""
    if store is None:
        return None
    for r in store.rows:
        if (r.session_id, r.dataset, r.clip_id, r.system) == (
                session_id, dataset, clip_id, system):
            return r.mos
    return None


def _write_rating(dataset_id: str, clip_id: str, system: str, blind_label: str,
                  mos_key: str, comment_key: str) -> None:
    ss = st.session_state
    rater = ss["rater"].strip()
    RatingsStore.for_rater(RATINGS_DIR, rater, ss.get("session_started")).upsert(
        Rating(
            timestamp=now_iso(),
            session_id=ss["session_id"],
            rater=rater,
            dataset=dataset_id,
            clip_id=clip_id,
            system=system,
            blind_label=blind_label,
            mos=int(ss.get(mos_key, 3)),
            comment=ss.get(comment_key, "").strip(),
        )
    )


def _autosave(dataset_id: str, clip_id: str, system: str, blind_label: str,
              mos_key: str, comment_key: str) -> None:
    """Slider changed → record the score (with whatever comment is present)."""
    ss = st.session_state
    if not ss.get("rater", "").strip():
        return                       # no identity yet; the UI shows a reminder
    if ss.get(mos_key, _MOS_UNRATED) == _MOS_UNRATED:
        return                       # still on the "not rated" stop
    _write_rating(dataset_id, clip_id, system, blind_label, mos_key, comment_key)


def _autosave_comment(dataset_id: str, clip_id: str, system: str, blind_label: str,
                      mos_key: str, comment_key: str) -> None:
    """Comment changed → attach it only if a score was already chosen, so a
    stray comment never silently records the midpoint default."""
    ss = st.session_state
    if not ss.get("rater", "").strip():
        return
    store = RatingsStore.for_rater(RATINGS_DIR, ss["rater"].strip(),
                                   ss.get("session_started"))
    if _saved_mos(store, ss["session_id"], dataset_id, clip_id, system) is None:
        return
    _write_rating(dataset_id, clip_id, system, blind_label, mos_key, comment_key)


# ---------------------------------------------------------------- clip view

def _render_clip(dataset: Dataset, clip: Clip, store: RatingsStore | None,
                 pos: int, n: int, ds_ids, ds_labels) -> None:
    ss = st.session_state
    reveal = ss.get("reveal_names", False)
    show_ref = ss.get("show_ref", True)

    mapping = _blind_assignment(clip.id)

    # ---- one shared-timeline player for every version of this clip ----
    # The reference is always identified; the three systems are blind A/B/C
    # unless revealed. Exactly one stream is audible at a time and they share a
    # single playhead, so switching is a true same-position A/B comparison.
    sources: List[Dict[str, str]] = []
    if show_ref and clip.has("reference"):
        sources.append({
            "id": "reference",
            "label": "Reference (ground truth)",
            "color": "#666",
            "path": clip.path("reference"),
        })
    for label, system in mapping.items():
        if not clip.has(system):
            continue
        sources.append({
            "id": label,
            "label": METHOD_LABELS[system] if reveal else f"System {label}",
            "color": SYSTEM_COLORS.get(label, "#888"),
            "path": clip.path(system),
        })

    # Heading row with the two playback toggles inline on the right. The single
    # reveal toggle replaces the old sidebar "Blind mode" checkbox and the
    # one-way per-clip reveal button; it flips freely both ways.
    head_col, ref_col, rev_col, _sp = st.columns(
        [1.5, 1.1, 1.85, 3.9], vertical_alignment="center")
    with head_col:
        st.markdown(
            "<h3 style='margin:0;padding:0;line-height:1.2;white-space:nowrap'>"
            "Listen &amp; compare</h3>",
            unsafe_allow_html=True)
    with ref_col:
        st.toggle("Show reference", key="show_ref",
                  help="Include the ground-truth binaural recording in the player.")
    with rev_col:
        st.toggle("Reveal system names", key="reveal_names",
                  help="Show or hide the real model names (A / B / C ↔ the systems).")

    if sources:
        # ``token`` controls when the browser re-decodes the audio: it depends on
        # the clip and on which sources are present (show_ref), but NOT on reveal
        # -- revealing only relabels the buttons and must not interrupt playback.
        token = f"{clip.id}|{int(show_ref)}|{len(sources)}"
        gapless_player(token=token, clip_id=clip.id,
                       session_id=ss["session_id"], sources=sources)
    else:
        st.info("No renderings available for this clip yet.")

    # Navigation (Prev / dataset switch / Next) + clip info, just above the
    # rating panel.
    _nav_row("nav", pos, n, dataset_switch=True, ds_ids=ds_ids, ds_labels=ds_labels)
    meta = (
        f"Clip **{pos + 1} / {n}** &nbsp;|&nbsp; "
        f"Clip **{clip.id}** &nbsp;|&nbsp; source `{clip.source}` &nbsp;|&nbsp; "
        f"{clip.duration_s:.0f} s starting at {clip.start_s:.1f} s"
    )
    if dataset.description:
        meta += (f" &nbsp;|&nbsp; <span style='color:#888;'>"
                 f"{dataset.description}</span>")
    st.markdown(meta, unsafe_allow_html=True)

    st.markdown(
        "<div style='display:flex;align-items:baseline;gap:0.55rem'>"
        "<h3 style='margin:0;padding:0;white-space:nowrap'>Rate each system</h3>"
        "<span style='color:#808495;font-size:0.9rem'>"
        "Use the player above to A/B the systems at the same moment, then score each on "
        "the MOS scale (5 = excellent … 1 = bad). Ratings autosave; changing a score just "
        "overwrites it.</span></div>",
        unsafe_allow_html=True,
    )
    if store is None:
        st.warning("Enter your name at the top to autosave your ratings.")

    cols = st.columns(len(mapping))
    for (label, system), col in zip(mapping.items(), cols):
        with col:
            heading = METHOD_LABELS[system] if reveal else f"System {label}"
            border = SYSTEM_COLORS.get(label, "#888")
            st.markdown(
                f'<div class="player-card" style="border-left-color:{border};">'
                f'<h4>{heading}</h4>'
                f'</div>',
                unsafe_allow_html=True,
            )

            if not clip.has(system):
                st.info(f"Rendering for {system} is not available yet.")
                continue

            mos_key = f"mos__{clip.id}__{label}"
            comment_key = f"comment__{clip.id}__{label}"
            ss.setdefault(mos_key, _MOS_UNRATED)
            ss.setdefault(comment_key, "")

            # Live widgets (no form): each change fires _autosave, then reruns.
            # Reruns are cheap (audio is served by URL) and the player iframe
            # persists, so playback is not interrupted.
            cb_args = (dataset.id, clip.id, system, label, mos_key, comment_key)
            st.select_slider(
                f"MOS for System {label}",
                options=_MOS_OPTIONS,
                format_func=_mos_label,
                key=mos_key,
                on_change=_autosave,
                args=cb_args,
            )
            # Custom 1..5 scale under the slider (the built-in tick bar is hidden
            # so "not rated" is not labelled; "1" is shifted right, off the
            # left-most "not rated" stop).
            st.markdown(
                "<div style='position:relative;height:2.6em;font-size:0.72rem;"
                "color:#808495;line-height:1.15;margin-top:-6px'>"
                f"<span style='position:absolute;left:15%;max-width:40%'>{MOS_SCALE[1]}</span>"
                f"<span style='position:absolute;right:0;max-width:46%;text-align:right'>"
                f"{MOS_SCALE[5]}</span></div>",
                unsafe_allow_html=True,
            )
            st.text_input(
                "Optional comment",
                key=comment_key,
                placeholder="e.g. spatial impression, timbre, artifacts",
                on_change=_autosave_comment,
                args=cb_args,
            )

            saved = _saved_mos(store, ss["session_id"], dataset.id, clip.id, system)
            if saved is not None:
                st.caption(f"✓ Autosaved — MOS {saved}")
            elif store is not None:
                st.caption("Not rated yet")


# ---------------------------------------------------------------- progress

def _progress_panel(catalog: Catalog, store: RatingsStore | None) -> None:
    st.markdown("### Progress for this rater")
    counts = (store.count_by_dataset_clip(session_id=st.session_state["session_id"])
              if store is not None else {})
    rows: List[Dict[str, str]] = []
    for ds in catalog.populated_datasets():
        for clip in ds.available_clips():
            done = counts.get((ds.id, clip.id), 0)
            total = len([m for m in SYSTEMS_TO_RATE if clip.has(m)])
            rows.append({
                "dataset": ds.label,
                "clip": clip.id,
                "rated": f"{done}/{total}",
            })
    st.dataframe(rows, use_container_width=True, hide_index=True)

    if store is not None:
        with open(store.csv_path, "rb") as fp:
            st.download_button(
                "Download my ratings as CSV",
                data=fp.read(),
                file_name=store.csv_path.name,
                mime="text/csv",
            )
    else:
        st.caption("Enter your name at the top to autosave and download your ratings.")


# ---------------------------------------------------------------- main

def main() -> None:
    st.set_page_config(
        page_title="AES 2026 CRM listening demo",
        page_icon="🎧",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    _init_state()
    _render_paper_qr()

    st.title("🎧 FOA → Binaural · listening test")
    st.markdown(
        "Listen to the reference and three rendering systems for each clip and "
        "rate each on the MOS scale. System names are hidden by default so your "
        "rating stays unbiased.  \n"
        "Flip **Reveal system names** once you're done."
    )

    if not CATALOG_PATH.exists():
        st.error(
            f"Audio index not found at `{CATALOG_PATH}`. "
            "Run `python scripts/generate_audio.py` first."
        )
        st.stop()
    if not AUDIO_ROOT.exists():
        st.warning(
            f"Audio root `{AUDIO_ROOT}` does not exist. "
            "Set `DEMO_AUDIO_ROOT` to the directory that contains the extracted "
            "demo audio (or place the WAVs under `audio/` next to this app)."
        )

    catalog = _load_catalog_cached(str(CATALOG_PATH), str(AUDIO_ROOT))
    populated = catalog.populated_datasets()
    if not populated:
        st.warning(
            "No audio found under the audio root. Run "
            "`python scripts/generate_audio.py` or set `DEMO_AUDIO_ROOT`."
        )
        st.stop()

    ds_ids = [d.id for d in populated]
    ds_labels = {d.id: d.label for d in populated}
    if st.session_state.get("dataset_id") not in ds_ids:
        st.session_state["dataset_id"] = ds_ids[0]   # seed before the radio widget
        st.session_state["clip_pos"] = 0

    # ---- identity (main screen; the sidebar is not needed to run the test) ----
    name_col, info_col = st.columns([2, 3], vertical_alignment="center")
    with name_col:
        st.text_input("Your name or initials", key="rater",
                      placeholder="Your name or initials",
                      label_visibility="collapsed")
    with info_col:
        st.caption(
            f"Session `{st.session_state['session_id']}` · "
            f"ratings autosave to `ratings/`."
        )

    dataset = catalog.dataset(st.session_state["dataset_id"])
    clips = dataset.available_clips()
    n = len(clips)
    pos = max(0, min(st.session_state["clip_pos"], n - 1))
    st.session_state["clip_pos"] = pos              # keep in range (set before widget)
    clip = clips[pos]

    rater = st.session_state["rater"].strip()
    store = (RatingsStore.for_rater(RATINGS_DIR, rater,
                                    st.session_state["session_started"])
             if rater else None)

    # ---- collapsed sidebar: optional jump to a clip in the current dataset ----
    with st.sidebar:
        st.subheader("Jump to a clip")
        st.selectbox(
            f"Clips in {dataset.label}",
            options=list(range(n)),
            format_func=lambda i: clips[i].id,
            key="clip_pos",
            label_visibility="collapsed",
        )
        st.caption("Switch datasets with the control between the arrows; "
                   "Next / Prev step through that dataset's clips.")

    _render_clip(dataset, clip, store, pos, n, ds_ids, ds_labels)

    _progress_panel(catalog, store)

    st.markdown(
        '<div class="footer">Zaporowski & Mróz, AES 2026 Paris. '
        'Code under CC BY-NC 4.0. See README for details.</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
