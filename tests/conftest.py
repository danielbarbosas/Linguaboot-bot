"""Fixtures compartilhadas dos testes."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from linguabot.config import Settings
from linguabot.container import Services
from linguabot.services.images import GeneratedCardProvider, ImageService
from linguabot.services.tts import SpeechService
from linguabot.storage.repository import Storage
from tests.fakes import FakeContext, FakeLLM, FakeSTT, FakeTTSEngine, FakeUser


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        bot_token="123456:TESTTOKEN",
        database_path=str(tmp_path / "test.db"),
        default_ui_lang="pt",
        rate_limit_per_minute=30,
    )


@pytest.fixture
def storage() -> Storage:
    store = Storage(":memory:")
    yield store
    store.close()


@pytest.fixture
def services(tmp_path: Path, settings: Settings, storage: Storage) -> Services:
    cache = str(tmp_path / "cache")
    images = ImageService([GeneratedCardProvider(cache)])
    return Services(
        settings=settings,
        storage=storage,
        llm=FakeLLM(),
        speech=SpeechService(FakeTTSEngine(), None),
        stt=FakeSTT(),
        images_adult=images,
        images_kids=images,
    )


@pytest.fixture
def context(services: Services) -> FakeContext:
    return FakeContext(services)


@pytest.fixture
def user() -> FakeUser:
    return FakeUser(1001, first_name="Ana")


def run(coro):
    """Executa uma corrotina em teste síncrono."""

    return asyncio.run(coro)
