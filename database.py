"""
EcoPulse Database Persistence Module
Lightweight, thread-safe SQLite persistence for sustainability logs and historical tracking.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from config import Config
from calculations import calculate_total_footprint

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Creates a connection to SQLite with row dictionary factory."""
    path = db_path if db_path is not None else Config.DATABASE_PATH
    conn = sqlite3.connect(path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[str] = None) -> None:
    """Initializes the database schema if not already present."""
    conn = get_connection(db_path)
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    total_tonnes REAL NOT NULL,
                    total_kg REAL NOT NULL,
                    transport_kg REAL NOT NULL,
                    energy_kg REAL NOT NULL,
                    waste_kg REAL NOT NULL,
                    other_kg REAL NOT NULL,
                    data_json TEXT NOT NULL
                );
            """)
    finally:
        conn.close()

def get_all_entries(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all assessment entries sorted chronologically."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entries ORDER BY id ASC;")
        rows = cursor.fetchall()
        entries = []
        for r in rows:
            entry = dict(r)
            try:
                entry["inputs"] = json.loads(r["data_json"])
            except Exception:
                entry["inputs"] = {}
            entries.append(entry)
        return entries
    finally:
        conn.close()

def get_entry_by_id(entry_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves a single entry by its ID, with parsed inputs and fresh calculations."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entries WHERE id = ?;", (entry_id,))
        row = cursor.fetchone()
        if not row:
            return None
        entry = dict(row)
        try:
            inputs = json.loads(row["data_json"])
        except Exception:
            inputs = {}
        entry["inputs"] = inputs
        entry["calculations"] = calculate_total_footprint(inputs)
        return entry
    finally:
        conn.close()

def get_latest_entry(db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves the most recently created or updated entry."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entries ORDER BY id DESC LIMIT 1;")
        row = cursor.fetchone()
        if not row:
            return None
        entry = dict(row)
        try:
            inputs = json.loads(row["data_json"])
        except Exception:
            inputs = {}
        entry["inputs"] = inputs
        entry["calculations"] = calculate_total_footprint(inputs)
        return entry
    finally:
        conn.close()

def create_entry(inputs: Dict[str, Any], title: Optional[str] = None, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Computes carbon footprint and saves a new log entry to SQLite."""
    conn = get_connection(db_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    calc = calculate_total_footprint(inputs)
    cleaned_inputs = calc["inputs"]
    data_json = json.dumps(cleaned_inputs)

    try:
        with conn:
            cursor = conn.cursor()
            # If no custom title provided, determine default title e.g. "Log #N"
            if not title:
                cursor.execute("SELECT COUNT(*) FROM entries;")
                count = cursor.fetchone()[0]
                title = f"Log #{count + 1}"

            cursor.execute("""
                INSERT INTO entries (
                    title, created_at, updated_at, total_tonnes, total_kg,
                    transport_kg, energy_kg, waste_kg, other_kg, data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                title,
                now,
                now,
                calc["total_tonnes"],
                calc["total_kg"],
                calc["breakdown"]["transportation"]["kg"],
                calc["breakdown"]["energy"]["kg"],
                calc["breakdown"]["waste"]["kg"],
                calc["breakdown"]["other"]["kg"],
                data_json
            ))
            new_id = cursor.lastrowid

        return get_entry_by_id(new_id, db_path)
    finally:
        conn.close()

def update_entry(entry_id: int, inputs: Dict[str, Any], title: Optional[str] = None, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Recalculates metrics and updates an existing entry in SQLite."""
    conn = get_connection(db_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    calc = calculate_total_footprint(inputs)
    cleaned_inputs = calc["inputs"]
    data_json = json.dumps(cleaned_inputs)

    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title FROM entries WHERE id = ?;", (entry_id,))
            existing = cursor.fetchone()
            if not existing:
                return None

            assigned_title = title if title else existing["title"]

            cursor.execute("""
                UPDATE entries SET
                    title = ?,
                    updated_at = ?,
                    total_tonnes = ?,
                    total_kg = ?,
                    transport_kg = ?,
                    energy_kg = ?,
                    waste_kg = ?,
                    other_kg = ?,
                    data_json = ?
                WHERE id = ?;
            """, (
                assigned_title,
                now,
                calc["total_tonnes"],
                calc["total_kg"],
                calc["breakdown"]["transportation"]["kg"],
                calc["breakdown"]["energy"]["kg"],
                calc["breakdown"]["waste"]["kg"],
                calc["breakdown"]["other"]["kg"],
                data_json,
                entry_id
            ))

        return get_entry_by_id(entry_id, db_path)
    finally:
        conn.close()

def delete_entry(entry_id: int, db_path: Optional[str] = None) -> bool:
    """Deletes an entry by ID from SQLite."""
    conn = get_connection(db_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM entries WHERE id = ?;", (entry_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()

def get_history_summary(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves lightweight timeline data for rendering the history chart."""
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, created_at, total_tonnes FROM entries ORDER BY id ASC;")
        rows = cursor.fetchall()
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "created_at": r["created_at"],
                "total_tonnes": round(r["total_tonnes"], 2)
            }
            for r in rows
        ]
    finally:
        conn.close()
