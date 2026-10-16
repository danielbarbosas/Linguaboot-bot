"""Definição das migrações do banco de dados (SQLite).

Cada migração tem uma versão incremental e é aplicada uma única vez. Nunca
edite uma migração já publicada: adicione uma nova versão.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    statements: tuple[str, ...]


MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version=1,
        name="criacao_inicial",
        statements=(
            """
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id     INTEGER NOT NULL UNIQUE,
                username        TEXT,
                first_name      TEXT,
                ui_lang         TEXT NOT NULL DEFAULT 'pt',
                learn_lang      TEXT,
                level           TEXT,
                voice           TEXT NOT NULL DEFAULT 'feminino',
                profile         TEXT NOT NULL DEFAULT 'adulto',
                modality        TEXT,
                correction_mode TEXT NOT NULL DEFAULT 'imediata',
                goal            TEXT,
                kids_consent    INTEGER NOT NULL DEFAULT 0,
                onboarded       INTEGER NOT NULL DEFAULT 0,
                run_key         TEXT NOT NULL DEFAULT 'default',
                xp              INTEGER NOT NULL DEFAULT 0,
                streak          INTEGER NOT NULL DEFAULT 0,
                last_activity   TEXT,
                created_at      TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sessions (
                telegram_id    INTEGER PRIMARY KEY,
                mode           TEXT,
                module         TEXT,
                lesson_id      TEXT,
                exercise_index INTEGER NOT NULL DEFAULT 0,
                current_item   TEXT NOT NULL DEFAULT '{}',
                awaiting       TEXT,
                updated_at     TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (telegram_id) REFERENCES users (telegram_id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS progress (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id  INTEGER NOT NULL,
                learn_lang   TEXT NOT NULL,
                run_key      TEXT NOT NULL DEFAULT 'default',
                module       TEXT NOT NULL,
                item_id      TEXT NOT NULL,
                status       TEXT NOT NULL DEFAULT 'started',
                score        REAL NOT NULL DEFAULT 0,
                attempts     INTEGER NOT NULL DEFAULT 0,
                updated_at   TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (telegram_id, run_key, module, item_id),
                FOREIGN KEY (telegram_id) REFERENCES users (telegram_id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS assessments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                learn_lang  TEXT NOT NULL,
                run_key     TEXT NOT NULL DEFAULT 'default',
                kind        TEXT NOT NULL,
                score       REAL NOT NULL DEFAULT 0,
                total       INTEGER NOT NULL DEFAULT 0,
                details     TEXT NOT NULL DEFAULT '{}',
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (telegram_id) REFERENCES users (telegram_id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS consents (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                kind        TEXT NOT NULL,
                granted     INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE (telegram_id, kind),
                FOREIGN KEY (telegram_id) REFERENCES users (telegram_id) ON DELETE CASCADE
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_progress_user ON progress (telegram_id, learn_lang)",
            "CREATE INDEX IF NOT EXISTS idx_assessments_user ON assessments (telegram_id, learn_lang)",
        ),
    ),
)
