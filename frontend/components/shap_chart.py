"""Renders SHAP feature contributions as a horizontal waterfall-style bar chart."""

from __future__ import annotations

from typing import Dict, List

import plotly.graph_objects as go
import streamlit as st

from frontend.utils.styling import THEME


def render_shap_chart(positive: List[Dict], negative: List[Dict]) -> None:
    combined = sorted(positive + negative, key=lambda c: c["shap_value"])
    if not combined:
        st.info("No SHAP contributions available.")
        return

    labels = [c["feature"].replace("_", " ") for c in combined]
    values = [c["shap_value"] for c in combined]
    colors = [THEME["risk"] if v > 0 else THEME["safe"] for v in values]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=[f"{v:+.3f}" for v in values],
            textposition="outside",
        )
    )
    fig.update_layout(
        plot_bgcolor=THEME["surface"],
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono, monospace", color=THEME["text"], size=11),
        margin=dict(l=10, r=10, t=10, b=10),
        height=320,
        xaxis=dict(
            title="SHAP contribution to risk",
            gridcolor=THEME["border"],
            zerolinecolor=THEME["border"],
        ),
        yaxis=dict(gridcolor=THEME["border"]),
    )
    st.plotly_chart(fig, use_container_width=True)
