import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from ..config import settings
from ..llm.model_catalog import (
    ModelPurpose,
    get_default_model_catalog,
    find_matching_installed_model
)

logger = logging.getLogger("sovereign_ai.model_registry")
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sovereign_auth.db"


def get_db_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_model_registry_db():
    """Initializes the model registry table in SQLite."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_registry (
                    purpose TEXT PRIMARY KEY,
                    configured_model TEXT NOT NULL,
                    active_model TEXT NOT NULL,
                    is_available INTEGER NOT NULL DEFAULT 0,
                    is_mandatory INTEGER NOT NULL DEFAULT 1,
                    role_title TEXT NOT NULL,
                    description TEXT,
                    vram_gb REAL DEFAULT 3.5,
                    last_synced TEXT NOT NULL
                )
            """)
    finally:
        conn.close()


def sync_model_registry(installed_models: List[str]) -> List[Dict[str, Any]]:
    """
    Synchronizes the database model registry with config.py and Ollama's installed models.
    Guarantees that changing config.py updates the active model registry.
    Eliminates any stale/legacy model references (e.g. qwen2.5-vl:7b).
    """
    init_model_registry_db()
    catalog = get_default_model_catalog()
    now_iso = datetime.now(timezone.utc).isoformat()
    synced_records: List[Dict[str, Any]] = []

    conn = get_db_connection()
    try:
        with conn:
            for purpose, spec in catalog.items():
                configured_model = spec.name
                matched_model = find_matching_installed_model(configured_model, installed_models)
                is_avail = 1 if matched_model else 0
                active_model = matched_model if matched_model else configured_model

                conn.execute("""
                    INSERT INTO model_registry (
                        purpose, configured_model, active_model, is_available,
                        is_mandatory, role_title, description, vram_gb, last_synced
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(purpose) DO UPDATE SET
                        configured_model = excluded.configured_model,
                        active_model = excluded.active_model,
                        is_available = excluded.is_available,
                        is_mandatory = excluded.is_mandatory,
                        role_title = excluded.role_title,
                        description = excluded.description,
                        vram_gb = excluded.vram_gb,
                        last_synced = excluded.last_synced
                """, (
                    purpose.value,
                    configured_model,
                    active_model,
                    is_avail,
                    1 if spec.is_mandatory else 0,
                    spec.role_title,
                    spec.description,
                    spec.vram_gb,
                    now_iso
                ))

                synced_records.append({
                    "purpose": purpose.value,
                    "configured_model": configured_model,
                    "active_model": active_model,
                    "is_available": bool(is_avail),
                    "is_mandatory": spec.is_mandatory,
                    "role_title": spec.role_title,
                    "description": spec.description,
                    "vram_gb": spec.vram_gb,
                    "last_synced": now_iso
                })

        logger.info(f"Model registry synchronized ({len(synced_records)} entries updated in database)")
    finally:
        conn.close()

    return synced_records


def get_model_registry_records() -> List[Dict[str, Any]]:
    """Retrieves all model registry entries from the SQLite database."""
    init_model_registry_db()
    conn = get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT purpose, configured_model, active_model, is_available,
                   is_mandatory, role_title, description, vram_gb, last_synced
            FROM model_registry
            ORDER BY purpose ASC
        """)
        rows = cursor.fetchall()
        return [
            {
                "purpose": row["purpose"],
                "configured_model": row["configured_model"],
                "active_model": row["active_model"],
                "is_available": bool(row["is_available"]),
                "is_mandatory": bool(row["is_mandatory"]),
                "role_title": row["role_title"],
                "description": row["description"],
                "vram_gb": row["vram_gb"],
                "last_synced": row["last_synced"]
            }
            for row in rows
        ]
    finally:
        conn.close()
