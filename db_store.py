import sqlite3
import hashlib
import hmac
import os
import json
from datetime import datetime

import pandas as pd

# ─────────────────────────────────────────────
# DB CONFIG
# ─────────────────────────────────────────────

_SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rbi_csf_data.db")


def _get_url():
    # 1. Local env
    url = os.environ.get("RBI_DB_PATH", "")

    # 2. Streamlit secrets
    try:
        import streamlit as st
        url = st.secrets.get("RBI_DB_PATH", url)
    except Exception:
        pass

    url = str(url).strip()

    print("🚀 DB URL DETECTED:", url)   # DEBUG

    return url


def _is_pg():
    return _get_url().startswith("postgres")


# ─────────────────────────────────────────────
# POSTGRES WRAPPER
# ─────────────────────────────────────────────

class _PGCursor:
    def __init__(self, cur):
        self._c = cur
        self.lastrowid = None

    def fetchone(self):
        r = self._c.fetchone()
        return dict(r) if r else None

    def fetchall(self):
        return [dict(r) for r in self._c.fetchall()]


class _PGConn:
    def __init__(self):
        import psycopg2
        import psycopg2.extras

        url = _get_url()

        if not url:
            raise Exception("❌ DATABASE URL NOT FOUND")

        self._raw = psycopg2.connect(
            url,
            cursor_factory=psycopg2.extras.RealDictCursor
        )

    def execute(self, sql, params=()):
        cur = self._raw.cursor()

        # Convert SQLite → PostgreSQL syntax
        sql = sql.replace("?", "%s")
        sql = sql.replace("AUTOINCREMENT", "")
        sql = sql.replace("INTEGER PRIMARY KEY", "SERIAL PRIMARY KEY")
        sql = sql.replace("BLOB", "BYTEA")
        sql = sql.replace("COLLATE NOCASE", "")

        print("🔹 EXEC SQL:", sql)   # DEBUG

        cur.execute(sql, params or ())

        wrapper = _PGCursor(cur)

        if sql.strip().upper().startswith("INSERT"):
            try:
                row = cur.fetchone()
                wrapper.lastrowid = row["id"] if row else None
            except:
                pass

        return wrapper

    def executescript(self, script):
        cur = self._raw.cursor()

        statements = [s.strip() for s in script.split(";") if s.strip()]

        for stmt in statements:
            try:
                stmt = stmt.replace("?", "%s")
                stmt = stmt.replace("AUTOINCREMENT", "")
                stmt = stmt.replace("INTEGER PRIMARY KEY", "SERIAL PRIMARY KEY")
                stmt = stmt.replace("BLOB", "BYTEA")
                stmt = stmt.replace("COLLATE NOCASE", "")

                print("🔹 RUN:", stmt)  # DEBUG

                cur.execute(stmt)
            except Exception as e:
                print("❌ FAILED:", stmt)
                print("ERROR:", e)
                raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_):
        if exc_type is None:
            self._raw.commit()
        else:
            self._raw.rollback()
        self._raw.close()


# ─────────────────────────────────────────────
# CONNECTION HANDLER
# ─────────────────────────────────────────────

def _conn():
    if _is_pg():
        return _PGConn()

    con = sqlite3.connect(_SQLITE_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


# ─────────────────────────────────────────────
# INIT DB
# ─────────────────────────────────────────────

def init_db():
    with _conn() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TEXT,
            last_login TEXT
        );

        CREATE TABLE IF NOT EXISTS bank_profiles (
            user_id INTEGER PRIMARY KEY,
            bank_name TEXT,
            bank_level TEXT,
            module1_flags TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS compliance_data (
            user_id INTEGER PRIMARY KEY,
            summary_json TEXT,
            combined_csv TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS gap_data (
            user_id INTEGER PRIMARY KEY,
            gap_csv TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS evidence_files (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            annex TEXT,
            control TEXT,
            file_name TEXT,
            file_ext TEXT,
            evidence_type TEXT,
            notes TEXT,
            file_bytes BYTEA,
            size_kb REAL,
            uploaded_at TEXT
        );

        CREATE TABLE IF NOT EXISTS audit_events (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            timestamp TEXT,
            event_type TEXT,
            action TEXT,
            detail TEXT,
            module TEXT
        );
        """)


# ─────────────────────────────────────────────
# PASSWORD FUNCTIONS
# ─────────────────────────────────────────────

def _new_salt():
    return os.urandom(32).hex()


def _hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        bytes.fromhex(salt),
        260000
    ).hex()


def _verify_password(password, salt, stored):
    return hmac.compare_digest(_hash_password(password, salt), stored)