"""Testes de persistência (banco, migrações e repositórios)."""

from __future__ import annotations

from linguabot.models import LearnLang, Level, Modality, UILang, Voice
from linguabot.storage.database import Database
from linguabot.storage.repository import Storage


def test_migracoes_idempotentes(tmp_path):
    path = str(tmp_path / "db.sqlite")
    first = Database(path)
    first.initialize()
    version = first.query_one("SELECT value FROM meta WHERE key='schema_version'")
    assert version["value"] == "1"
    first.close()

    second = Database(path)
    second.initialize()  # não deve falhar nem duplicar
    tables = {r["name"] for r in second.query("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"users", "sessions", "progress", "assessments", "consents"} <= tables
    second.close()


def test_criar_e_ler_perfil(storage: Storage):
    storage.users.ensure_user(1, username="ana", first_name="Ana")
    profile = storage.users.get_profile(1)
    assert profile is not None
    assert profile.telegram_id == 1
    assert profile.ui_lang is UILang.PT
    assert profile.onboarded is False


def test_atualizar_preferencias(storage: Storage):
    storage.users.ensure_user(1)
    storage.users.update(
        1,
        learn_lang=LearnLang.EN.value,
        level=Level.BASICO.value,
        voice=Voice.MASCULINO.value,
        modality=Modality.GRAMATICA.value,
        onboarded=True,
    )
    profile = storage.users.get_profile(1)
    assert profile.learn_lang is LearnLang.EN
    assert profile.level is Level.BASICO
    assert profile.voice is Voice.MASCULINO
    assert profile.modality is Modality.GRAMATICA
    assert profile.onboarded is True


def test_campo_nao_permitido_ignorado(storage: Storage):
    storage.users.ensure_user(1)
    storage.users.update(1, xp=9999)  # xp não está na allowlist de update()
    row = storage.users.get(1)
    assert row["xp"] == 0


def test_xp_acumula(storage: Storage):
    storage.users.ensure_user(1)
    assert storage.users.add_xp(1, 5) == 5
    assert storage.users.add_xp(1, 3) == 8


def test_sessao_salva_e_recuperada(storage: Storage):
    storage.users.ensure_user(1)
    from linguabot.models import LearningSession

    storage.sessions.save(
        LearningSession(
            telegram_id=1,
            mode=Modality.PRONUNCIA,
            module="pronunciation",
            lesson_id="en-verb-to-be",
            exercise_index=2,
            current_item={"term": "dog"},
            awaiting="pronunciation",
        )
    )
    session = storage.sessions.get(1)
    assert session is not None
    assert session.mode is Modality.PRONUNCIA
    assert session.current_item["term"] == "dog"
    assert session.awaiting == "pronunciation"

    storage.sessions.clear(1)
    assert storage.sessions.get(1) is None


def test_progresso_upsert(storage: Storage):
    storage.users.ensure_user(1)
    storage.progress.record(1, "en", "grammar", "ex-1", status="review", score=0.0)
    storage.progress.record(1, "en", "grammar", "ex-1", status="completed", score=1.0)
    rows = storage.progress.list_for(1, "en")
    assert len(rows) == 1
    assert rows[0]["status"] == "completed"
    assert rows[0]["score"] == 1.0
    assert rows[0]["attempts"] == 2


def test_isolamento_entre_usuarios(storage: Storage):
    storage.users.ensure_user(1)
    storage.users.ensure_user(2)
    storage.progress.record(1, "en", "grammar", "a", status="completed", score=1)
    storage.progress.record(2, "en", "grammar", "b", status="completed", score=1)
    assert len(storage.progress.list_for(1, "en")) == 1
    assert len(storage.progress.list_for(2, "en")) == 1
    assert storage.progress.list_for(1, "en")[0]["item_id"] == "a"


def test_avaliacoes(storage: Storage):
    storage.users.ensure_user(1)
    storage.assessments.add(1, "en", "vocabulario", 4, 5, {"pct": 80})
    rows = storage.assessments.list_for(1, "en")
    assert len(rows) == 1
    assert rows[0]["score"] == 4
    assert rows[0]["details"]["pct"] == 80


def test_export_e_delete(storage: Storage):
    storage.users.ensure_user(1, first_name="Ana")
    storage.users.update(1, learn_lang="en")
    storage.progress.record(1, "en", "grammar", "a", status="completed", score=1)
    storage.assessments.add(1, "en", "vocabulario", 5, 5)
    data = storage.users.export(1)
    assert data["users"][0]["first_name"] == "Ana"
    assert len(data["progress"]) == 1

    storage.users.delete(1)
    assert storage.users.get(1) is None
    assert storage.progress.list_for(1, "en") == []
    assert storage.assessments.list_for(1, "en") == []
