"""Streamlit styling shared across the demo."""

from __future__ import annotations

# Standard MOS scale (ITU-R BS.1116 / P.800 wording, abbreviated).
MOS_SCALE = {
    5: "5 - Excellent (imperceptible difference)",
    4: "4 - Good (perceptible but not annoying)",
    3: "3 - Fair (slightly annoying)",
    2: "2 - Poor (annoying)",
    1: "1 - Bad (very annoying)",
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
    /* The built-in slider tick bar is hidden; a custom 1..5 scale is rendered
       under each MOS slider instead (so the "not rated" start stop is
       unlabelled and "1" is shifted off the far-left position). */
    [data-testid="stSliderTickBar"] { display: none; }
    [data-testid="stSlider"] { margin-bottom: 0.1rem; }

    /* Free the upper-right corner for the paper QR by hiding only the Deploy
       button, the ⋮ options menu, and the run-status widget. Do NOT hide the
       whole stToolbar: the control that re-opens a collapsed sidebar lives
       inside it, so hiding the toolbar would trap the sidebar closed. */
    [data-testid="stAppDeployButton"],
    [data-testid="stMainMenu"],
    [data-testid="stStatusWidget"] { display: none !important; }

    /* Paper QR, fixed in the upper-right corner. */
    a.paper-qr {
        position: fixed; top: 0.55rem; right: 0.8rem; z-index: 1000000;
        display: flex; flex-direction: column; align-items: center;
        text-decoration: none;
        background: rgba(255, 255, 255, 0.92);
        padding: 6px 6px 3px; border-radius: 10px;
        box-shadow: 0 1px 6px rgba(0, 0, 0, 0.18);
    }
    a.paper-qr img { width: 185px; height: 185px; display: block; }
    a.paper-qr span { font-size: 0.78rem; color: #333; margin-top: 3px; }
    a.paper-qr:hover { box-shadow: 0 2px 10px rgba(0, 0, 0, 0.28); }

    /* Trim Streamlit's large default top padding so the title sits near the top
       (the toolbar that used to need that clearance is hidden). */
    [data-testid="stMainBlockContainer"], .block-container {
        padding-top: 0.25rem !important;
    }
    [data-testid="stMainBlockContainer"] h1:first-of-type,
    .block-container h1:first-of-type { margin-top: 0; padding-top: 0; }
    /* Shrink the (mostly empty) top chrome so the page starts near the top. Keep
       the toolbar present — it holds the sidebar-expand control — but short. */
    [data-testid="stHeader"] { height: 0; background: transparent; }
    [data-testid="stToolbar"] { height: 1.4rem !important; min-height: 0 !important; }

    /* Center the dataset switch between the nav arrows. The radio shrinks to its
       content, so we centre its (flex-item) element container within the column. */
    [data-testid="stRadio"] { width: fit-content; }
    [data-testid="stElementContainer"]:has(> [data-testid="stRadio"]) {
        margin-left: auto; margin-right: auto;
    }
    [data-testid="stRadio"] [role="radiogroup"] { justify-content: center; }

    /* The two playback toggles read ~8px high beside the big heading; nudge them
       down so they sit level with it. (Only those two toggles are stCheckbox.) */
    [data-testid="stCheckbox"] { position: relative; top: 8px; }
</style>
"""
