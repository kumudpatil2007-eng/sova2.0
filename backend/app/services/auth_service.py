import os
import sqlite3
import secrets
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

logger = logging.getLogger("sovereign_ai.auth")

# Initialize Argon2id hasher (high security, memory-hard against GPU/ASIC attacks)
ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32
)

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sovereign_auth.db"

# In-memory authenticated session store: token -> session dict
_active_sessions: Dict[str, Dict[str, Any]] = {}


def get_db_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db():
    """Initializes the SQLite authentication database and seeds default engineer if empty."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    display_name TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Check if any user exists
            cursor = conn.execute("SELECT COUNT(*) as count FROM users")
            count = cursor.fetchone()["count"]
            
            if count == 0:
                logger.info("Initializing local auth store: Seeding default user 'deepak' with Argon2id...")
                hashed = ph.hash("deepak123")
                conn.execute(
                    "INSERT INTO users (username, password_hash, display_name, created_at) VALUES (?, ?, ?, ?)",
                    ("deepak", hashed, "Deepak Sharma", datetime.now(timezone.utc).isoformat())
                )
                logger.info("Default local user 'deepak' successfully provisioned.")
    finally:
        conn.close()


def has_users() -> bool:
    """Returns True if at least one local user exists."""
    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT COUNT(*) as count FROM users")
        return cursor.fetchone()["count"] > 0
    finally:
        conn.close()


def create_user(username: str, password: str, display_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates a new local user with an Argon2id password hash.
    Plaintext passwords are NEVER stored.
    """
    clean_username = username.strip()
    if not clean_username or len(clean_username) < 2:
        raise ValueError("Username must be at least 2 characters.")
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")

    password_hash = ph.hash(password)
    created_at = datetime.now(timezone.utc).isoformat()
    disp = display_name.strip() if display_name else clean_username.capitalize()

    conn = get_db_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, display_name, created_at) VALUES (?, ?, ?, ?)",
                (clean_username, password_hash, disp, created_at)
            )
        logger.info(f"Local user '{clean_username}' registered with Argon2id hash.")
        return {
            "username": clean_username,
            "display_name": disp,
            "created_at": created_at
        }
    except sqlite3.IntegrityError:
        raise ValueError(f"Username '{clean_username}' already exists.")
    finally:
        conn.close()


def verify_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Verifies credentials using Argon2id.
    Returns sanitized user profile dict on success, None on failure.
    Does NOT reveal whether username or password was incorrect.
    """
    clean_username = username.strip()
    if not clean_username or not password:
        return None

    conn = get_db_connection()
    try:
        cursor = conn.execute("SELECT id, username, password_hash, display_name, created_at FROM users WHERE username = ?", (clean_username,))
        row = cursor.fetchone()
        if not row:
            # Perform dummy verify to mitigate timing attacks
            try:
                ph.verify("$argon2id$v=19$m=65536,t=3,p=4$dummy_salt$dummy_hash", password)
            except Exception:
                pass
            return None

        stored_hash = row["password_hash"]
        try:
            ph.verify(stored_hash, password)
            
            # Check if hash needs rehash with updated parameters
            if ph.check_needs_rehash(stored_hash):
                new_hash = ph.hash(password)
                with conn:
                    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, row["id"]))

            return {
                "id": row["id"],
                "username": row["username"],
                "display_name": row["display_name"] or row["username"],
                "created_at": row["created_at"]
            }
        except (VerifyMismatchError, InvalidHashError):
            return None
    finally:
        conn.close()


def create_session(user_data: Dict[str, Any]) -> str:
    """Generates a secure cryptographic session token for authenticated session."""
    token = secrets.token_hex(32)
    _active_sessions[token] = {
        "user": user_data,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    return token


def verify_session(token: str) -> Optional[Dict[str, Any]]:
    """Validates session token."""
    session = _active_sessions.get(token)
    if session:
        return session.get("user")
    return None


def revoke_session(token: str):
    """Revokes session token on lock/logout."""
    if token in _active_sessions:
        del _active_sessions[token]
