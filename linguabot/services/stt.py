"""Adaptadores de reconhecimento de fala (áudio -> texto).

Prioridade de projeto: reconhecimento local e gratuito (Vosk). O Gemini é
opcional. Se nada estiver disponível, o serviço retorna ``None`` e o bot
avisa o usuário, sem fingir que reconheceu o áudio.
"""

from __future__ import annotations

import logging
import os
import wave
from pathlib import Path
from typing import Protocol

from ..config import Settings
from ..content.languages import get_language
from ..models import LearnLang
from . import audio

logger = logging.getLogger(__name__)


class STTClient(Protocol):
    name: str

    @property
    def available(self) -> bool:
        ...

    def transcribe(self, audio_path: str, lang: str) -> str | None:
        ...


class NullSTT:
    name = "null"

    @property
    def available(self) -> bool:
        return False

    def transcribe(self, audio_path: str, lang: str) -> str | None:
        return None


class VoskSTT:
    """Reconhecimento de fala local e gratuito com Vosk."""

    name = "vosk"

    def __init__(self, models_dir: str) -> None:
        self.models_dir = Path(models_dir)
        self._models: dict[str, object] = {}

    @property
    def available(self) -> bool:
        try:
            import vosk  # noqa: F401

            return True
        except Exception:
            return False

    def _get_model(self, lang: str):
        if lang in self._models:
            return self._models[lang]
        try:
            import vosk
        except Exception:
            return None
        try:
            language = get_language(LearnLang(lang))
        except (ValueError, KeyError):
            return None
        # Prefere o modelo grande (muito mais preciso); cai para o pequeno.
        candidates = [
            name
            for name in (language.vosk_model_large, language.vosk_model)
            if name
        ]
        if not candidates:
            logger.warning("Sem modelo Vosk definido para o idioma %s", lang)
            return None
        model_path: Path | None = None
        for name in candidates:
            candidate = self.models_dir / name
            if candidate.exists():
                model_path = candidate
                break
        if model_path is None:
            logger.warning(
                "Modelo Vosk ausente em %s. Rode scripts/download_vosk_models.py.",
                self.models_dir / candidates[0],
            )
            return None
        vosk.SetLogLevel(-1)
        logger.info("Carregando modelo Vosk: %s", model_path.name)
        model = vosk.Model(str(model_path))
        self._models[lang] = model
        return model

    def transcribe(self, audio_path: str, lang: str) -> str | None:
        try:
            import vosk
        except Exception:
            return None

        model = self._get_model(lang)
        if model is None:
            return None

        wav_path: str | None = None
        try:
            wav_path = audio.convert_to_wav_16k_mono(audio_path)
            rec = vosk.KaldiRecognizer(model, 16000)
            with wave.open(wav_path, "rb") as wav_file:
                while True:
                    data = wav_file.readframes(4000)
                    if not data:
                        break
                    rec.AcceptWaveform(data)
            import json

            text = json.loads(rec.FinalResult()).get("text", "").strip()
            return text or None
        except Exception as exc:
            logger.warning("Falha ao transcrever com Vosk: %s", exc)
            return None
        finally:
            if wav_path:
                audio.safe_unlink(wav_path)


class GeminiSTT:
    """Transcrição via Google Gemini (opcional, requer chave)."""

    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        self.model = model
        self._client = None
        if api_key:
            try:
                from google import genai

                self._client = genai.Client(api_key=api_key)
            except Exception as exc:  # pragma: no cover
                logger.warning("Gemini STT indisponível: %s", exc)

    @property
    def available(self) -> bool:
        return self._client is not None

    def transcribe(self, audio_path: str, lang: str) -> str | None:
        if self._client is None:
            return None
        try:
            from google.genai import types

            uploaded = self._client.files.upload(
                file=audio_path,
                config=types.UploadFileConfig(mime_type="audio/ogg"),
            )
            response = self._client.models.generate_content(
                model=self.model,
                contents=[
                    "Transcreva exatamente a fala, apenas o texto, no idioma falado.",
                    uploaded,
                ],
            )
            text = getattr(response, "text", None)
            return text.strip() if text else None
        except Exception as exc:  # pragma: no cover - depende de rede
            logger.warning("Falha do Gemini STT: %s", exc)
            return None


def build_stt(settings: Settings) -> STTClient:
    if settings.stt_provider == "vosk":
        client = VoskSTT(settings.vosk_models_dir)
        if client.available:
            return client
        logger.warning("Vosk não instalado; STT desativado.")
    elif settings.stt_provider == "gemini":
        client = GeminiSTT(settings.gemini_api_key, settings.gemini_model)
        if client.available:
            return client
    return NullSTT()
