"""
db_store.py — Persistent Backend Store
Dual-mode: PostgreSQL (Supabase) when RBI_DB_PATH starts with "postgres",
           SQLite otherwise (local dev).

Set environment variable:
    RBI_DB_PATH = postgresql://postgres:[PASSWORD]@db.ekqbtuwocnxlxjbiftei.supabase.co:5432/postgres

All public function signatures are unchanged — App.py and modules need no edits.
"""

import sqlite3
import hashlib
import hmac
import os
import json
import io
from datetime import datetime
from typing import Optional, Dict, List, Any

import pandas as pd

# ── Detect mode ────────────────────────────────────────────────────────────
# Streamlit Cloud stores secrets in st.secrets, not os.environ
def _get_db_url() -> str:
    # 1. Try os.environ first (local dev / Docker)
    url = os.environ.get("RBI_DB_PATH", "")
    if url:
        return url
    # 2. Try st.secrets (Streamlit Cloud)
    try:
        import streamlit as st
        url = st.secrets.get("RBI_DB_PATH", "")
        if url:
            return url
    except Exception:
        pass
    return ""

_DB_URL = _get_db_url()
_IS_PG  = _DB_URL.startswith("postgres")

# SQLite fallback path (used when RBI_DB_PATH is not a postgres URL)
_SQLITE_PATH = (
    _DB_URL if _DB_URL and not _IS_PG
    else os.path.join(os.path.dirname(os.path.abspath(__file__)), "rbi_csf_data.db")
)

# Legacy alias so App.py `st.session_state["BASE_DIR"]` doesn't break
DB_PATH = _SQLITE_PATH


# ══════════════════════════════════════════════════════════════════════════
#  POSTGRESQL WRAPPER  — makes psycopg2 behave like sqlite3 for this codebase
# ══════════════════════════════════════════════════════════════════════════

class _PGCursor:
    """Thin cursor wrapper: dict-like rows + lastrowid via RETURNING id."""
    def __init__(self, raw_cur):
        self._c       = raw_cur
        self._last_id = None

    def fetchone(self):
        try:
            row = self._c.fetchone()
            return dict(row) if row else None
        except Exception:
            return None

    def fetchall(self):
        try:
            rows = self._c.fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    @property
    def lastrowid(self):
        if self._last_id is not None:
            return self._last_id
        try:
            row = self._c.fetchone()
            if row:
                d = dict(row)
                self._last_id = d.get("id")
                return self._last_id
        except Exception:
            pass
        return None

    def __iter__(self):
        return iter(self.fetchall())


class _PGConn:
    """
    Wraps a psycopg2 connection to mimic sqlite3's interface:
      • con.execute(sql, params)  → returns _PGCursor
      • con.executescript(sql)    → runs ; -separated statements
      • context manager           → commit on exit, rollback on error
    """
    def __init__(self):
        import psycopg2
        import psycopg2.extras
        self._raw = psycopg2.connect(
            _DB_URL,
            cursor_factory=psycopg2.extras.RealDictCursor,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _adapt(sql: str) -> str:
        """Replace SQLite-isms with PostgreSQL equivalents."""
        sql = sql.replace("?", "%s")
        sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        sql = sql.replace("BLOB",          "BYTEA")
        sql = sql.replace("COLLATE NOCASE","")
        # SQLite PRAGMA lines — drop them
        lines = [l for l in sql.splitlines()
                 if not l.strip().upper().startswith("PRAGMA")]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def execute(self, sql: str, params=()):
        sql = self._adapt(sql)
        # For INSERT statements without RETURNING, append it so lastrowid works
        stripped = sql.strip().upper()
        if stripped.startswith("INSERT") and "RETURNING" not in stripped:
            sql = sql.rstrip().rstrip(";") + " RETURNING id"
        cur = self._raw.cursor()
        cur.execute(sql, params or ())
        wrapper = _PGCursor(cur)
        # Pre-fetch id for INSERT so fetchone() on the cursor later still works
        if stripped.startswith("INSERT"):
            try:
                row = cur.fetchone()
                wrapper._last_id = dict(row).get("id") if row else None
            except Exception:
                pass
        return wrapper

    def executescript(self, script: str):
        """Run a ; -separated DDL script (used by init_db)."""
        cur = self._raw.cursor()
        for stmt in script.split(";"):
            stmt = stmt.strip()
            if stmt:
                stmt = self._adapt(stmt)
                try:
                    cur.execute(stmt)
                except Exception:
                    self._raw.rollback()
                    raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_):
        if exc_type is None:
            self._raw.commit()
        else:
            self._raw.rollback()
        self._raw.close()


