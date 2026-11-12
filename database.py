import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from backend.config import ROOT_DIR, MONGODB_URI, MONGODB_DATABASE

DB_PATH = ROOT_DIR / "data" / "claims.db"

def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                claim_id TEXT PRIMARY KEY,
                patient_name TEXT,
                policy_number TEXT,
                hospital_name TEXT,
                claim_amount REAL,
                claim_date TEXT,
                diagnosis TEXT,
                extracted_text TEXT,
                summary TEXT,
                status TEXT,
                flags TEXT,
                source_filename TEXT,
                created_at TEXT
            )
        """)

def save_claim(claim: dict[str, Any]) -> str:
    init_db()
    created_at = datetime.now(timezone.utc).isoformat()
    values = (
        claim["claim_id"], claim.get("patient_name"), claim.get("policy_number"),
        claim.get("hospital_name"), claim.get("claim_amount"), claim.get("claim_date"),
        claim.get("diagnosis"), claim.get("extracted_text", ""), claim.get("summary", ""),
        claim.get("status", "Needs review"), json.dumps(claim.get("flags", [])),
        claim.get("source_filename"), created_at
    )
    with _connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO claims VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)

    # Optional MongoDB mirror. SQLite remains the reliable local fallback.
    if MONGODB_URI:
        try:
            from pymongo import MongoClient
            client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2500)
            doc = dict(claim)
            doc["created_at"] = created_at
            client[MONGODB_DATABASE]["claims"].replace_one(
                {"claim_id": claim["claim_id"]}, doc, upsert=True
            )
            client.close()
        except Exception:
            pass
    return claim["claim_id"]

def list_claims(limit: int = 200):
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT claim_id, patient_name, policy_number, hospital_name, claim_amount, claim_date, diagnosis, summary, status, flags, source_filename, created_at FROM claims ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    results = []
    for row in rows:
        item = dict(row)
        item["flags"] = json.loads(item["flags"] or "[]")
        results.append(item)
    return results

def get_claim(claim_id: str):
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM claims WHERE claim_id = ?", (claim_id,)).fetchone()
    if not row:
        return None
    item = dict(row)
    item["flags"] = json.loads(item["flags"] or "[]")
    return item

def delete_claim(claim_id: str):
    init_db()
    with _connect() as conn:
        cur = conn.execute("DELETE FROM claims WHERE claim_id = ?", (claim_id,))
        return cur.rowcount > 0
