# Cograx Security

**Explainable AI-powered Smart Contract Security Risk Assessment Platform with Immutable Blockchain Audit Trails.**

> **Status: release candidate.** Frozen ML artifacts are preserved byte-for-byte; application hardening, release tooling, test coverage, and documentation are included.

## What's working right now

- **Frozen ML artifacts preserved as-is**: `models/rugguard_xgb.pkl` (XGBoost) and `models/scaler.pkl` (StandardScaler), copied byte-for-byte from the upload, never retrained or refit.
- **Full FastAPI backend** (`backend/`) --clean-architecture layout (`core`, `services`, `repositories`, `api/routes`, `api/schemas`). Verified end-to-end: `/health` (open), `POST /api/v1/predict`, `/api/v1/audit`, `/api/v1/audit/{id}`, `/api/v1/predict/{id}/report`, `/metrics` (validation → scaling → inference → thresholding → SHAP → hashing → optional blockchain anchor → response). Every route except `/health` requires an `X-API-Key` header once `COGRAX_API_KEY` is set — see `docs/SECURITY.md`.
- **SHAP explainability**, wired against the frozen model via `shap.TreeExplainer` — confirmed working locally with real output (see example below).
- **Deterministic security rule engine** -- mint/pause/ownership/verification/liquidity/holder-concentration/tax/age/liquidity-depth checks, independent of the ML score.
- **Vyper smart contract** (`blockchain/contracts/RugGuardAudit.vy`) storing prediction evidence on-chain (hash, score, confidence, model version, timestamp), restricted to the contract `owner` (the backend's signer) so evidence is provably backend-generated, plus a `deploy.py` script and a `web3.py`-based `BlockchainService` that degrades gracefully when no chain is configured.
- **Streamlit dashboard** (`frontend/app.py`) -- dark ledger/terminal-styled UI with a risk gauge, SHAP bar chart, security checklist, blockchain status, PDF export, and prediction timeline.

### Verified example (real output from this build)

```
POST /api/v1/predict  →  risk_score: 99.93, risk_level: CRITICAL
Top risk factors (SHAP): TopHolder_Pct, Liquidity_Locked_Pct, Owner_Can_Pause, Ownership_Renounced, Owner_Can_Mint
```

## Quickstart

```bash
pip install -r requirements.txt

# Backend
uvicorn backend.main:app --reload --port 8000

# Frontend (separate terminal)
COGRAX_API_URL=http://localhost:8000 streamlit run frontend/app.py
```

Interactive API docs: `http://localhost:8000/docs`.

## Repository layout

```
backend/        FastAPI app — core, services, repositories, api/routes, api/schemas
blockchain/      Vyper contract, deploy script, ABI output
frontend/        Streamlit dashboard, components, styling, API client
models/          Frozen rugguard_xgb.pkl + scaler.pkl (do not modify)
data/            Frozen rugguard_dataset.csv
docs/            Architecture, model card, deployment, and security docs
tests/           Unit + integration tests (backend services and API routes)
```

## Known limitations (honest, per project philosophy)

- The frozen model was trained on engineered/tabular features, not live on-chain scans — there is no real-time feature-extraction pipeline in this repo. See `docs/MODEL.md` for the full model card.
- Audit evidence persists transactionally in SQLite (`backend/repositories/audit_repository.py`), not an in-memory dict — durable across restarts, but a single-file database, not a clustered production datastore. See `docs/SECURITY.md` for the managed-Postgres migration note at multi-instance scale.
- Every `/api/v1/*` route and `/metrics` require an `X-API-Key` header once `COGRAX_API_KEY` is set (always required in production — see `docs/SECURITY.md`). This is a single shared key, not per-user identity/RBAC.
- On-chain, `storePrediction` is restricted to the contract `owner` (the backend's signer address), so a stored record is provable evidence the backend wrote it — see `docs/SECURITY.md` for the full trust-model writeup.
- Blockchain anchoring requires a locally deployed contract and a running RPC node (e.g., Anvil); it is not connected to any live network by default (`blockchain_enabled=False`).

See `PROJECT_PLAN.md`, `FINAL_REVIEW.md`, and `docs/` for architecture, API, model, blockchain, deployment, and security guidance.
