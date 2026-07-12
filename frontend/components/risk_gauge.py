"""Risk gauge — a semi-circular arc gauge rendered as inline SVG, colored by
risk level, echoing the ledger/audit visual language of the dashboard."""

from __future__ import annotations

import math

import streamlit as st

from frontend.utils.styling import THEME

_LEVEL_COLOR = {
    "LOW": THEME["safe"],
    "MEDIUM": THEME["warn"],
    "HIGH": "#FB923C",
    "CRITICAL": THEME["risk"],
}


def render_risk_gauge(risk_score: float, risk_level: str) -> None:
    color = _LEVEL_COLOR.get(risk_level, THEME["muted"])
    angle = math.pi * (risk_score / 100)
    cx, cy, r = 100, 100, 80

    needle_x = cx - r * math.cos(angle)
    needle_y = cy - r * math.sin(angle)

    svg = f"""
    <svg viewBox="0 0 200 120" width="100%" height="160">
        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none"
              stroke="{THEME['border']}" stroke-width="14" stroke-linecap="round"/>
        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none"
              stroke="{color}" stroke-width="14" stroke-linecap="round"
              stroke-dasharray="{angle * r} {math.pi * r}"/>
        <line x1="{cx}" y1="{cy}" x2="{needle_x:.1f}" y2="{needle_y:.1f}"
              stroke="{THEME['text']}" stroke-width="3" stroke-linecap="round"/>
        <circle cx="{cx}" cy="{cy}" r="6" fill="{THEME['text']}"/>
        <text x="100" y="95" text-anchor="middle" font-family="Space Grotesk, sans-serif"
              font-size="28" font-weight="700" fill="{color}">{risk_score:.0f}</text>
        <text x="100" y="112" text-anchor="middle" font-family="JetBrains Mono, monospace"
              font-size="11" fill="{THEME['muted']}">RISK / 100 · {risk_level}</text>
    </svg>
    """
    st.markdown(svg, unsafe_allow_html=True)
