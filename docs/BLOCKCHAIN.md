# Blockchain

Compile and deploy with `python -m blockchain.scripts.deploy --rpc http://127.0.0.1:8545`. The script writes `blockchain/abi/RugGuardAudit.json`; commit the generated ABI for the configured contract release. Set `COGRAX_BLOCKCHAIN_ENABLED=true`, RPC URL, and contract address to anchor evidence.

The contract rejects duplicate prediction hashes, bounds score/confidence to basis points, emits `PredictionStored`, and stores no ML model or raw feature values. `storePrediction` is restricted to `owner` (set at deploy time to the deployer/backend signer address), so only the backend can write evidence — anyone can still read it via `getPrediction`/`isDuplicateHash`. Review and test on the target chain before any public deployment.
