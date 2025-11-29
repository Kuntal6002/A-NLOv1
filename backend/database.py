# backend/database.py
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

DB_PATH = Path(__file__).resolve().parent / "anlo.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def dict_row(cursor: sqlite3.Cursor, row: sqlite3.Row) -> Dict[str, Any]:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS balances (
            date TEXT PRIMARY KEY,
            balance REAL NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_logs (
            cycle INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            state TEXT NOT NULL,
            plan TEXT NOT NULL,
            result TEXT NOT NULL,
            reward REAL NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            cash REAL NOT NULL,
            positions_json TEXT NOT NULL
        )
        """
    )

    # Ensure single portfolio row
    cur.execute("SELECT COUNT(*) AS c FROM portfolio")
    c = cur.fetchone()[0]
    if c == 0:
        cur.execute(
            "INSERT INTO portfolio (id, cash, positions_json) VALUES (1, ?, ?)",
            (10000.0, "{}"),
        )

    conn.commit()
    conn.close()


def reset_db() -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS transactions")
    cur.execute("DROP TABLE IF EXISTS balances")
    cur.execute("DROP TABLE IF EXISTS agent_logs")
    cur.execute("DROP TABLE IF EXISTS portfolio")
    conn.commit()
    conn.close()
    init_db()


def fetch_all(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    conn = get_connection()
    conn.row_factory = dict_row
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def fetch_one(query: str, params: tuple = ()) -> Dict[str, Any] | None:
    conn = get_connection()
    conn.row_factory = dict_row
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return row


def execute(query: str, params: tuple = ()) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    conn.close()
