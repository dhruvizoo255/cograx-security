from pathlib import Path

from backend.repositories.audit_repository import AuditRepository


def test_repository_indexes_stable_feature_hash(tmp_path: Path) -> None:
    repo = AuditRepository(tmp_path / "audit.db")
    record = {
        "prediction_id": "p1",
        "prediction_hash": "evidence",
        "feature_hash": "features",
        "model_version": "v1",
        "timestamp": "2026-01-01T00:00:00+00:00",
    }
    repo.save(record)
    assert repo.get("p1") == record
    assert repo.find_by_hash("evidence") == record
    assert repo.find_by_feature_hash("features", "v1") == record
