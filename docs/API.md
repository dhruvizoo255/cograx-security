# API

Start with `uvicorn backend.main:app --reload --port 8000`; interactive OpenAPI is at `/docs`.

`POST /api/v1/predict` accepts `{ "features": { ... }, "wallet_address": null, "store_on_chain": false }` and returns risk, confidence, SHAP factors, checklist, recommendations, hashes, and audit status. Bounds are enforced for percentage and non-negative numeric fields. When `COGRAX_API_KEY` is configured, send it as `X-API-Key` on every call below — required (not optional) once the environment is `production`. `GET /api/v1/audit/{id}`, `GET /api/v1/audit`, `POST /api/v1/predict/{id}/report`, and `GET /metrics` (no `/api/v1` prefix) expose SQLite-backed audit data and are gated behind the same key so audit history is never publicly enumerable.