# ══════════════════════════════════════════════════════════════════════════
#  CONNECTION HELPER  — returns either _PGConn or sqlite3.Connection
# ══════════════════════════════════════════════════════════════════════════

def _conn():
    if _IS_PG:
        return _PGConn()
    # SQLite
    con = sqlite3.connect(_SQLITE_PATH, check_same_thread=False, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def _row(r) -> dict:
    """Normalise a row to plain dict (works for both sqlite3.Row and dict)."""
    if r is None:
        return {}
    if isinstance(r, dict):
        return r
    return dict(r)


# ══════════════════════════════════════════════════════════════════════════
#  SCHEMA INIT
# ══════════════════════════════════════════════════════════════════════════

def init_db() -> None:
    """Create all tables if they don't exist yet. Safe to call on every startup."""
    with _conn() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL COLLATE NOCASE,
            password_hash TEXT    NOT NULL,
            salt          TEXT    NOT NULL,
            role          TEXT    NOT NULL DEFAULT 'user',
            created_at    TEXT    NOT NULL,
            last_login    TEXT
        );

        CREATE TABLE IF NOT EXISTS bank_profiles (
            user_id       INTEGER PRIMARY KEY,
            bank_name     TEXT,
            bank_level    TEXT,
            module1_flags TEXT,
            updated_at    TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS compliance_data (
            user_id       INTEGER PRIMARY KEY,
            summary_json  TEXT,
            combined_csv  TEXT,
            updated_at    TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS gap_data (
            user_id       INTEGER PRIMARY KEY,
            gap_csv       TEXT,
            updated_at    TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS evidence_files (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            annex         TEXT    NOT NULL,
            control       TEXT    NOT NULL,
            file_name     TEXT    NOT NULL,
            file_ext      TEXT,
            evidence_type TEXT,
            notes         TEXT,
            file_bytes    BLOB,
            size_kb       REAL,
            uploaded_at   TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_evidence_user ON evidence_files(user_id);

        CREATE TABLE IF NOT EXISTS audit_events (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            timestamp     TEXT    NOT NULL,
            event_type    TEXT,
            action        TEXT,
            detail        TEXT,
            module        TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_events(user_id);

        CREATE TABLE IF NOT EXISTS compliance_history (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            recorded_at   TEXT    NOT NULL,
            percent       REAL,
            total         INTEGER,
            compliant     INTEGER,
            partial       INTEGER,
            non_compliant INTEGER,
            na            INTEGER,
            risk          TEXT,
            bank_level    TEXT,
            file_names    TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_history_user ON compliance_history(user_id);

        CREATE TABLE IF NOT EXISTS gap_history (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            recorded_at   TEXT    NOT NULL,
            total_gaps    INTEGER,
            high_gaps     INTEGER,
            medium_gaps   INTEGER,
            critical_gaps INTEGER,
            file_names    TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_gap_history_user ON gap_history(user_id);
        """)


# ══════════════════════════════════════════════════════════════════════════
#  PASSWORD UTILITIES
# ══════════════════════════════════════════════════════════════════════════

def _new_salt() -> str:
    return os.urandom(32).hex()


def _hash_password(password: str, salt: str) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        iterations=260_000,
        dklen=32,
    )
    return dk.hex()


def _verify_password(password: str, salt: str, stored_hash: str) -> bool:
    candidate = _hash_password(password, salt)
    return hmac.compare_digest(candidate, stored_hash)


# ══════════════════════════════════════════════════════════════════════════
#  USER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════

def create_user(username: str, password: str, role: str = "user") -> Dict:
    if len(username.strip()) < 3:
        return {"ok": False, "error": "Username must be at least 3 characters."}
    if len(password) < 6:
        return {"ok": False, "error": "Password must be at least 6 characters."}

    salt    = _new_salt()
    pw_hash = _hash_password(password, salt)
    now     = datetime.now().strftime("%d %b %Y  %H:%M:%S")

    try:
        with _conn() as con:
            cur = con.execute(
                "INSERT INTO users (username, password_hash, salt, role, created_at) VALUES (?,?,?,?,?)",
                (username.strip(), pw_hash, salt, role, now),
            )
            return {"ok": True, "user_id": cur.lastrowid}
    except Exception as e:
        msg = str(e)
        if "unique" in msg.lower() or "duplicate" in msg.lower():
            return {"ok": False, "error": f"Username '{username}' is already taken."}
        return {"ok": False, "error": msg}


def verify_login(username: str, password: str) -> Optional[Dict]:
    # Case-insensitive username lookup — works for both SQLite (COLLATE NOCASE) and PG (LOWER)
    sql = (
        "SELECT id, username, password_hash, salt, role FROM users WHERE LOWER(username) = LOWER(?)"
        if _IS_PG else
        "SELECT id, username, password_hash, salt, role FROM users WHERE username = ? COLLATE NOCASE"
    )
    with _conn() as con:
        row = _row(con.execute(sql, (username.strip(),)).fetchone())

    if not row:
        return None
    if not _verify_password(password, row["salt"], row["password_hash"]):
        return None

    now = datetime.now().strftime("%d %b %Y  %H:%M:%S")
    with _conn() as con:
        con.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, row["id"]))

    return {"id": row["id"], "username": row["username"], "role": row["role"]}


def get_all_users() -> List[Dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT id, username, role, created_at, last_login FROM users ORDER BY created_at DESC"
        ).fetchall()
    return [_row(r) for r in rows]


def delete_user(user_id: int) -> None:
    with _conn() as con:
        con.execute("DELETE FROM users WHERE id = ?", (user_id,))


def change_password(user_id: int, new_password: str) -> Dict:
    if len(new_password) < 6:
        return {"ok": False, "error": "Password must be at least 6 characters."}
    salt    = _new_salt()
    pw_hash = _hash_password(new_password, salt)
    with _conn() as con:
        con.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
            (pw_hash, salt, user_id),
        )
    return {"ok": True}


# ══════════════════════════════════════════════════════════════════════════
#  BANK PROFILE  (Module 1)
# ══════════════════════════════════════════════════════════════════════════

def save_bank_profile(user_id: int, bank_name: str, bank_level: str,
                      module1_flags: dict) -> None:
    now        = datetime.now().strftime("%d %b %Y  %H:%M:%S")
    flags_json = json.dumps(module1_flags)
    with _conn() as con:
        con.execute("""
            INSERT INTO bank_profiles (user_id, bank_name, bank_level, module1_flags, updated_at)
            VALUES (?,?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                bank_name     = excluded.bank_name,
                bank_level    = excluded.bank_level,
                module1_flags = excluded.module1_flags,
                updated_at    = excluded.updated_at
        """, (user_id, bank_name, bank_level, flags_json, now))


def load_bank_profile(user_id: int) -> Optional[Dict]:
    with _conn() as con:
        row = _row(con.execute(
            "SELECT * FROM bank_profiles WHERE user_id = ?", (user_id,)
        ).fetchone())
    if not row:
        return None
    try:
        row["module1_flags"] = json.loads(row.get("module1_flags") or "{}")
    except Exception:
        row["module1_flags"] = {}
    return row


# ══════════════════════════════════════════════════════════════════════════
#  COMPLIANCE DATA  (Module 3)
# ══════════════════════════════════════════════════════════════════════════

def save_compliance(user_id: int, summary: dict, combined_df: pd.DataFrame) -> None:
    now          = datetime.now().strftime("%d %b %Y  %H:%M:%S")
    summary_json = json.dumps(summary)
    csv_str      = combined_df.to_csv(index=False) if combined_df is not None else ""
    with _conn() as con:
        con.execute("""
            INSERT INTO compliance_data (user_id, summary_json, combined_csv, updated_at)
            VALUES (?,?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                summary_json = excluded.summary_json,
                combined_csv = excluded.combined_csv,
                updated_at   = excluded.updated_at
        """, (user_id, summary_json, csv_str, now))


def load_compliance(user_id: int) -> tuple:
    with _conn() as con:
        row = _row(con.execute(
            "SELECT * FROM compliance_data WHERE user_id = ?", (user_id,)
        ).fetchone())
    if not row:
        return None, None
    try:
        summary = json.loads(row["summary_json"])
        df      = pd.read_csv(io.StringIO(row["combined_csv"])) if row.get("combined_csv") else None
        return summary, df
    except Exception:
        return None, None


# ══════════════════════════════════════════════════════════════════════════
#  GAP DATA  (Module 4)
# ══════════════════════════════════════════════════════════════════════════

def save_gaps(user_id: int, gap_df: pd.DataFrame) -> None:
    now     = datetime.now().strftime("%d %b %Y  %H:%M:%S")
    csv_str = gap_df.to_csv(index=False) if gap_df is not None else ""
    with _conn() as con:
        con.execute("""
            INSERT INTO gap_data (user_id, gap_csv, updated_at)
            VALUES (?,?,?)
            ON CONFLICT(user_id) DO UPDATE SET
                gap_csv    = excluded.gap_csv,
                updated_at = excluded.updated_at
        """, (user_id, csv_str, now))


def load_gaps(user_id: int) -> Optional[pd.DataFrame]:
    with _conn() as con:
        row = _row(con.execute(
            "SELECT * FROM gap_data WHERE user_id = ?", (user_id,)
        ).fetchone())
    if not row or not row.get("gap_csv"):
        return None
    try:
        return pd.read_csv(io.StringIO(row["gap_csv"]))
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════
#  EVIDENCE FILES  (Module 8)
# ══════════════════════════════════════════════════════════════════════════

def save_evidence_entry(user_id: int, entry: dict) -> int:
    with _conn() as con:
        cur = con.execute("""
            INSERT INTO evidence_files
                (user_id, annex, control, file_name, file_ext,
                 evidence_type, notes, file_bytes, size_kb, uploaded_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            user_id,
            entry["annex"],
            entry["control"],
            entry["file_name"],
            entry.get("file_ext", ""),
            entry.get("evidence_type", ""),
            entry.get("notes", ""),
            entry.get("file_bytes", b""),
            entry.get("size_kb", 0),
            entry.get("uploaded_at", datetime.now().strftime("%d %b %Y  %H:%M:%S")),
        ))
        return cur.lastrowid


def delete_evidence_entry(db_id: int) -> None:
    with _conn() as con:
        con.execute("DELETE FROM evidence_files WHERE id = ?", (db_id,))


def load_evidence_store(user_id: int) -> dict:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM evidence_files WHERE user_id = ? ORDER BY uploaded_at ASC",
            (user_id,),
        ).fetchall()

    store = {}
    for r in rows:
        row = _row(r)
        key = f"{row['annex']}||{row['control']}"
        if key not in store:
            store[key] = []
        fb = row.get("file_bytes") or b""
        store[key].append({
            "annex":         row["annex"],
            "control":       row["control"],
            "file_name":     row["file_name"],
            "file_ext":      row.get("file_ext", ""),
            "evidence_type": row.get("evidence_type", ""),
            "notes":         row.get("notes", ""),
            "file_bytes":    bytes(fb) if fb else b"",
            "size_kb":       row.get("size_kb", 0),
            "uploaded_at":   row.get("uploaded_at", ""),
            "_db_id":        row["id"],
        })
    return store


def clear_evidence(user_id: int) -> None:
    with _conn() as con:
        con.execute("DELETE FROM evidence_files WHERE user_id = ?", (user_id,))


# ══════════════════════════════════════════════════════════════════════════
#  AUDIT LOG  (Module 6/7)
# ══════════════════════════════════════════════════════════════════════════

def save_audit_event(user_id: int, event: dict) -> None:
    with _conn() as con:
        con.execute("""
            INSERT INTO audit_events (user_id, timestamp, event_type, action, detail, module)
            VALUES (?,?,?,?,?,?)
        """, (
            user_id,
            event.get("timestamp", datetime.now().strftime("%d %b %Y  %H:%M:%S")),
            event.get("type", "system"),
            event.get("action", ""),
            event.get("detail", ""),
            event.get("module", "app"),
        ))


def load_audit_log(user_id: int) -> List[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM audit_events WHERE user_id = ? ORDER BY id ASC",
            (user_id,),
        ).fetchall()
    return [
        {
            "timestamp": _row(r)["timestamp"],
            "type":      _row(r)["event_type"],
            "action":    _row(r)["action"],
            "detail":    _row(r)["detail"],
            "module":    _row(r)["module"],
        }
        for r in rows
    ]


def clear_audit_log(user_id: int) -> None:
    with _conn() as con:
        con.execute("DELETE FROM audit_events WHERE user_id = ?", (user_id,))


def append_audit_event(user_id: int, event: dict) -> None:
    save_audit_event(user_id, event)


# ══════════════════════════════════════════════════════════════════════════
#  SESSION LOAD / SAVE HELPERS
# ══════════════════════════════════════════════════════════════════════════

def load_full_session(user_id: int) -> dict:
    state = {}
    profile = load_bank_profile(user_id)
    if profile:
        state["bank_name"]     = profile.get("bank_name", "")
        state["bank_level"]    = profile.get("bank_level", "")
        state["module1_flags"] = profile.get("module1_flags", {})
    summary, combined_df = load_compliance(user_id)
    if summary:
        state["compliance_summary"] = summary
    if combined_df is not None:
        state["combined_df"] = combined_df
    gap_df = load_gaps(user_id)
    if gap_df is not None:
        state["gap_dataframe"] = gap_df
    state["evidence_store"] = load_evidence_store(user_id)
    state["audit_log"]      = load_audit_log(user_id)
    return state


def save_full_session(user_id: int, ss: dict) -> None:
    bank_name  = ss.get("bank_name", "")
    bank_level = ss.get("bank_level", "")
    flags      = ss.get("module1_flags", {})
    if bank_name or bank_level:
        save_bank_profile(user_id, bank_name, bank_level, flags)
    summary     = ss.get("compliance_summary")
    combined_df = ss.get("combined_df")
    if summary:
        save_compliance(user_id, summary, combined_df)
    gap_df = ss.get("gap_dataframe")
    if gap_df is not None:
        save_gaps(user_id, gap_df)


# ══════════════════════════════════════════════════════════════════════════
#  COMPLIANCE HISTORY  (Trend Tracking)
# ══════════════════════════════════════════════════════════════════════════

def save_compliance_snapshot(user_id: int, summary: dict, file_names: list, bank_level: str) -> None:
    now = datetime.now().strftime("%d %b %Y  %H:%M:%S")
    with _conn() as con:
        con.execute("""
            INSERT INTO compliance_history
                (user_id, recorded_at, percent, total, compliant, partial,
                 non_compliant, na, risk, bank_level, file_names)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            user_id, now,
            summary.get("percent", 0), summary.get("total", 0),
            summary.get("compliant", 0), summary.get("partial", 0),
            summary.get("non", 0), summary.get("na", 0),
            summary.get("risk", ""), bank_level,
            json.dumps(file_names),
        ))


def load_compliance_history(user_id: int, limit: int = 20) -> List[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM compliance_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    result = []
    for r in reversed(rows):
        d = _row(r)
        result.append({
            "recorded_at":   d["recorded_at"],
            "percent":       d["percent"],
            "total":         d["total"],
            "compliant":     d["compliant"],
            "partial":       d["partial"],
            "non_compliant": d["non_compliant"],
            "na":            d["na"],
            "risk":          d["risk"],
            "bank_level":    d["bank_level"],
            "file_names":    json.loads(d.get("file_names") or "[]"),
        })
    return result


def clear_compliance_history(user_id: int) -> None:
    with _conn() as con:
        con.execute("DELETE FROM compliance_history WHERE user_id = ?", (user_id,))


def save_gap_snapshot(user_id: int, total: int, high: int, medium: int,
                      critical: int, file_names: list) -> None:
    now = datetime.now().strftime("%d %b %Y  %H:%M:%S")
    with _conn() as con:
        con.execute("""
            INSERT INTO gap_history
                (user_id, recorded_at, total_gaps, high_gaps,
                 medium_gaps, critical_gaps, file_names)
            VALUES (?,?,?,?,?,?,?)
        """, (user_id, now, total, high, medium, critical, json.dumps(file_names)))


def load_gap_history(user_id: int, limit: int = 20) -> List[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM gap_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    result = []
    for r in reversed(rows):
        d = _row(r)
        result.append({
            "recorded_at":   d["recorded_at"],
            "total_gaps":    d["total_gaps"],
            "high_gaps":     d["high_gaps"],
            "medium_gaps":   d["medium_gaps"],
            "critical_gaps": d["critical_gaps"],
            "file_names":    json.loads(d.get("file_names") or "[]"),
        })
    return result


def clear_gap_history(user_id: int) -> None:
    with _conn() as con:
        con.execute("DELETE FROM gap_history WHERE user_id = ?", (user_id,))


# ══════════════════════════════════════════════════════════════════════════
#  ADMIN STATS
# ══════════════════════════════════════════════════════════════════════════

def admin_stats() -> dict:
    with _conn() as con:
        users      = _row(con.execute("SELECT COUNT(*) AS c FROM users").fetchone()).get("c", 0)
        profiles   = _row(con.execute("SELECT COUNT(*) AS c FROM bank_profiles").fetchone()).get("c", 0)
        evidence   = _row(con.execute("SELECT COUNT(*) AS c FROM evidence_files").fetchone()).get("c", 0)
        audit_evts = _row(con.execute("SELECT COUNT(*) AS c FROM audit_events").fetchone()).get("c", 0)
        ev_size    = _row(con.execute(
            "SELECT COALESCE(SUM(size_kb),0) AS s FROM evidence_files"
        ).fetchone()).get("s", 0)
    return {
        "total_users":    users,
        "active_banks":   profiles,
        "evidence_files": evidence,
        "audit_events":   audit_evts,
        "evidence_mb":    round(float(ev_size) / 1024, 2),
    }