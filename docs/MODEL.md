# Model Card — Cograx Security Rug-Pull Risk Model

This document exists so anyone reading the repository can see exactly what
the model is, how it was evaluated, and what it should and shouldn't be
trusted for. The artifacts described here are **frozen** — this repository
never trains, retrains, or mutates them. Startup integrity checks compare
their SHA-256 against `.env` (see `COGRAX_MODEL_SHA256` / `COGRAX_SCALER_SHA256`)
and refuse to boot on a mismatch, so the model actually serving predictions
is provably the one this card describes.

## 1. Intended use

Cograx Security estimates the probability that a given ERC-20 token exhibits
the on-chain and tokenomic characteristics typically associated with a
"rug pull" (an exit scam or malicious liquidity withdrawal). The score is
**decision support for human review** — a triage signal to prioritize which
tokens deserve manual due diligence. It is:

- **Not** investment advice.
- **Not** a security audit or certification of a contract.
- **Not** a guarantee about future contract behavior — it scores a static
  snapshot of features at prediction time.

## 2. Model artifacts

| Artifact | Type | Configuration |
|---|---|---|
| `models/rugguard_xgb.pkl` | `xgboost.sklearn.XGBClassifier`, `objective=binary:logistic` | `n_estimators=400`, `max_depth=6`, `learning_rate=0.05`, `subsample=0.9`, `colsample_bytree=0.9`, `random_state=42` |
| `models/scaler.pkl` | `sklearn.preprocessing.StandardScaler` | Fit on the same 14 numeric features, in the exact column order the model expects |

`FeatureService` is responsible for taking the human-readable request schema
and re-ordering it into that exact column order before scaling.

## 3. Training data

`data/rugguard_dataset.csv` — 10,000 rows of **engineered security features**
(liquidity lock %, mint/pause authority, ownership renouncement, contract
verification, top-holder concentration, holder count, buy/sell tax, LP-burn
status, token age, liquidity/volume/market-cap in USD) with a binary
`RugPull` label. Class balance is roughly 80.6% negative / 19.5% positive
(8,055 / 1,945).

**This is not live on-chain data.** It's a structured, engineered-feature
dataset built to represent the signal patterns real rug pulls exhibit — not
a scrape of Etherscan/GoPlus history. See §7 for the planned migration path.

## 4. Metrics

Evaluated by scoring the frozen model + scaler against the full dataset
described above:

| Metric | Value |
|---|---|
| ROC-AUC | 0.997 |
| Accuracy | 0.973 |
| Precision (RugPull=1) | 0.892 |
| Recall (RugPull=1) | 0.978 |
| F1 | 0.933 |

**Read these honestly, not as a certification.** The original train/validation
split used when the model was fit is not preserved in this repository, so
these numbers characterize how well the frozen model fits the known dataset
as a whole — they are not an independently verified, held-out generalization
score. Treat them as evidence the model has learned the intended signal, not
as a production SLA.

## 5. Threshold explanation

The model outputs a raw probability in `[0, 1]`. That probability is scaled
to a 0–100 `risk_score` and mapped to a band by `risk_engine.py`:

| Band | Score range | Meaning |
|---|---|---|
| LOW | 0–24 | Few or no rug-pull indicators present |
| MEDIUM | 25–49 | Some indicators present; manual review advised |
| HIGH | 50–74 | Multiple strong indicators present |
| CRITICAL | 75–100 | Pattern strongly consistent with historical rug pulls |

These band cutoffs are a **product decision layered on top of the model**,
not something the model itself learned — they can be retuned without
touching the frozen artifacts.

## 6. Explainability (SHAP)

Every prediction is explained with `shap.TreeExplainer` against the frozen
booster (`explainability_service.py`). The response includes the top
risk-increasing and top risk-reducing features for that specific token, each
with its raw value and signed SHAP contribution — so a reviewer can see
*why* a score was assigned, not just the number itself. This is local
(per-prediction) explainability, not a global feature-importance ranking.

## 7. Limitations

- **Feature source, not live extraction.** Inputs are supplied by the caller
  (or a future data-source integration) rather than fetched live from chain
  state by this service today.
- **Static snapshot.** A token can change behavior (mint, pause, liquidity
  pull) after a prediction is made; the score does not update itself.
- **Engineered-feature dataset**, not a scrape of real historical incidents
  — see §3.
- **Class imbalance** (~19.5% positive) means precision/recall trade-offs
  matter more than accuracy alone; the threshold bands in §5 exist partly to
  make that trade-off visible to the end user instead of hiding it behind a
  single accept/reject cut.
- **No adversarial robustness claims.** A sophisticated actor who understands
  the feature set could structure a token to score artificially low.

## 8. Future migration path (no architecture change required)

The service boundary (`FeatureService` producing the model's expected column
order) is intentionally the only place a future data source needs to plug
in:

- **GoPlus Security API** — live contract-risk flags (honeypot, mintable,
  proxy, blacklist) to replace/augment manually supplied features.
- **Etherscan / block-explorer APIs** — verified-source status, holder
  distribution, and contract age pulled live instead of caller-supplied.
- **Historical blockchain snapshots** — building a labeled dataset from
  *actual* past rug pulls (rather than engineered features) for a future
  retraining pass.

None of this requires changing `PredictionService`, the API contract, or the
blockchain audit trail — only `FeatureService`'s data source and, eventually,
a retrained model artifact behind the same frozen-artifact integrity check
described in the introduction above.
