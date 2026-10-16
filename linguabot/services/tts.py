"""Adaptadores de síntese de voz (texto -> áudio).

Motores:
- ``edge`` (padrão): Microsoft Edge TTS, gratuito, sem chave, com vozes
  masculinas e femininas reais por idioma.
- ``gtts``: Google TTS via pacote gTTS, gratuito, mas SEM escolha de gênero.
- ``piper``: TTS neural local/offline (requer binário e modelos do Piper).

O gênero escolhido pelo usuário só é aplicado quando o motor suporta vozes
por gênero; caso contrário o bot informa a limitação (nunca finge).
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Protocol

from ..config import Settings
from ..content.languages import get_language
from ..models import LearnLang, Voice
from . import audio

logger = logging.getLogger(__name__)

MAX_TTS_CHARS = 600


class TTSEngine(Protocol):
    name: str
    supports_gender: bool

    async def synthesize(
        self, text: str, lang: str, voice: Voice, out_path: str
    ) -> str:
        ...


def _clean(text: str) -> str:
    return text.strip()[:MAX_TTS_CHARS]


class EdgeTTSEngine:
    name = "edge"
    supports_gender = True

    async def synthesize(self, text: str, lang: str, voice: Voice, out_path: str) -> str:
        import edge_tts

        language = get_language(LearnLang(lang))
        voice_name = language.edge_voices.get(voice) or language.edge_voices[Voice.FEMININO]
        communicate = edge_tts.Communicate(_clean(text), voice_name)
        await communicate.save(out_path)
        return out_path


class GTTSEngine:
    name = "gtts"
    supports_gender = False

    async def synthesize(self, text: str, lang: str, voice: Voice, out_path: str) -> str:
        from gtts import gTTS

        language = get_language(LearnLang(lang))

        def _run() -> str:
            tts = gTTS(text=_clean(text), lang=language.gtts_code)
            tts.save(out_path)
            return out_path

        return await asyncio.to_thread(_run)


class PiperEngine:
    name = "piper"
    supports_gender = True

    def __init__(self, exe: str, models_dir: str) -> None:
        self.exe = exe
        self.models_dir = Path(models_dir)

    def _model_for(self, lang: str, voice: Voice) -> str | None:
        for pattern in (f"{lang}_{voice.value}.onnx", f"{lang}-{voice.value}.onnx"):
            candidate = self.models_dir / pattern
            if candidate.exists():
                return str(candidate)
        return None

    async def synthesize(self, text: str, lang: str, voice: Voice, out_path: str) -> str:
        model = self._model_for(lang, voice)
        if not model:
            raise RuntimeError(f"Modelo Piper não encontrado para {lang}/{voice.value}")

        def _run() -> str:
            import subprocess

            proc = subprocess.run(
                [self.exe, "--model", model, "--output_file", out_path],
                input=_clean(text).encode("utf-8"),
                capture_output=True,
            )
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.decode(errors="ignore")[:300])
            return out_path

        return await asyncio.to_thread(_run)


class SpeechService:
    """Gera um arquivo de áudio pronto para o Telegram (OGG/Opus)."""

    def __init__(self, primary: TTSEngine, fallback: TTSEngine | None = None) -> None:
        self.primary = primary
        self.fallback = fallback

    @property
    def supports_gender(self) -> bool:
        return self.primary.supports_gender

    async def synthesize_voice(self, text: str, lang: str, voice: Voice) -> str | None:
        """Retorna o caminho de um OGG/Opus (ou MP3, se a conversão falhar)."""

        if not text or not text.strip():
            return None

        engines = [self.primary]
        if self.fallback is not None and self.fallback is not self.primary:
            engines.append(self.fallback)

        raw_path: str | None = None
        used: TTSEngine | None = None
        for engine in engines:
            suffix = ".wav" if engine.name == "piper" else ".mp3"
            out = audio._tmp(suffix)  # noqa: SLF001 - helper interno do módulo
            try:
                await engine.synthesize(text, lang, voice, out)
                raw_path = out
                used = engine
                break
            except Exception as exc:
                logger.warning("TTS %s falhou: %s", engine.name, exc)
                audio.safe_unlink(out)

        if not raw_path or used is None:
            return None

        try:
            return audio.convert_to_ogg_opus(raw_path)
        except Exception as exc:
            logger.warning("Conversão para OGG falhou (%s); enviando %s.", exc, used.name)
            return raw_path


def build_speech(settings: Settings) -> SpeechService:
    fallback: TTSEngine = GTTSEngine()

    if settings.tts_provider == "piper" and settings.piper_exe:
        primary: TTSEngine = PiperEngine(settings.piper_exe, settings.piper_models_dir)
        return SpeechService(primary, fallback)
    if settings.tts_provider == "gtts":
        return SpeechService(GTTSEngine(), None)
    return SpeechService(EdgeTTSEngine(), fallback)
