"""Testes de configuração."""

from __future__ import annotations

from linguabot.config import Settings


def test_defaults_sem_token(monkeypatch):
    for var in ("BOT_TOKEN", "LLM_PROVIDER", "STT_PROVIDER", "TTS_PROVIDER", "DATABASE_PATH"):
        monkeypatch.delenv(var, raising=False)
    settings = Settings.from_env()
    assert settings.bot_token == ""
    assert settings.token_available is False
    assert settings.llm_provider == "none"
    assert settings.stt_provider == "vosk"
    assert settings.tts_provider == "edge"
    assert any("BOT_TOKEN" in p for p in settings.problems)


def test_le_env(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "chave")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "5")
    settings = Settings.from_env()
    assert settings.token_available is True
    assert settings.llm_provider == "gemini"
    assert settings.rate_limit_per_minute == 5
    assert not settings.problems


def test_provider_invalido_gera_aviso(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("TTS_PROVIDER", "voz-magica")
    settings = Settings.from_env()
    assert any("TTS_PROVIDER" in p for p in settings.problems)


def test_gemini_sem_chave_avisa(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    settings = Settings.from_env()
    assert any("GEMINI_API_KEY" in p for p in settings.problems)
