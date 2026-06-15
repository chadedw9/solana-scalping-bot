"""SQLite persistence for price alerts.

Kept deliberately small: the standard-library sqlite3 module is plenty for a
single-process bot, and alerts survive restarts so users don't lose them.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

_SCHEMA = """
CREATE TABLE IF NOT EXISTS alerts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id      INTEGER NOT NULL,
    query        TEXT    NOT NULL,
    symbol       TEXT    NOT NULL,
    direction    TEXT    NOT NULL CHECK (direction IN ('above', 'below')),
    target_price REAL    NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


@dataclass
class Alert:
    id: int
    chat_id: int
    query: str
    symbol: str
    direction: str
    target_price: float


class Storage:
    def __init__(self, path: str) -> None:
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def add_alert(
        self, chat_id: int, query: str, symbol: str, direction: str, target_price: float
    ) -> int:
        cur = self._conn.execute(
            "INSERT INTO alerts (chat_id, query, symbol, direction, target_price) "
            "VALUES (?, ?, ?, ?, ?)",
            (chat_id, query, symbol, direction, target_price),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def list_alerts(self, chat_id: int) -> list[Alert]:
        rows = self._conn.execute(
            "SELECT * FROM alerts WHERE chat_id = ? ORDER BY id", (chat_id,)
        ).fetchall()
        return [self._row_to_alert(r) for r in rows]

    def all_alerts(self) -> list[Alert]:
        rows = self._conn.execute("SELECT * FROM alerts ORDER BY id").fetchall()
        return [self._row_to_alert(r) for r in rows]

    def remove_alert(self, chat_id: int, alert_id: int) -> bool:
        cur = self._conn.execute(
            "DELETE FROM alerts WHERE id = ? AND chat_id = ?", (alert_id, chat_id)
        )
        self._conn.commit()
        return cur.rowcount > 0

    def delete_alert(self, alert_id: int) -> None:
        self._conn.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
        self._conn.commit()

    @staticmethod
    def _row_to_alert(row: sqlite3.Row) -> Alert:
        return Alert(
            id=row["id"],
            chat_id=row["chat_id"],
            query=row["query"],
            symbol=row["symbol"],
            direction=row["direction"],
            target_price=row["target_price"],
        )
