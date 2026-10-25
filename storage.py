import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

DB_FILE = "phoenix_workspace.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            domain_name TEXT,
            active_version TEXT,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS test_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            version_label TEXT,
            passed INTEGER,
            failed INTEGER,
            results_json TEXT,
            timestamp TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS resurrection_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            report_md TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_project_state(project_id: str, domain_name: str, active_version: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO projects (project_id, domain_name, active_version, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(project_id) DO UPDATE SET
            domain_name=excluded.domain_name,
            active_version=excluded.active_version
    """, (project_id, domain_name, active_version, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def log_test_run(project_id: str, version_label: str, passed: int, failed: int, results: List[Dict[str, Any]]):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO test_runs (project_id, version_label, passed, failed, results_json, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (project_id, version_label, passed, failed, json.dumps(results), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def save_report(project_id: str, report_md: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO resurrection_reports (project_id, report_md, created_at)
        VALUES (?, ?, ?)
    """, (project_id, report_md, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
