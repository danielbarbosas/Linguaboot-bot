"""Repositórios: acesso tipado às tabelas do banco."""

from __future__ import annotations

import json
from typing import Any

from ..models import (
    CorrectionMode,
    LearnLang,
    LearningSession,
    Level,
    Modality,
    Profile,
    UILang,
    UserProfileData,
    Voice,
)
from .database import Database

_UPDATABLE_FIELDS = {
    "ui_lang",
    "learn_lang",
    "level",
    "voice",
    "profile",
    "modality",
    "correction_mode",
    "goal",
    "kids_consent",
    "onboarded",
    "run_key",
}


class UserRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    # ------------------------------------------------------------------
    def ensure_user(
        self,
        telegram_id: int,
        *,
        username: str | None = None,
        first_name: str | None = None,
        default_ui_lang: str = "pt",
    ) -> None:
        self.db.execute(
            """
            INSERT INTO users (telegram_id, username, first_name, ui_lang)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (telegram_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_activity = datetime('now'),
                updated_at = datetime('now')
            """,
            (telegram_id, username, first_name, default_ui_lang),
        )

    def get(self, telegram_id: int):
        return self.db.query_one(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )

    def get_profile(self, telegram_id: int) -> UserProfileData | None:
        row = self.get(telegram_id)
        if row is None:
            return None
        return self._row_to_profile(row)

    @staticmethod
    def _row_to_profile(row) -> UserProfileData:
        def _enum(value, enum_cls, default=None):
            if value is None:
                return default
            try:
                return enum_cls(value)
            except ValueError:
                return default

        return UserProfileData(
            telegram_id=row["telegram_id"],
            ui_lang=_enum(row["ui_lang"], UILang, UILang.PT),
            learn_lang=_enum(row["learn_lang"], LearnLang),
            level=_enum(row["level"], Level),
            voice=_enum(row["voice"], Voice, Voice.FEMININO),
            profile=_enum(row["profile"], Profile, Profile.ADULTO),
            modality=_enum(row["modality"], Modality),
            correction_mode=_enum(
                row["correction_mode"], CorrectionMode, CorrectionMode.IMEDIATA
            ),
            goal=row["goal"],
            kids_consent=bool(row["kids_consent"]),
            onboarded=bool(row["onboarded"]),
            run_key=row["run_key"] or "default",
            id=row["id"],
            first_name=row["first_name"],
        )

    # ------------------------------------------------------------------
    def update(self, telegram_id: int, **fields: Any) -> None:
        clean = {k: v for k, v in fields.items() if k in _UPDATABLE_FIELDS}
        if not clean:
            return
        # Converte enums para string/valor.
        for key, value in list(clean.items()):
            if hasattr(value, "value"):
                clean[key] = value.value
            elif isinstance(value, bool):
                clean[key] = int(value)
        assignments = ", ".join(f"{k} = ?" for k in clean)
        params = list(clean.values()) + [telegram_id]
        self.db.execute(
            f"UPDATE users SET {assignments}, updated_at = datetime('now') "
            "WHERE telegram_id = ?",
            params,
        )

    def add_xp(self, telegram_id: int, amount: int) -> int:
        self.db.execute(
            "UPDATE users SET xp = xp + ?, last_activity = datetime('now') "
            "WHERE telegram_id = ?",
            (amount, telegram_id),
        )
        row = self.db.query_one(
            "SELECT xp FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        return int(row["xp"]) if row else 0

    def set_consent(self, telegram_id: int, kind: str, granted: bool) -> None:
        self.db.execute(
            """
            INSERT INTO consents (telegram_id, kind, granted)
            VALUES (?, ?, ?)
            ON CONFLICT (telegram_id, kind) DO UPDATE SET
                granted = excluded.granted,
                created_at = datetime('now')
            """,
            (telegram_id, kind, int(granted)),
        )

    # ------------------------------------------------------------------
    def delete(self, telegram_id: int) -> None:
        """Remove o usuário e todos os dados relacionados (LGPD)."""

        with self.db.transaction() as conn:
            for table in ("sessions", "progress", "assessments", "consents"):
                conn.execute(f"DELETE FROM {table} WHERE telegram_id = ?", (telegram_id,))
            conn.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))

    def export(self, telegram_id: int) -> dict[str, Any]:
        """Exporta todos os dados do usuário (portabilidade)."""

        result: dict[str, Any] = {"telegram_id": telegram_id}
        for table in ("users", "sessions", "progress", "assessments", "consents"):
            rows = self.db.query(
                f"SELECT * FROM {table} WHERE telegram_id = ?", (telegram_id,)
            )
            result[table] = [dict(row) for row in rows]
        return result


class SessionRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def save(self, session: LearningSession) -> None:
        self.db.execute(
            """
            INSERT INTO sessions
                (telegram_id, mode, module, lesson_id, exercise_index, current_item, awaiting, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT (telegram_id) DO UPDATE SET
                mode = excluded.mode,
                module = excluded.module,
                lesson_id = excluded.lesson_id,
                exercise_index = excluded.exercise_index,
                current_item = excluded.current_item,
                awaiting = excluded.awaiting,
                updated_at = datetime('now')
            """,
            (
                session.telegram_id,
                session.mode.value if session.mode else None,
                session.module,
                session.lesson_id,
                session.exercise_index,
                json.dumps(session.current_item, ensure_ascii=False),
                session.awaiting,
            ),
        )

    def get(self, telegram_id: int) -> LearningSession | None:
        row = self.db.query_one(
            "SELECT * FROM sessions WHERE telegram_id = ?", (telegram_id,)
        )
        if row is None:
            return None

        def _enum(value, enum_cls):
            if value is None:
                return None
            try:
                return enum_cls(value)
            except ValueError:
                return None

        try:
            current_item = json.loads(row["current_item"] or "{}")
        except json.JSONDecodeError:
            current_item = {}
        return LearningSession(
            telegram_id=row["telegram_id"],
            mode=_enum(row["mode"], Modality),
            module=row["module"],
            lesson_id=row["lesson_id"],
            exercise_index=row["exercise_index"],
            current_item=current_item,
            awaiting=row["awaiting"],
            updated_at=row["updated_at"],
        )

    def clear(self, telegram_id: int) -> None:
        self.db.execute("DELETE FROM sessions WHERE telegram_id = ?", (telegram_id,))


class ProgressRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def record(
        self,
        telegram_id: int,
        learn_lang: str,
        module: str,
        item_id: str,
        *,
        status: str = "started",
        score: float = 0.0,
        run_key: str = "default",
    ) -> None:
        self.db.execute(
            """
            INSERT INTO progress
                (telegram_id, learn_lang, run_key, module, item_id, status, score, attempts, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, datetime('now'))
            ON CONFLICT (telegram_id, run_key, module, item_id) DO UPDATE SET
                status = excluded.status,
                score = MAX(progress.score, excluded.score),
                attempts = progress.attempts + 1,
                updated_at = datetime('now')
            """,
            (telegram_id, learn_lang, run_key, module, item_id, status, score),
        )

    def list_for(
        self, telegram_id: int, learn_lang: str | None = None, run_key: str | None = None
    ) -> list[dict[str, Any]]:
        sql = "SELECT * FROM progress WHERE telegram_id = ?"
        params: list[Any] = [telegram_id]
        if learn_lang:
            sql += " AND learn_lang = ?"
            params.append(learn_lang)
        if run_key:
            sql += " AND run_key = ?"
            params.append(run_key)
        return [dict(row) for row in self.db.query(sql, params)]

    def summary(self, telegram_id: int, learn_lang: str, run_key: str = "default") -> dict[str, int]:
        rows = self.list_for(telegram_id, learn_lang, run_key)
        completed = sum(1 for r in rows if r["status"] == "completed")
        started = sum(1 for r in rows if r["status"] != "completed")
        return {"completed": completed, "started": started, "total": len(rows)}


class AssessmentRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(
        self,
        telegram_id: int,
        learn_lang: str,
        kind: str,
        score: float,
        total: int,
        details: dict[str, Any] | None = None,
        run_key: str = "default",
    ) -> None:
        self.db.execute(
            """
            INSERT INTO assessments
                (telegram_id, learn_lang, run_key, kind, score, total, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                learn_lang,
                run_key,
                kind,
                score,
                total,
                json.dumps(details or {}, ensure_ascii=False),
            ),
        )

    def list_for(
        self, telegram_id: int, learn_lang: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        sql = "SELECT * FROM assessments WHERE telegram_id = ?"
        params: list[Any] = [telegram_id]
        if learn_lang:
            sql += " AND learn_lang = ?"
            params.append(learn_lang)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = [dict(row) for row in self.db.query(sql, params)]
        for row in rows:
            try:
                row["details"] = json.loads(row["details"] or "{}")
            except json.JSONDecodeError:
                row["details"] = {}
        return rows


class Storage:
    """Fachada que reúne banco e repositórios."""

    def __init__(self, database_path: str = ":memory:") -> None:
        self.db = Database(database_path)
        self.db.initialize()
        self.users = UserRepository(self.db)
        self.sessions = SessionRepository(self.db)
        self.progress = ProgressRepository(self.db)
        self.assessments = AssessmentRepository(self.db)

    def close(self) -> None:
        self.db.close()
