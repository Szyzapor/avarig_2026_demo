"""Gapless A/B comparison player as a no-build Streamlit component.

``st.audio`` renders each clip as an independent ``<audio>`` element with its
own clock, so two can play at once and they never share a playhead. For a blind
listening test we instead want *one* transport that drives every version of a
clip, with exclusive, sample-aligned, click-free switching between them. That is
implemented by the small Web Audio frontend in ``player/index.html``; this module
declares the component and tells it where to fetch the audio.

Audio is delivered by URL via Streamlit's static file server rather than inlined:
inlining ~28 MB of base64 per clip made *every* rerun (each Save, each reveal)
re-ship that payload and take ~4 s. Each clip's versions are instead copied once
into ``static/clips/<session>/<clip>/`` under blind filenames (``reference.wav``,
``A.wav`` … so the mapping never leaks through a URL) and served at
``/app/static/...``; reruns then ship only a few short URLs and stay snappy.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components

_DIR = Path(__file__).resolve().parent / "player"
_REPO = _DIR.parents[2]                       # src/demo/player -> repo root
_STATIC_CLIPS = _REPO / "static" / "clips"    # served by enableStaticServing
_URL_PREFIX = "/app/static/clips"             # absolute path -> iframe same-origin

_component = components.declare_component("gapless_player", path=str(_DIR))


@st.cache_data(show_spinner=False)
def _publish(session_id: str, clip_id: str, items: Tuple[Tuple[str, str], ...]) -> Dict[str, str]:
    """Copy each ``(id, src_wav)`` into the static dir under its blind id and
    return ``{id: url}``. Cached so the copy runs once per (session, clip)."""
    dest_dir = _STATIC_CLIPS / session_id / clip_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    urls: Dict[str, str] = {}
    for sid, src in items:
        dst = dest_dir / f"{sid}.wav"
        if not dst.exists() or dst.stat().st_size != Path(src).stat().st_size:
            shutil.copyfile(src, dst)
        urls[sid] = f"{_URL_PREFIX}/{session_id}/{clip_id}/{sid}.wav"
    return urls


def gapless_player(
    token: str,
    clip_id: str,
    session_id: str,
    sources: List[Dict[str, str]],
    height: int = 260,
    key: Optional[str] = "gapless_player",
) -> None:
    """Render the shared-timeline comparison player.

    Args:
        token: identity of the loaded audio set. The frontend re-decodes only
            when this changes, so reruns that merely relabel the sources (e.g.
            revealing the systems) do not interrupt playback.
        clip_id, session_id: used to place/serve this clip's static audio.
        sources: ordered ``{"id", "label", "color", "path"}`` dicts. ``path`` is
            an on-disk WAV; only the blind ``id``/``label`` reach the browser.
        key: stable component key so the iframe (decoded buffers + playback
            position) persists across Streamlit reruns.
    """
    items = tuple((s["id"], s["path"]) for s in sources)
    urls = _publish(session_id, clip_id, items)
    payload = [
        {
            "id": s["id"],
            "label": s["label"],
            "color": s.get("color", "#888"),
            "uri": urls[s["id"]],
        }
        for s in sources
    ]
    _component(token=token, sources=payload, height=height, key=key, default=None)
