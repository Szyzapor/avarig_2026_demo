"""Streamlit styling shared across the demo."""

from __future__ import annotations

# Standard MOS scale (ITU-R BS.1116 / P.800 wording, abbreviated).
MOS_SCALE = {
    5: "5 — Excellent (imperceptible difference)",
    4: "4 — Good (perceptible but not annoying)",
    3: "3 — Fair (slightly annoying)",
    2: "2 — Poor (annoying)",
    1: "1 — Bad (very annoying)",
}

# Soft pastel palette for the four players.
SYSTEM_COLORS = {
    "A": "#9ec5fe",
    "B": "#ffc107",
    "C": "#9ddfaf",
    "D": "#f9a8d4",
}

CUSTOM_CSS = """
<style>
    .player-card {
        background: var(--secondary-background-color);
        border-radius: 8px;
        padding: 1rem 1rem 0.6rem 1rem;
        margin-bottom: 0.5rem;
        border-left: 6px solid #888;
    }
    .player-card h4 { margin-top: 0; margin-bottom: 0.4rem; }
    .player-meta { color: #666; font-size: 0.85rem; margin-bottom: 0.4rem; }
    .footer { color: #888; font-size: 0.8rem; margin-top: 2rem; }
    .pill {
        display: inline-block; padding: 0.15rem 0.6rem;
        border-radius: 999px; background: #eef; color: #224;
        font-size: 0.8rem; margin-right: 0.4rem;
    }
</style>
"""
