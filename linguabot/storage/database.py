"""Camada de acesso ao banco SQLite com migrações automáticas."""

from __future__ import annotations

import logging
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Sequence

from .schema import MIGRATIONS

logger = logging.getLogger(__name__)


class Database:
    """Conexão SQLite com migrações versionadas e acesso thread-safe.

    Uma única conexão é compartilhada; o acesso é serializado por um lock, o
    que é suficiente para a carga típica de um bot de Telegram.
    """

    def __init__(self, path: str = ":memory:") -> None:
        self.path = path
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    def connect(self) -> sqlite3.Connection:
        if self._conn is not None:
            return self._conn

        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        if self.path != ":memory:":
            conn.execute("PRAGMA journal_mode = WAL")
        self._conn = conn
        return conn

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn or self.connect()

    # ------------------------------------------------------------------
    def initialize(self) -> None:
        """Cria as tabelas e aplica as migrações pendentes."""

        with self._lock:
            conn = self.connect()
            conn.execute(
                "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            conn.commit()
            current = self._current_version()
            for migration in MIGRATIONS:
                if migration.version <= current:
                    continue
                logger.info(
                    "Aplicando migração %s - %s", migration.version, migration.name
                )
                try:
                    for statement in migration.statements:
                        conn.execute(statement)
                    conn.execute(
                        "INSERT INTO meta (key, value) VALUES ('schema_version', ?) "
                        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                        (str(migration.version),),
                    )
                    conn.commit()
                except sqlite3.Error:
                    conn.rollback()
                    raise

    def _current_version(self) -> int:
        row = self.conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()
        return int(row["value"]) if row else 0

    # ------------------------------------------------------------------
    def execute(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Cursor:
        with self._lock:
            cursor = self.conn.execute(sql, params)
            self.conn.commit()
            return cursor

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[sqlite3.Row]:
        with self._lock:
            return list(self.conn.execute(sql, params).fetchall())

    def query_one(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Row | None:
        with self._lock:
            return self.conn.execute(sql, params).fetchone()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            try:
                yield self.conn
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

    # ------------------------------------------------------------------
    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
