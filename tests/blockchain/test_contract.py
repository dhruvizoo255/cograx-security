"""Contract-level checks for RugGuardAudit.vy.

Deliberately lightweight: compiles the contract (catches syntax/type errors
before they ever reach a deploy script) and asserts the on-chain trust
model — only the contract owner (the backend's signer) may write evidence —
is actually present in the bytecode's source, not just in the docs.
"""

from pathlib import Path

from vyper import compile_code

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2]
    / "blockchain"
    / "contracts"
    / "RugGuardAudit.vy"
)


def _source() -> str:
    return CONTRACT_PATH.read_text()


def test_contract_compiles() -> None:
    abi = compile_code(_source(), output_formats=["abi"])["abi"]
    function_names = {f["name"] for f in abi if f.get("type") == "function"}
    assert "storePrediction" in function_names
    assert "getPrediction" in function_names


def test_store_prediction_is_owner_restricted() -> None:
    """Regression guard: anyone being able to call storePrediction directly
    would let a third party forge evidence never produced by the backend."""
    source = _source()
    fn_start = source.index("def storePrediction")
    fn_body = source[fn_start : fn_start + 1200]
    assert "msg.sender == self.owner" in fn_body, (
        "storePrediction must stay restricted to the contract owner, or "
        "on-chain evidence is no longer provably backend-generated"
    )


def test_read_functions_stay_public() -> None:
    """Reads must NOT be owner-gated -- audit evidence should remain
    publicly verifiable on-chain, only writes are restricted."""
    source = _source()
    fn_start = source.index("def getPrediction")
    fn_body = source[fn_start : fn_start + 400]
    assert "msg.sender == self.owner" not in fn_body
