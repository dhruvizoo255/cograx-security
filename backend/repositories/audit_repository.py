"""Durable SQLite audit repository for prediction evidence and replay protection."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Optional

from backend.core.config import get_settings


class AuditRepository:
    """Small transactional repository; SQLite is suitable for a single API instance.

    Multi-instance production deployments should replace this implementation with
    a managed Postgres-backed repository behind the same interface.
    """

    def __init__(self, database_path: Path | None = None) -> None:
        self._path = database_path or get_settings().audit_db_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path, timeout=5, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS audits (
                    prediction_id TEXT PRIMARY KEY,
                    prediction_hash TEXT NOT NULL UNIQUE,
                    feature_hash TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    payload TEXT NOT NULL
                )""")
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_audits_replay "
                "ON audits(feature_hash, model_version)"
            )

    def save(self, record: dict) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT INTO audits
                (prediction_id, prediction_hash, feature_hash, model_version, timestamp, payload)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    record["prediction_id"],
                    record["prediction_hash"],
                    record["feature_hash"],
                    record["model_version"],
                    record["timestamp"],
                    json.dumps(record, sort_keys=True),
                ),
            )

    def get(self, prediction_id: str) -> Optional[dict]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM audits WHERE prediction_id = ?", (prediction_id,)
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def find_by_hash(self, prediction_hash: str) -> Optional[dict]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM audits WHERE prediction_hash = ?",
                (prediction_hash,),
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def find_by_feature_hash(
        self, feature_hash: str, model_version: str
    ) -> Optional[dict]:
        """Find the latest cacheable response for exact inputs and model version."""
        with self._connect() as connection:
            row = connection.execute(
                """SELECT payload FROM audits WHERE feature_hash = ? AND model_version = ?
                ORDER BY timestamp DESC LIMIT 1""",
                (feature_hash, model_version),
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def all(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM audits ORDER BY timestamp DESC"
            ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def count(self) -> int:
        with self._connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM audits").fetchone()[0])


_audit_repository_singleton: AuditRepository | None = None
_singleton_lock = threading.Lock()


def get_audit_repository() -> AuditRepository:
    global _audit_repository_singleton
    if _audit_repository_singleton is None:
        with _singleton_lock:
            if _audit_repository_singleton is None:
                _audit_repository_singleton = AuditRepository()
    return _audit_repository_singleton
