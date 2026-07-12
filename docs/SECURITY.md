# Security

Input schemas constrain percentages and non-negative quantities. Every
`/api/v1/*` endpoint — inference, audit lookup, audit listing, report
generation — and the `/metrics` endpoint require a constant-time-compared
`X-API-Key` header whenever `COGRAX_API_KEY` is configured; production
config validation refuses to start without one set (see
`backend/core/config.py`). The inference endpoint additionally has a
process-local fixed-window rate limit per client IP. `GET /health` stays
open by design (used for container/orchestrator liveness probes and reveals
no audit data). CORS defaults to the local Streamlit origin, not `*`.
Feature fingerprints replay identical requests from the audit cache;
timestamped prediction hashes provide immutable evidence.

**On-chain trust model.** `RugGuardAudit.storePrediction` is restricted to
`msg.sender == owner`, where `owner` is set at deploy time to the backend's
signer address. This means a record existing in the contract is provable
evidence that Cograx Security's backend (the only holder of that private
key) wrote it — not something any address could write directly by calling
the function. If the signer key is ever rotated, `transferOwnership` moves
that guarantee to the new key. A richer scheme (e.g. EIP-712 signed
payloads verified on-chain, supporting multiple authorized signers) is a
reasonable next step if this ever needs more than one writer; it was not
added here to avoid introducing a second trust primitive where a single
owner-gated writer already satisfies the requirement.

Audit evidence persists transactionally in SQLite and should be placed on
an encrypted persistent volume. For multi-instance deployment, replace it
with managed Postgres and distributed rate limiting.

**What a single shared API key does *not* give you:** per-user identity,
audit-log attribution to a specific human, or role-based access control.
It is a reasonable bar for an MVP/portfolio deployment behind a small trusted
frontend, not a substitute for a real identity provider. Production beyond
that still wants: a proper identity/authorization layer (OAuth2/OIDC or
per-client API keys with scopes), a secret manager instead of `.env`, TLS
termination, structured log aggregation, dependency scanning, backups, and
an independent third-party audit of the Vyper contract before it is trusted
with anything of real value.
