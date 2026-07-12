"""Renders the deterministic security checklist as colored badge rows."""

from __future__ import annotations

from typing import Dict, List

import streamlit as st

from frontend.utils.styling import THEME

_SEVERITY_COLOR = {
    "info": THEME["safe"],
    "low": THEME["safe"],
    "medium": THEME["warn"],
    "high": "#FB923C",
    "critical": THEME["risk"],
}


def render_checklist(checks: List[Dict]) -> None:
    if not checks:
        st.info("No security checks available.")
        return

    rows = []
    for c in checks:
        icon = "✅" if c["passed"] else "⚠️"
        color = _SEVERITY_COLOR.get(c["severity"], THEME["muted"])
        rows.append(
            f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:0.45rem 0;border-bottom:1px solid {THEME['border']};">
                <div style="font-family:'Inter',sans-serif;font-size:0.85rem;color:{THEME['text']};">
                    {icon}&nbsp; {c['name']}
                </div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;
                            color:{color};text-transform:uppercase;letter-spacing:0.05em;">
                    {c['severity']}
                </div>
            </div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;
                        color:{THEME['muted']};padding-bottom:0.35rem;">
                {c['detail']}
            </div>
            """
        )
    st.markdown("".join(rows), unsafe_allow_html=True)
