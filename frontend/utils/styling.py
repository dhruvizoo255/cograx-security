"""Design tokens and CSS injection for the Cograx Security dashboard.

Design direction: an audit-ledger / terminal aesthetic — deep navy-black
surface, monospace data readouts, a teal 'verified' accent and a red/amber
risk accent — distinct from generic SaaS-dashboard defaults.
"""

from __future__ import annotations

import streamlit as st

_BG = "#0B1220"
_SURFACE = "#121A2C"
_TEXT = "#E5E9F0"
_MUTED = "#8A93A6"
_SAFE = "#2DD4BF"
_WARN = "#FBBF24"
_RISK = "#F87171"
_BORDER = "#1F2A40"


def inject_theme() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;600&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            color: {_TEXT};
        }}
        .stApp {{
            background: {_BG};
        }}
        section[data-testid="stSidebar"] {{
            background: {_SURFACE};
            border-right: 1px solid {_BORDER};
        }}
        /* Streamlit's default label/caption color is a dark grey tuned for a
           light theme background — nearly invisible against our dark navy
           sidebar. Force it light. Deliberately scoped to labels/markdown
           text only, not inputs, so text typed into the white input boxes
           stays dark-on-white and readable. */
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] label,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
        section[data-testid="stSidebar"] label {{
            color: {_TEXT} !important;
            opacity: 1 !important;
        }}
        /* Slider min/max endpoint labels use a separate testid. */
        section[data-testid="stSidebar"] [data-testid="stTickBarMin"],
        section[data-testid="stSidebar"] [data-testid="stTickBarMax"] {{
            color: {_MUTED} !important;
        }}
        /* Main content area also needs this — headers, list items, and body
           text (e.g. "Recommendations", the bullet list, "Prediction
           timeline") default to the same low-contrast grey outside the
           sidebar too. */
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] h5 {{
            color: {_TEXT} !important;
        }}
        .cx-header {{
            border-bottom: 1px solid {_BORDER};
            padding: 0.75rem 0 1rem 0;
            margin-bottom: 1rem;
        }}
        .cx-header-mark {{
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700;
            font-size: 1.6rem;
            letter-spacing: 0.04em;
            color: {_SAFE};
        }}
        .cx-header-sub {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            color: {_MUTED};
            letter-spacing: 0.02em;
        }}
        .cx-empty {{
            border: 1px dashed {_BORDER};
            border-radius: 6px;
            padding: 3rem 1rem;
            text-align: center;
            color: {_MUTED};
            font-family: 'JetBrains Mono', monospace;
        }}
        .cx-ledger {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            background: {_SURFACE};
            border: 1px solid {_BORDER};
            border-radius: 6px;
            padding: 0.75rem 1rem;
            display: grid;
            grid-template-columns: max-content 1fr;
            gap: 0.25rem 0.75rem;
            color: {_MUTED};
        }}
        .cx-ledger code {{
            color: {_TEXT};
            background: transparent;
        }}
        div[data-testid="stMetric"] {{
            background: {_SURFACE};
            border: 1px solid {_BORDER};
            border-radius: 6px;
            padding: 0.75rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


THEME = {
    "bg": _BG,
    "surface": _SURFACE,
    "text": _TEXT,
    "muted": _MUTED,
    "safe": _SAFE,
    "warn": _WARN,
    "risk": _RISK,
    "border": _BORDER,
}
