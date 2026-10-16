"""Testes do conteúdo educacional e dos serviços (pronúncia, tutor, áudio)."""

from __future__ import annotations

from pathlib import Path

import pytest

from linguabot.content.grammar import get_lesson, get_lessons
from linguabot.content.languages import LANGUAGES, get_language
from linguabot.content.vocabulary import KID_CATEGORIES, get_word, get_words
from linguabot.models import LearnLang, Level, Voice
from linguabot.services import audio as audio_service
from linguabot.services.images import GeneratedCardProvider, ImageService, LocalAssetsProvider
from linguabot.services.stt import NullSTT, VoskSTT, build_stt
from linguabot.services.tts import GTTSEngine, SpeechService
from linguabot.services.tutor import (
    PronResult,
    evaluate_pronunciation,
    pronunciation_feedback,
    rule_corrections,
)
from tests.fakes import FakeTTSEngine


# --- idiomas -----------------------------------------------------------------
def test_idiomas_tem_vozes_masculina_e_feminina():
    for lang in LANGUAGES.values():
        assert Voice.FEMININO in lang.edge_voices
        assert Voice.MASCULINO in lang.edge_voices
        assert lang.edge_voices[Voice.FEMININO] != lang.edge_voices[Voice.MASCULINO]


def test_vocabulario_filtra_por_categoria_e_publico():
    kids = get_words(LearnLang.EN, kids_only=True)
    assert kids, "deve haver palavras infantis em inglês"
    assert all(w.category in KID_CATEGORIES for w in kids)
    animals = get_words(LearnLang.EN, category="animals")
    assert animals and all(w.category == "animals" for w in animals)


def test_gramatica_por_idioma():
    assert get_lessons(LearnLang.EN)
    lesson = get_lesson(LearnLang.EN, "en-verb-to-be")
    assert lesson is not None and lesson.exercises


# --- pronúncia ---------------------------------------------------------------
def test_pronuncia_exata():
    result = evaluate_pronunciation("dog", "dog")
    assert result.status == "ok"
    assert result.similarity == 1.0


def test_pronuncia_proxima():
    result = evaluate_pronunciation("apple", "apples")
    assert result.status in {"ok", "close"}
    assert result.similarity > 0.6


def test_pronuncia_diferente():
    result = evaluate_pronunciation("dog", "completely different")
    assert result.status == "different"


def test_pronuncia_desconhecida():
    result = evaluate_pronunciation("dog", None)
    assert result.status == "unknown"
    assert result.confident is False


def test_feedback_avisa_limite_tecnico():
    result = PronResult("close", 0.7, "appl", "apple")
    text = pronunciation_feedback(result, "épol")
    assert "não mede fonemas" in text.lower()
    assert "épol" in text


# --- tutor / regras ----------------------------------------------------------
def test_regras_de_correcao():
    suggestions = rule_corrections("i is happy")
    assert any("i am" in s.lower() for s in suggestions)


def test_correcao_capitaliza():
    assert any(s[0].isupper() for s in rule_corrections("hello world"))


# --- áudio (usa ffmpeg embutido) ---------------------------------------------
def test_conversao_de_audio(tmp_path: Path):
    from tests.fakes import _write_silence_wav

    src = str(tmp_path / "in.wav")
    _write_silence_wav(src, 0.2)
    wav = audio_service.convert_to_wav_16k_mono(src)
    assert Path(wav).exists()
    ogg = audio_service.convert_to_ogg_opus(wav)
    assert Path(ogg).exists() and ogg.endswith(".ogg")
    audio_service.safe_unlink(wav)
    audio_service.safe_unlink(ogg)


# --- TTS ---------------------------------------------------------------------
def test_speech_service_gera_ogg():
    import asyncio

    engine = FakeTTSEngine()
    service = SpeechService(engine, None)
    path = asyncio.run(service.synthesize_voice("hello", "en", Voice.FEMININO))
    assert path is not None and path.endswith(".ogg")
    assert engine.calls and engine.calls[0][0] == "hello"
    audio_service.safe_unlink(path)


def test_speech_service_fallback():
    import asyncio

    failing = FakeTTSEngine(fail=True)
    working = FakeTTSEngine()
    service = SpeechService(failing, working)
    path = asyncio.run(service.synthesize_voice("hello", "en", Voice.MASCULINO))
    assert path is not None
    assert working.calls
    audio_service.safe_unlink(path)


def test_gtts_nao_suporta_genero():
    assert GTTSEngine.supports_gender is False


# --- STT ---------------------------------------------------------------------
def test_build_stt_none(settings):
    settings.stt_provider = "none"
    assert isinstance(build_stt(settings), NullSTT)


def test_vosk_transcribe_sem_modelo_retorna_none(tmp_path):
    stt = VoskSTT(str(tmp_path / "sem-modelos"))
    assert stt.transcribe(str(tmp_path / "x.ogg"), "en") is None


# --- imagens -----------------------------------------------------------------
def test_cartao_gerado_localmente(tmp_path):
    provider = GeneratedCardProvider(str(tmp_path))
    result = provider.get_image(term="dog", category="animals", emoji="🐶", translation="cachorro")
    assert result is not None
    assert Path(result.path).exists()


def test_assets_ausentes_retorna_none(tmp_path):
    provider = LocalAssetsProvider(str(tmp_path / "nao-existe"))
    assert provider.get_image(term="dog", category="animals", emoji="🐶", translation="c") is None


def test_image_service_sem_provedores(tmp_path):
    service = ImageService([LocalAssetsProvider(str(tmp_path / "vazio"))])
    assert service.get_image(term="dog", category="animals", emoji="🐶", translation="c") is None
