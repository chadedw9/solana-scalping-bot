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

CREATE TABLE IF NOT EXISTS wallets (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id        INTEGER NOT NULL,
    address        TEXT    NOT NULL,
    label          TEXT    NOT NULL DEFAULT '',
    last_signature TEXT,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (chat_id, address)
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


@dataclass
class Wallet:
    id: int
    chat_id: int
    address: str
    label: str
    last_signature: str | None


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

    # --- Wallet tracking ---

    def add_wallet(self, chat_id: int, address: str, label: str, last_signature: str | None) -> int:
        """Insert (or update) a watched wallet. Returns its row id.

        Re-watching the same address just refreshes the label/baseline rather
        than creating a duplicate.
        """
        self._conn.execute(
            "INSERT INTO wallets (chat_id, address, label, last_signature) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT (chat_id, address) DO UPDATE SET "
            "label = excluded.label, last_signature = excluded.last_signature",
            (chat_id, address, label, last_signature),
        )
        self._conn.commit()
        row = self._conn.execute(
            "SELECT id FROM wallets WHERE chat_id = ? AND address = ?", (chat_id, address)
        ).fetchone()
        return int(row["id"])

    def list_wallets(self, chat_id: int) -> list[Wallet]:
        rows = self._conn.execute(
            "SELECT * FROM wallets WHERE chat_id = ? ORDER BY id", (chat_id,)
        ).fetchall()
        return [self._row_to_wallet(r) for r in rows]

    def all_wallets(self) -> list[Wallet]:
        rows = self._conn.execute("SELECT * FROM wallets ORDER BY id").fetchall()
        return [self._row_to_wallet(r) for r in rows]

    def remove_wallet(self, chat_id: int, wallet_id: int) -> bool:
        cur = self._conn.execute(
            "DELETE FROM wallets WHERE id = ? AND chat_id = ?", (wallet_id, chat_id)
        )
        self._conn.commit()
        return cur.rowcount > 0

    def update_wallet_signature(self, wallet_id: int, last_signature: str | None) -> None:
        self._conn.execute(
            "UPDATE wallets SET last_signature = ? WHERE id = ?", (last_signature, wallet_id)
        )
        self._conn.commit()

    @staticmethod
    def _row_to_wallet(row: sqlite3.Row) -> Wallet:
        return Wallet(
            id=row["id"],
            chat_id=row["chat_id"],
            address=row["address"],
            label=row["label"],
            last_signature=row["last_signature"],
        )
