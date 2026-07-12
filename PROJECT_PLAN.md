# PROJECT_PLAN.md — Cograx Security

## 1. Current Repository Analysis (as uploaded)

The uploaded archive `RugGuardAI.zip` contains the following, in full:

```
RugGuardAI/
├── models/
│   ├── rugguard_xgb.pkl      # trained XGBClassifier (binary)
│   └── scaler.pkl            # fitted sklearn StandardScaler
├── data/
│   └── rugguard_dataset.csv  # 10,000 rows, 15 columns
├── backend/       (empty)
├── frontend/      (empty)
├── notebooks/     (empty)
├── blockchain/    (empty)
├── tests/         (empty)
├── docs/          (empty)
└── utils/         (empty)
```

**Important correction to the brief:** the folder layout (`backend/`, `frontend/`, `notebooks/`, `blockchain/`, `tests/`, `docs/`, `utils/`) exists, but every one of those folders is empty. There are no notebooks, no SHAP code, no threshold-optimization code, no evaluation reports, and no application code anywhere in the archive. The **only real artifacts** are:

| File | What it actually is |
|---|---|
| `models/rugguard_xgb.pkl` | `xgboost.sklearn.XGBClassifier`, `objective=binary:logistic`, `n_estimators=400`, `max_depth=6`, `learning_rate=0.05`, `subsample=0.9`, `colsample_bytree=0.9`, `random_state=42`. Trained on 14 numeric features (no feature names embedded in the booster). |
| `models/scaler.pkl` | `sklearn.preprocessing.StandardScaler`, fitted on the same 14 columns, **with `feature_names_in_` embedded**, so we recovered the exact column order used at training time. |
| `data/rugguard_dataset.csv` | 10,000 rows × 15 columns (14 features + `RugPull` label). Label is imbalanced: 8,055 negative / 1,945 positive (~19.5% rug-pull rate). |

Recovered feature order (from the scaler, verified against the CSV header):
`Liquidity_Locked_Pct, Owner_Can_Mint, Owner_Can_Pause, Ownership_Renounced, Contract_Verified, TopHolder_Pct, Number_of_Holders, Buy_Tax, Sell_Tax, LP_Burned, Token_Age_Days, Liquidity_USD, Daily_Volume_USD, Market_Cap_USD`

I loaded both artifacts and ran inference end-to-end against the CSV to confirm the pipeline is internally consistent (scaler → model → `predict_proba` produces sane, monotonic-looking probabilities against known labels). **No retraining, refitting, or modification of `rugguard_xgb.pkl` or `scaler.pkl` was performed or will be performed** — per the frozen-artifact rule, they are copied byte-for-byte into the new repository.

There is no SHAP explainability, threshold-optimization logic, or evaluation code to preserve, because none exists in the upload — those are described in the brief as if already built, but they aren't present. This plan treats the **model + scaler + dataset** as the frozen ML core, and builds the SHAP explainability, thresholding, and everything else as new (clearly-labeled) work, not as edits to something pre-existing.

## 2. Architecture Review

There is no existing architecture to review — this is a from-scratch build on top of two frozen artifacts. The plan below is what will be built.

## 3. Strengths (of what was provided)

- The model and scaler are compatible and load cleanly with `joblib`.
- The scaler carries `feature_names_in_`, which removes ambiguity about feature order — a common failure point in "reconstruct the pipeline" tasks.
- The dataset's feature set maps naturally onto real rug-pull heuristics used by tools like GoPlus/Token Sniffer (mint/pause authority, ownership renouncement, LP burn, holder concentration, taxes), so a believable security narrative can be built around it honestly.

## 4. Weaknesses / Honest Limitations

- **No real on-chain data ingestion** — the dataset is engineered/synthetic-looking tabular data, not derived from live chain scans in this repo. This will be stated plainly in `MODEL.md` and `README.md`, not hidden.
- **No existing notebook or metrics artifact** — threshold, ROC/PR curves, and feature importance will be computed fresh (read-only against the frozen model) to populate `MODEL.md`, but there's no "original" evaluation to preserve.
- **Binary classifier, not multi-class** — the LOW/MEDIUM/HIGH/CRITICAL risk banding is a business-logic layer on top of the model's single probability output, not a property of the model itself.
- **No blockchain contract, ABI, or deployment scripts existed** — Vyper contract and web3 wrapper are new.

## 5. Implementation Roadmap

1. **Backend core** — FastAPI app, config, logging, exception handling.
2. **ML service layer** — `PredictorService` (loads frozen `.pkl`s once, never mutates them), `FeatureService` (validation + column ordering), `ExplainabilityService` (SHAP `TreeExplainer` against the frozen model, read-only).
3. **Security rule engine** — deterministic checks (mint/pause/owner/LP/tax/holder heuristics) independent of the ML score, combined into a risk band + recommendations.
4. **Hashing / integrity** — SHA-256 of input features + prediction, used both for audit and duplicate-prediction detection.
5. **Blockchain layer** — Vyper `RugGuardAudit` contract storing evidence (hash, score, confidence, timestamp, model version, token, wallet), `web3.py` wrapper, local deploy script (Anvil/Ganache-targeted).
6. **API routes** — `/predict`, `/health`, `/metrics`, `/audit/{id}`, versioned under `/api/v1`.
7. **Frontend** — Streamlit dashboard consuming the API (risk gauge, SHAP plots, checklist, PDF export, history).
8. **Reporting** — PDF generation service (reportlab) bundling prediction + SHAP + checklist.
9. **Tests** — unit tests per service, using the real frozen artifacts (no mocking of the model itself).
10. **DevOps** — Docker, docker-compose (api + streamlit), GitHub Actions (lint + test), pre-commit, Makefile.
11. **Docs** — README, ARCHITECTURE, API, DEPLOYMENT, MODEL, BLOCKCHAIN, SECURITY, CONTRIBUTING.

## 6. Dependency Graph (high level)

```
config  →  core (logging/exceptions)  →  services  →  api/routes  →  main (FastAPI app)
                                              ↑
                                   repositories (model/scaler/audit storage)
                                              ↑
                                   models/*.pkl, data/*.csv   (frozen, read-only)

blockchain/contracts (Vyper) → blockchain/scripts (deploy) → backend/services/blockchain_service → api/routes

frontend  →  backend API (HTTP only, no direct model access)
```

## 7. Suggested Improvements Beyond MVP (documented in README "Future Work")

GoPlus Security API integration, real on-chain feature extraction, temporal-leakage-aware retraining, continuous learning loop, multi-chain support.

---
*This document was generated before any implementation code was written, per project instructions.*
