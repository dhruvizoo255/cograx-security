"""
Cograx Security — Streamlit dashboard.

A dark, terminal/ledger-inspired UI: the visual language of an audit log,
not a generic SaaS dashboard. Talks to the FastAPI backend over HTTP only —
never touches the model or blockchain directly.

Run with:
    streamlit run frontend/app.py
"""

from __future__ import annotations

import os
import sys

import requests
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.components.risk_gauge import render_risk_gauge
from frontend.components.security_checklist import render_checklist
from frontend.components.shap_chart import render_shap_chart
from frontend.utils.api_client import ApiClient
from frontend.utils.styling import inject_theme

st.set_page_config(
    page_title="Cograx Security — Risk Assessment",
    page_icon="⛓",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

API_BASE_URL = os.getenv("COGRAX_API_URL", "http://localhost:8000")
API_KEY = os.getenv("COGRAX_API_KEY", "")
client = ApiClient(API_BASE_URL, api_key=API_KEY)

if "history" not in st.session_state:
    st.session_state.history = []

# ---------------------------------------------------------------- Header ---
st.markdown(
    """
    <div class="cx-header">
        <div class="cx-header-mark">⛓&#8202;COGRAX</div>
        <div class="cx-header-sub">Explainable AI Smart-Contract Risk Assessment · Immutable Audit Trail</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------- Sidebar ---
with st.sidebar:
    st.markdown("### Token Submission")
    token_address = st.text_input(
        "Contract address", "0x1234567890abcdef1234567890abcdef12345678"
    )

    st.markdown("**Ownership & Control**")
    owner_can_mint = st.toggle("Owner can mint", value=False)
    owner_can_pause = st.toggle("Owner can pause / blacklist", value=False)
    ownership_renounced = st.toggle("Ownership renounced", value=True)
    contract_verified = st.toggle("Contract verified", value=True)

    st.markdown("**Liquidity**")
    liquidity_locked_pct = st.slider("Liquidity locked (%)", 0, 100, 50)
    lp_burned = st.toggle("LP burned", value=False)
    liquidity_usd = st.number_input(
        "Liquidity (USD)", min_value=0, value=250_000, step=1000
    )

    st.markdown("**Distribution & Activity**")
    top_holder_pct = st.slider("Top holder (%)", 0, 100, 20)
    number_of_holders = st.number_input(
        "Number of holders", min_value=0, value=5000, step=10
    )
    token_age_days = st.number_input("Token age (days)", min_value=0, value=180)
    daily_volume_usd = st.number_input(
        "Daily volume (USD)", min_value=0, value=50_000, step=1000
    )
    market_cap_usd = st.number_input(
        "Market cap (USD)", min_value=0, value=5_000_000, step=1000
    )

    st.markdown("**Taxes**")
    buy_tax = st.slider("Buy tax (%)", 0, 100, 5)
    sell_tax = st.slider("Sell tax (%)", 0, 100, 5)

    st.markdown("---")
    wallet_address = st.text_input("Your wallet (optional)", "")
    store_on_chain = st.checkbox("Anchor this prediction on-chain", value=False)

    submitted = st.button(
        "Run Risk Assessment", type="primary", use_container_width=True
    )

# ----------------------------------------------------------- Prediction ---
if submitted:
    payload = {
        "features": {
            "token_address": token_address,
            "liquidity_locked_pct": liquidity_locked_pct,
            "owner_can_mint": owner_can_mint,
            "owner_can_pause": owner_can_pause,
            "ownership_renounced": ownership_renounced,
            "contract_verified": contract_verified,
            "top_holder_pct": top_holder_pct,
            "number_of_holders": number_of_holders,
            "buy_tax": buy_tax,
            "sell_tax": sell_tax,
            "lp_burned": lp_burned,
            "token_age_days": token_age_days,
            "liquidity_usd": liquidity_usd,
            "daily_volume_usd": daily_volume_usd,
            "market_cap_usd": market_cap_usd,
        },
        "wallet_address": wallet_address or None,
        "store_on_chain": store_on_chain,
    }
    try:
        with st.spinner("Running scaling → inference → SHAP → hashing…"):
            result = client.predict(payload)
        st.session_state.last_prediction = result
        st.session_state.last_payload = payload
        st.session_state.history.insert(0, result)
    except requests.exceptions.ConnectionError:
        st.error(
            f"Could not reach the Cograx API at {API_BASE_URL}. Is the backend running?"
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"Prediction failed: {exc}")

# -------------------------------------------------------------- Results ---
result = st.session_state.get("last_prediction")

if result is None:
    st.markdown(
        '<div class="cx-empty">No assessment yet — submit token details in the sidebar to begin.</div>',
        unsafe_allow_html=True,
    )
else:
    col_gauge, col_meta = st.columns([1, 2])

    with col_gauge:
        render_risk_gauge(result["risk_score"], result["risk_level"])
        st.metric("Confidence", f"{result['confidence'] * 100:.1f}%")

    with col_meta:
        st.markdown(f"#### {result['token_address']}")
        st.markdown(f"> {result['natural_language_explanation']}")

        bc = result["blockchain_status"]
        if bc["stored"]:
            st.success(
                f"Anchored on-chain · tx `{bc['tx_hash']}` · block {bc['block_number']}"
            )
        elif bc.get("error"):
            st.info(f"Not anchored on-chain: {bc['error']}")

        st.markdown(
            f"""
            <div class="cx-ledger">
              <span>MODEL</span><code>{result['model_version']}</code>
              <span>PREDICTION ID</span><code>{result['prediction_id']}</code>
              <span>HASH</span><code>{result['prediction_hash'][:24]}…</code>
              <span>TIMESTAMP</span><code>{result['timestamp']}</code>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### Why this score — SHAP factors")
        render_shap_chart(
            result["top_positive_factors"], result["top_negative_factors"]
        )
    with c2:
        st.markdown("##### Security checklist")
        render_checklist(result["security_checklist"])

    if result["recommendations"]:
        st.markdown("##### Recommendations")
        for rec in result["recommendations"]:
            st.markdown(f"- {rec}")

    dl_col, _ = st.columns([1, 3])
    with dl_col:
        if st.button("Download PDF report"):
            try:
                pdf_bytes = client.report(
                    result["prediction_id"], st.session_state.last_payload
                )
                st.download_button(
                    "Save report",
                    data=pdf_bytes,
                    file_name=f"cograx_report_{result['prediction_id']}.pdf",
                    mime="application/pdf",
                )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Report generation failed: {exc}")

# ------------------------------------------------------------- History ---
if st.session_state.history:
    st.markdown("---")
    st.markdown("##### Prediction timeline")
    for item in st.session_state.history[:10]:
        ts = item["timestamp"]
        st.markdown(
            f"`{ts}` · **{item['risk_level']}** ({item['risk_score']}/100) · "
            f"`{item['token_address'][:10]}…` · hash `{item['prediction_hash'][:12]}…`"
        )
