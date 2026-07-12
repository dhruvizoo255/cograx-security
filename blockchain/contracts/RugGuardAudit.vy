# @version ^0.3.10
"""
@title RugGuardAudit
@notice Immutable evidence store for Cograx Security risk predictions.
@dev Stores ONLY evidence of an off-chain ML prediction (hash, score,
     confidence, model version, timestamp). The ML model, features, and
     inference logic never touch the chain — only tamper-evident evidence
     of a prediction result does.
"""

event PredictionStored:
    predictionId: indexed(bytes32)
    tokenAddress: indexed(address)
    wallet: indexed(address)
    predictionHash: bytes32
    riskScore: uint256
    confidence: uint256
    modelVersion: String[64]
    timestamp: uint256

event OwnershipTransferred:
    previousOwner: indexed(address)
    newOwner: indexed(address)

struct PredictionRecord:
    tokenAddress: address
    wallet: address
    predictionHash: bytes32
    riskScore: uint256      # 0-10000 (basis points, i.e. risk_score * 100)
    confidence: uint256     # 0-10000 (basis points)
    modelVersion: String[64]
    timestamp: uint256
    exists: bool

owner: public(address)
records: public(HashMap[bytes32, PredictionRecord])
predictionCountByToken: public(HashMap[address, uint256])
totalPredictions: public(uint256)

# Duplicate-prediction protection: predictionHash -> already seen
seenHashes: public(HashMap[bytes32, bool])


@external
def __init__():
    self.owner = msg.sender


@external
def transferOwnership(newOwner: address):
    assert msg.sender == self.owner, "not owner"
    assert newOwner != empty(address), "zero address"
    previous: address = self.owner
    self.owner = newOwner
    log OwnershipTransferred(previous, newOwner)


@external
def storePrediction(
    predictionId: bytes32,
    tokenAddress: address,
    wallet: address,
    predictionHash: bytes32,
    riskScore: uint256,
    confidence: uint256,
    modelVersion: String[64],
    timestamp: uint256,
) -> bool:
    """
    @notice Store evidence of a prediction on-chain. Reverts on duplicate hash.
    @dev Restricted to `owner` (the backend's configured signer address). This
         is the on-chain half of the trust model: the backend is the only
         account that can ever hold a private key for `owner`, so a record
         existing in this contract is provable evidence that Cograx Security's
         API produced it -- not something anyone can write directly by calling
         this function themselves. Ownership can be rotated with
         `transferOwnership` if the signer key is rotated.
    """
    assert msg.sender == self.owner, "only the Cograx Security signer may store evidence"
    assert not self.records[predictionId].exists, "prediction id already stored"
    assert not self.seenHashes[predictionHash], "duplicate prediction hash"
    assert riskScore <= 10000, "risk score out of range"
    assert confidence <= 10000, "confidence out of range"

    self.records[predictionId] = PredictionRecord({
        tokenAddress: tokenAddress,
        wallet: wallet,
        predictionHash: predictionHash,
        riskScore: riskScore,
        confidence: confidence,
        modelVersion: modelVersion,
        timestamp: timestamp,
        exists: True,
    })
    self.seenHashes[predictionHash] = True
    self.predictionCountByToken[tokenAddress] += 1
    self.totalPredictions += 1

    log PredictionStored(
        predictionId, tokenAddress, wallet, predictionHash, riskScore, confidence, modelVersion, timestamp
    )
    return True


@view
@external
def getPrediction(predictionId: bytes32) -> PredictionRecord:
    return self.records[predictionId]


@view
@external
def isDuplicateHash(predictionHash: bytes32) -> bool:
    return self.seenHashes[predictionHash]
