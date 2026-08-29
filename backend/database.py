#!/usr/bin/env python3
"""
SIH26170 - Backend SQLite Storage Layer
=============================================================================
Manages persistent storage for all semiconductor screening transactions,
raw & scaled inputs, model predictions, user ground truth, discrepancy metrics,
and AI chatbot diagnostic explanations.
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Default database location
DEFAULT_DB_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "screening.db"


class ScreeningDatabase:
    """SQLite Database manager for screening records and chat interactions."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self._ensure_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_db(self):
        """Create database directory and tables if they do not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Table 1: Screenings and Discrepancy Records
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS screenings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    component_id TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    raw_input REAL NOT NULL,
                    scaled_input REAL NOT NULL,
                    scaled_output REAL NOT NULL,
                    physical_output REAL NOT NULL,
                    user_said_output REAL,
                    delta REAL,
                    pct_diff REAL,
                    ratio REAL,
                    direction TEXT,
                    risk_decision TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    physics_causes TEXT,
                    recommendations TEXT,
                    chatbot_explanation TEXT,
                    ai_provider TEXT
                )
            """)

            # Table 2: Conversational Chat Logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL,
                    screening_id INTEGER,
                    FOREIGN KEY (screening_id) REFERENCES screenings(id)
                )
            """)

            conn.commit()

    def save_screening(self, data: Dict[str, Any]) -> int:
        """
        Insert a complete screening transaction into the database.
        Returns the inserted row ID.
        """
        now = datetime.now().isoformat()
        causes_json = json.dumps(data.get("physics_causes", []))
        recs_json = json.dumps(data.get("recommendations", []))

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO screenings (
                    timestamp, component_id, model_type, raw_input, scaled_input,
                    scaled_output, physical_output, user_said_output, delta, pct_diff,
                    ratio, direction, risk_decision, severity, physics_causes,
                    recommendations, chatbot_explanation, ai_provider
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("timestamp", now),
                data.get("component_id", "DUT-01"),
                data.get("model_type", "breakdown"),
                float(data.get("raw_input", 0.0)),
                float(data.get("scaled_input", 0.0)),
                float(data.get("scaled_output", 0.0)),
                float(data.get("physical_output", 0.0)),
                float(data["user_said_output"]) if data.get("user_said_output") is not None else None,
                float(data["delta"]) if data.get("delta") is not None else None,
                float(data["pct_diff"]) if data.get("pct_diff") is not None else None,
                float(data["ratio"]) if data.get("ratio") is not None else None,
                data.get("direction", "NOMINAL"),
                data.get("risk_decision", "PASS"),
                data.get("severity", "LOW"),
                causes_json,
                recs_json,
                data.get("chatbot_explanation", ""),
                data.get("ai_provider", "offline")
            ))
            conn.commit()
            return cursor.lastrowid

    def get_screenings(
        self,
        limit: int = 50,
        offset: int = 0,
        model_type: Optional[str] = None,
        risk_decision: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve historical screening records with optional filtering."""
        query = "SELECT * FROM screenings WHERE 1=1"
        params: List[Any] = []

        if model_type:
            query += " AND model_type = ?"
            params.append(model_type)
        if risk_decision:
            query += " AND risk_decision = ?"
            params.append(risk_decision)

        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                d = dict(row)
                try:
                    d["physics_causes"] = json.loads(d.get("physics_causes") or "[]")
                except json.JSONDecodeError:
                    d["physics_causes"] = []
                try:
                    d["recommendations"] = json.loads(d.get("recommendations") or "[]")
                except json.JSONDecodeError:
                    d["recommendations"] = []
                results.append(d)
            return results

    def get_screening_by_id(self, screening_id: int) -> Optional[Dict[str, Any]]:
        """Fetch single screening record by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM screenings WHERE id = ?", (screening_id,))
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            try:
                d["physics_causes"] = json.loads(d.get("physics_causes") or "[]")
                d["recommendations"] = json.loads(d.get("recommendations") or "[]")
            except:
                pass
            return d

    def save_chat_message(
        self,
        session_id: str,
        role: str,
        message: str,
        screening_id: Optional[int] = None
    ) -> int:
        """Save chat conversation message to database."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_logs (timestamp, session_id, role, message, screening_id)
                VALUES (?, ?, ?, ?, ?)
            """, (now, session_id, role, message, screening_id))
            conn.commit()
            return cursor.lastrowid

    def get_chat_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent chat history for a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM chat_logs WHERE session_id = ?
                ORDER BY id ASC LIMIT ?
            """, (session_id, limit))
            return [dict(r) for r in cursor.fetchall()]

    def get_summary_stats(self) -> Dict[str, Any]:
        """Compute aggregate statistics on stored screenings."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM screenings")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT risk_decision, COUNT(*) FROM screenings GROUP BY risk_decision")
            decisions = {r[0]: r[1] for r in cursor.fetchall()}

            return {
                "total_screenings": total,
                "pass_count": decisions.get("PASS", 0),
                "hold_count": decisions.get("HOLD", 0),
                "reject_count": decisions.get("REJECT", 0)
            }
