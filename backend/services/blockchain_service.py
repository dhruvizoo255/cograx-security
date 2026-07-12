"""
Blockchain service — the API's interface to the on-chain `RugGuardAudit`
contract. Gracefully degrades to "not stored" when blockchain access is
disabled or unreachable, so the ML/security parts of the API keep working
even without a configured chain.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from backend.api.schemas.response_schemas import BlockchainStatus
from backend.core.config import Settings, get_settings
from backend.core.logging_config import get_logger

logger = get_logger(__name__)

ABI_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "blockchain"
    / "abi"
    / "RugGuardAudit.json"
)


class BlockchainService:
    """Wraps web3.py calls to `RugGuardAudit`. Lazily connects on first use."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._w3 = None
        self._contract = None

    def _ensure_connected(self) -> bool:
        if not self._settings.blockchain_enabled:
            return False
        if self._w3 is not None:
            return self._w3.is_connected()
        try:
            from web3 import Web3

            self._w3 = Web3(Web3.HTTPProvider(self._settings.web3_rpc_url))
            if not self._w3.is_connected():
                logger.warning(
                    "Blockchain RPC unreachable at %s", self._settings.web3_rpc_url
                )
                return False
            if not ABI_PATH.exists():
                logger.error("Contract ABI missing at %s", ABI_PATH)
                return False
            if self._settings.contract_address:
                abi = json.loads(ABI_PATH.read_text())
                self._contract = self._w3.eth.contract(
                    address=Web3.to_checksum_address(self._settings.contract_address),
                    abi=abi,
                )
            return True
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("Blockchain connection failed: %s", exc)
            return False

    @property
    def is_connected(self) -> bool:
        return self._ensure_connected()

    def store_prediction(
        self,
        prediction_id: str,
        token_address: str,
        wallet_address: Optional[str],
        prediction_hash: str,
        risk_score: float,
        confidence: float,
        model_version: str,
        timestamp: int,
    ) -> BlockchainStatus:
        """Store prediction evidence on-chain. Returns a status object that
        never raises for infra failures — the caller always gets a response,
        with `error` populated on failure."""
        if not self._ensure_connected() or self._contract is None:
            return BlockchainStatus(
                stored=False, error="Blockchain not connected/configured."
            )

        try:
            sender = (
                self._w3.eth.account.from_key(
                    self._settings.deployer_private_key
                ).address
                if self._settings.deployer_private_key
                else self._w3.eth.accounts[0]
            )
            transaction = self._contract.functions.storePrediction(
                self._w3.keccak(text=prediction_id),
                self._w3.to_checksum_address(token_address),
                (
                    self._w3.to_checksum_address(wallet_address)
                    if wallet_address
                    else "0x0000000000000000000000000000000000000000"
                ),
                self._w3.keccak(
                    hexstr=(
                        prediction_hash
                        if prediction_hash.startswith("0x")
                        else "0x" + prediction_hash
                    )
                ),
                int(risk_score * 100),
                int(confidence * 10000),
                model_version,
                timestamp,
            ).build_transaction(
                {
                    "from": sender,
                    "chainId": self._settings.chain_id,
                    "nonce": self._w3.eth.get_transaction_count(sender),
                }
            )
            if self._settings.deployer_private_key:
                signed = self._w3.eth.account.sign_transaction(
                    transaction, self._settings.deployer_private_key
                )
                tx_hash = self._w3.eth.send_raw_transaction(signed.raw_transaction)
            else:
                tx_hash = self._w3.eth.send_transaction(transaction)
            receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash)
            return BlockchainStatus(
                stored=True,
                tx_hash=receipt.transactionHash.hex(),
                block_number=receipt.blockNumber,
                contract_address=self._settings.contract_address,
            )
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.error("Failed to store prediction on-chain: %s", exc)
            return BlockchainStatus(stored=False, error=str(exc))
