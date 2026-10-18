"""SQLite persistence for the human-gated local prototype."""
import json
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.getenv("DATABASE_PATH", "./data/prototype.db")

def now():
    return datetime.now(timezone.utc).isoformat()

def connect():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db

def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
          id TEXT PRIMARY KEY, brand TEXT NOT NULL, handle TEXT NOT NULL UNIQUE,
          profile_name TEXT, bio TEXT, profile_link TEXT, category TEXT, image_ref TEXT,
          owner TEXT NOT NULL, recovery_email TEXT, recovery_phone TEXT,
          two_factor_method TEXT, two_factor_enabled INTEGER NOT NULL DEFAULT 0,
          backup_codes_in_vault INTEGER NOT NULL DEFAULT 0, vault_refs TEXT NOT NULL DEFAULT '[]',
          people_roles TEXT NOT NULL DEFAULT '[]', status TEXT NOT NULL,
          blockers TEXT NOT NULL DEFAULT '[]', last_verified_at TEXT,
          evidence_label TEXT NOT NULL DEFAULT 'unverified', updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tasks (
          id TEXT PRIMARY KEY, idempotency_key TEXT NOT NULL UNIQUE, account_id TEXT,
          title TEXT NOT NULL, owner TEXT NOT NULL, due_at TEXT, status TEXT NOT NULL,
          instructions TEXT NOT NULL, evidence TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          FOREIGN KEY(account_id) REFERENCES accounts(id)
        );
        CREATE TABLE IF NOT EXISTS findings (
          id TEXT PRIMARY KEY, account_id TEXT NOT NULL, finding_type TEXT NOT NULL,
          severity TEXT NOT NULL, label TEXT NOT NULL, evidence TEXT NOT NULL,
          remediation_status TEXT NOT NULL, created_at TEXT NOT NULL,
          FOREIGN KEY(account_id) REFERENCES accounts(id)
        );
        CREATE TABLE IF NOT EXISTS audit_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT NOT NULL, correlation_id TEXT,
          details TEXT NOT NULL, created_at TEXT NOT NULL
        );
        """)
        # Additive migration for databases created by an earlier prototype version.
        existing={row[1] for row in db.execute("PRAGMA table_info(accounts)").fetchall()}
        for column in ("profile_name","bio","profile_link","category","image_ref"):
            if column not in existing:
                db.execute(f"ALTER TABLE accounts ADD COLUMN {column} TEXT")

def record_event(event, details, correlation_id=None):
    with connect() as db:
        db.execute("INSERT INTO audit_events(event,correlation_id,details,created_at) VALUES(?,?,?,?)",
                   (event, correlation_id, json.dumps(details), now()))

def seed_demo():
    """Seed clearly synthetic fixtures once; never indicates live access."""
    init_db()
    with connect() as db:
        if db.execute("SELECT count(*) FROM accounts").fetchone()[0]:
            return
        rows = [
          ("demo-clean", "Northstar Test Brand", "northstar_test_demo", "Demo Northstar", "Sample company bio", "https://example.invalid", "Sample category", "brand-image-ref://synthetic", "Test Owner", "owner@company.example.invalid", "+1-XXX-XXX-0101", "authenticator_app", 1, 1, '["vault://demo/account-password","vault://demo/backup-codes"]', '[{"person":"Test Operator","role":"Analyst"}]', "ready_for_human_review", "[]", now(), "unverified"),
          ("demo-findings", "Orchid Test Brand", "orchid_test_demo", "Demo Orchid", "Sample bio", "https://example.invalid", "Sample category", "brand-image-ref://synthetic", "Test Owner", "personal@example.invalid", None, "", 0, 0, '["vault://demo/account-password"]', '[{"person":"Departing Member","role":"Admin","last_verified":"2025-01-01"}]', "blocked", '["Company test environment access not supplied"]', None, "unverified")
        ]
        for a in rows:
            db.execute("INSERT INTO accounts(id,brand,handle,profile_name,bio,profile_link,category,image_ref,owner,recovery_email,recovery_phone,two_factor_method,two_factor_enabled,backup_codes_in_vault,vault_refs,people_roles,status,blockers,last_verified_at,evidence_label,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (*a, now()))
    record_event("demo_seeded", {"classification":"synthetic", "records":2})
