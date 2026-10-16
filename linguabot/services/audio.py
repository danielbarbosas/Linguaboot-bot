"""Conversão de áudio usando o ffmpeg embutido (imageio-ffmpeg).

O Telegram envia mensagens de voz em OGG/Opus. Para reconhecimento de fala
precisamos de WAV PCM 16 kHz mono; para enviar uma "mensagem de voz" de volta
precisamos de OGG/Opus. Nada disso exige instalar o ffmpeg no sistema.
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioError(RuntimeError):
    """Falha ao converter áudio."""


def ffmpeg_executable() -> str:
    """Retorna o caminho do ffmpeg embutido do imageio-ffmpeg."""

    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # pragma: no cover - depende do ambiente
        raise AudioError(
            "ffmpeg embutido não encontrado. Instale imageio-ffmpeg (requirements.txt)."
        ) from exc


def _run(args: list[str]) -> None:
    logger.debug("ffmpeg: %s", " ".join(args))
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise AudioError(f"ffmpeg falhou: {proc.stderr.strip()[:500]}")


def _tmp(suffix: str) -> str:
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    handle.close()
    return handle.name


def convert_to_wav_16k_mono(src: str, dst: str | None = None) -> str:
    """Converte qualquer áudio em WAV PCM 16 kHz mono (entrada do Vosk)."""

    dst = dst or _tmp(".wav")
    _run(
        [
            ffmpeg_executable(),
            "-y",
            "-i",
            src,
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            dst,
        ]
    )
    return dst


def convert_to_ogg_opus(src: str, dst: str | None = None) -> str:
    """Converte áudio em OGG/Opus (formato de mensagem de voz do Telegram)."""

    dst = dst or _tmp(".ogg")
    _run(
        [
            ffmpeg_executable(),
            "-y",
            "-i",
            src,
            "-c:a",
            "libopus",
            "-b:a",
            "48k",
            "-ar",
            "48000",
            "-ac",
            "1",
            dst,
        ]
    )
    return dst


def safe_unlink(path: str | None) -> None:
    if not path:
        return
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:  # pragma: no cover - defensivo
        logger.debug("Falha ao remover arquivo temporário %s", path)
