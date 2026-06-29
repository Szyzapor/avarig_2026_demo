"""Listening demo for the AES 2026 CRM Ambisonics-to-Binaural paper.

Streamlit GUI showing renderings of the same FOA recording produced by the
Proposed CRM, the Zhu et al. baseline, and the A2B (Gebru et al.) baseline,
together with the ground-truth binaural reference. Visitors at the poster
session listen to all four versions and rate each system on the
ITU-style MOS scale (1-5). The systems are presented blind by default
(System A / B / C / D in randomised order) so the rating is not biased by
the model name.

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
)
from demo.style import CUSTOM_CSS, MOS_SCALE, SYSTEM_COLORS  # noqa: E402


CATALOG_PATH = _REPO / "configs" / "audio_index.json"
RATINGS_DIR = _REPO / "ratings"
# Audio root. Defaults to ``audio/`` next to this script for backwards
# compatibility; set DEMO_AUDIO_ROOT when the WAVs live elsewhere (for
# example after extracting them from a SharePoint share).
AUDIO_ROOT = Path(os.environ.get("DEMO_AUDIO_ROOT", _REPO / "audio")).expanduser()


# ---------------------------------------------------------------- caching

@st.cache_resource(show_spinner=False)
def _load_catalog_cached(path_str: str, audio_root_str: str) -> Catalog:
    return load_catalog(path_str, audio_root=audio_root_str)


# ---------------------------------------------------------------- state

def _init_state() -> None:
    """Populate ``st.session_state`` on first run."""
    ss = st.session_state
    ss.setdefault("session_id", new_session_id())
    ss.setdefault("rater", "")
    ss.setdefault("reveal", {})              # clip_id -> bool
    ss.setdefault("blind_assignments", {})   # clip_id -> {label: system}
    ss.setdefault("ratings_loaded_for", None)
    ss.setdefault("show_help", False)


def _blind_assignment(clip_id: str) -> Dict[str, str]:
    """Return a stable, per-clip shuffled mapping from blind label to system.

    The shuffle uses :func:`random.Random` seeded with the clip id so the
    label order stays constant for the duration of the session but differs
    between clips.
    """
    cache = st.session_state["blind_assignments"]
    if clip_id in cache:
        return cache[clip_id]

    systems = list(SYSTEMS_TO_RATE)
    seed_int = abs(hash((st.session_state["session_id"], clip_id)))
    random.Random(seed_int).shuffle(systems)
    labels = ["A", "B", "C"]
    mapping = dict(zip(labels, systems))
    cache[clip_id] = mapping
    return mapping


# ---------------------------------------------------------------- sidebar

def _sidebar(catalog: Catalog) -> tuple[Dataset, Clip] | tuple[None, None]:
    ss = st.session_state
    st.sidebar.header("Listening session")
    rater = st.sidebar.text_input("Rater name (or initials)", value=ss["rater"])
    if rater != ss["rater"]:
        ss["rater"] = rater
        ss["ratings_loaded_for"] = None

    st.sidebar.markdown(f"Session ID: `{ss['session_id']}`")

    populated = catalog.populated_datasets()
    if not populated:
        st.sidebar.warning(
            "No audio found in `audio/`. Run `scripts/generate_audio.py` first."
        )
        return None, None

    dataset_labels = {d.id: d.label for d in populated}
    dataset_id = st.sidebar.selectbox(
        "Dataset",
        options=list(dataset_labels.keys()),
        format_func=lambda x: dataset_labels[x],
    )
    dataset = catalog.dataset(dataset_id)

    clips = dataset.available_clips()
    clip_labels = {c.id: f"{c.id}  ({c.duration_s:.0f}s)" for c in clips}
    clip_id = st.sidebar.selectbox(
        "Clip",
        options=[c.id for c in clips],
        format_func=lambda x: clip_labels[x],
    )
    clip = next(c for c in clips if c.id == clip_id)

    st.sidebar.divider()
    st.sidebar.caption("Blind mode hides the model behind labels A / B / C.")
    blind_on = st.sidebar.checkbox("Blind mode", value=True, key="blind_on")
    show_ref = st.sidebar.checkbox("Show reference player", value=True, key="show_ref")

    st.sidebar.divider()
    if st.sidebar.button("Reset blind ordering for this clip"):
        ss["blind_assignments"].pop(clip.id, None)
        ss["reveal"].pop(clip.id, None)

    st.sidebar.caption("Ratings autosave to `ratings/ratings_<rater>.csv`.")
    return dataset, clip


# ---------------------------------------------------------------- main panel

def _render_clip(dataset: Dataset, clip: Clip, store: RatingsStore | None) -> None:
    ss = st.session_state
    blind_on = ss.get("blind_on", True)
    show_ref = ss.get("show_ref", True)

    st.subheader(f"Dataset: {dataset.label}")
    if dataset.description:
        st.caption(dataset.description)

    meta = (
        f"Clip **{clip.id}** &nbsp;|&nbsp; source `{clip.source}` &nbsp;|&nbsp; "
        f"{clip.duration_s:.0f} s starting at {clip.start_s:.1f} s"
    )
    st.markdown(meta, unsafe_allow_html=True)

    # Reference player (always identified, never blinded).
    if show_ref and clip.has("reference"):
        with st.container():
            st.markdown(
                '<div class="player-card" style="border-left-color:#666;">'
                '<h4>Reference (ground truth binaural)</h4>'
                '<div class="player-meta">This is the original captured binaural recording.</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.audio(clip.path("reference"))

    st.markdown("### Listen and rate each system")
    st.caption(
        "Headphones strongly recommended. Use the MOS scale: "
        "5 = excellent, 4 = good, 3 = fair, 2 = poor, 1 = bad."
    )

    mapping = _blind_assignment(clip.id)
    reveal = ss["reveal"].get(clip.id, False) or not blind_on

    cols = st.columns(len(mapping))
    for (label, system), col in zip(mapping.items(), cols):
        with col:
            heading = f"System {label}" if not reveal else METHOD_LABELS[system]
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
            st.audio(clip.path(system))

            # MOS slider with descriptive labels via select_slider.
            mos_key = f"mos__{clip.id}__{label}"
            comment_key = f"comment__{clip.id}__{label}"
            default = ss.get(mos_key, 3)
            mos = st.select_slider(
                f"MOS for System {label}",
                options=[1, 2, 3, 4, 5],
                value=default,
                format_func=lambda v: MOS_SCALE[v],
                key=mos_key,
            )
            comment = st.text_input(
                "Optional comment",
                value=ss.get(comment_key, ""),
                key=comment_key,
                placeholder="e.g. spatial impression, timbre, artifacts",
            )

            # Save button per system. Storing per-system makes it harder to lose
            # work if the rater navigates away mid-clip.
            if st.button(f"Save rating for System {label}", key=f"save__{clip.id}__{label}"):
                if store is None:
                    st.error("Enter a rater name in the sidebar first.")
                else:
                    rating = Rating(
                        timestamp=now_iso(),
                        session_id=ss["session_id"],
                        rater=ss["rater"],
                        dataset=dataset.id,
                        clip_id=clip.id,
                        system=system,
                        blind_label=label,
                        mos=int(mos),
                        comment=comment.strip(),
                    )
                    store.append(rating)
                    st.success(
                        f"Saved MOS={mos} for System {label} "
                        f"({METHOD_LABELS[system] if reveal else 'hidden'})."
                    )

    st.divider()

    bc1, bc2, _ = st.columns([1, 1, 2])
    with bc1:
        if blind_on and st.button(
            "Reveal which system is which",
            disabled=reveal, use_container_width=True,
        ):
            ss["reveal"][clip.id] = True
            st.rerun()
    with bc2:
        if reveal:
            keys = "".join([f"<li><b>System {l}</b> = {METHOD_LABELS[s]}</li>"
                            for l, s in mapping.items()])
            st.markdown(f"<ul>{keys}</ul>", unsafe_allow_html=True)


# ---------------------------------------------------------------- progress

def _progress_panel(catalog: Catalog, store: RatingsStore | None) -> None:
    if store is None:
        return
    st.markdown("### Progress for this rater")
    counts = store.count_by_dataset_clip()
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

    with open(store.csv_path, "rb") as fp:
        st.download_button(
            "Download my ratings as CSV",
            data=fp.read(),
            file_name=store.csv_path.name,
            mime="text/csv",
        )


# ---------------------------------------------------------------- main

def main() -> None:
    st.set_page_config(
        page_title="AES 2026 CRM listening demo",
        page_icon="🎧",
        layout="wide",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    _init_state()

    st.title("🎧 FOA → Binaural · listening test")
    st.markdown(
        "Listen to four versions of the same recording (Reference + three "
        "rendering systems) and rate each system on the MOS scale. The model "
        "names are hidden by default to keep the rating unbiased."
    )

    if not CATALOG_PATH.exists():
        st.error(
            f"Audio index not found at `{CATALOG_PATH}`. Run "
            "`python scripts/generate_audio.py` (or `scripts/build_index.py`) first."
        )
        st.stop()

    if not AUDIO_ROOT.exists():
        st.warning(
            f"Audio root `{AUDIO_ROOT}` does not exist. "
            "Set `DEMO_AUDIO_ROOT` to the directory that contains the "
            "extracted demo audio (or place the WAVs under `audio/` next to "
            "this app)."
        )
    catalog = _load_catalog_cached(str(CATALOG_PATH), str(AUDIO_ROOT))
    dataset, clip = _sidebar(catalog)
    if dataset is None or clip is None:
        st.stop()

    store: RatingsStore | None = None
    if st.session_state["rater"]:
        store = RatingsStore.for_rater(RATINGS_DIR, st.session_state["rater"])

    _render_clip(dataset, clip, store)
    _progress_panel(catalog, store)

    st.markdown(
        '<div class="footer">Zaporowski & Mroz, AES 2026 Paris. '
        'Code under CC BY-NC 4.0. See README for details.</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
