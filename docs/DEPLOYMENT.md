# Deployment

Copy `.env.example` to `.env`; for production set `COGRAX_ENVIRONMENT=production`, a strong `COGRAX_API_KEY`, explicit CORS/trusted-host lists, SHA-256 artifact values, and persistent-volume path. `docker-compose.yml` loads the same `.env` for both the `api` and `dashboard` services, so the dashboard automatically authenticates with the same key once it's set — no separate configuration needed. Then run `docker compose up --build`. API is exposed at port 8000 and dashboard at 8501. The container runs unprivileged and mounts a named volume for SQLite audit evidence. For local development, install `requirements.txt`, run `make run`, and run `make ui` separately.

Before release run `make format`, `make lint`, and `make test`. Do not enable blockchain anchoring without a reviewed contract address and an RPC endpoint appropriate to the target network.
