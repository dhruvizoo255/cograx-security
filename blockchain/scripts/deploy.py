"""
Deploy `RugGuardAudit.vy` to a local or remote EVM chain.

Usage:
    python -m blockchain.scripts.deploy --rpc http://127.0.0.1:8545

Requires `vyper` and `web3` to be installed, and a funded deployer account
(the `DEPLOYER_PRIVATE_KEY` environment variable, or a local dev chain such
as Anvil / Ganache with unlocked accounts).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

CONTRACT_PATH = (
    Path(__file__).resolve().parent.parent / "contracts" / "RugGuardAudit.vy"
)
ABI_OUTPUT_PATH = Path(__file__).resolve().parent.parent / "abi" / "RugGuardAudit.json"


def compile_contract() -> tuple[str, list]:
    """Compile the Vyper contract, returning (bytecode_hex, abi)."""
    import vyper

    source = CONTRACT_PATH.read_text()
    output = vyper.compile_code(source, output_formats=["bytecode", "abi"])
    return output["bytecode"], output["abi"]


def deploy(rpc_url: str, private_key: str | None) -> str:
    from web3 import Web3

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise RuntimeError(f"Could not connect to RPC endpoint: {rpc_url}")

    bytecode, abi = compile_contract()

    ABI_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ABI_OUTPUT_PATH.write_text(json.dumps(abi, indent=2))

    if private_key:
        account = w3.eth.account.from_key(private_key)
        sender = account.address
    else:
        # Dev-chain convenience path (Anvil/Ganache default unlocked account).
        sender = w3.eth.accounts[0]

    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = Contract.constructor().build_transaction(
        {
            "from": sender,
            "nonce": w3.eth.get_transaction_count(sender),
        }
    )

    if private_key:
        signed = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    else:
        tx_hash = w3.eth.send_transaction(tx)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"RugGuardAudit deployed at: {receipt.contractAddress}")
    print(f"ABI written to: {ABI_OUTPUT_PATH}")
    return receipt.contractAddress


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy the RugGuardAudit contract.")
    parser.add_argument(
        "--rpc", default=os.getenv("WEB3_RPC_URL", "http://127.0.0.1:8545")
    )
    parser.add_argument("--private-key", default=os.getenv("DEPLOYER_PRIVATE_KEY"))
    args = parser.parse_args()

    deploy(args.rpc, args.private_key)
