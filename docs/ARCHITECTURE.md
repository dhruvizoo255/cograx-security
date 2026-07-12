# Architecture

`frontend` is an HTTP-only Streamlit client. FastAPI routes validate requests, invoke `PredictionService`, and return typed Pydantic responses. The service maps readable features to the frozen scaler order, performs read-only inference and SHAP explanation, applies deterministic security rules, then creates a hash-backed audit record. `AuditRepository` persists JSON evidence in SQLite transactionally; replace it with managed Postgres for horizontally scaled production.

The Vyper contract stores evidence only, never raw model inputs or model logic. This keeps on-chain cost and data exposure bounded. Every route the frontend calls other than `/health` sits behind an `X-API-Key` dependency (`backend/api/security.py`), and on-chain writes are restricted to the contract owner (the backend's signer) — see `docs/SECURITY.md` for the full trust-boundary writeup.
