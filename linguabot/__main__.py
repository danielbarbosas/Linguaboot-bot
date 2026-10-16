"""Ponto de entrada do LinguaBot.

Uso:
    python -m linguabot            # inicia o bot (long polling)
    python -m linguabot --diagnose # mostra o diagnóstico do ambiente e sai
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .config import Settings
from .logging_setup import setup_logging


def _acquire_lock(lock_path: Path) -> object | None:
    """Evita duas instâncias de polling simultâneas (proteção básica)."""

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        # Arquivo existe: verifica se o processo ainda está vivo.
        try:
            pid = int(lock_path.read_text(encoding="utf-8").strip() or "0")
        except (ValueError, OSError):
            pid = 0
        if pid and _pid_alive(pid):
            return None
        lock_path.write_text(str(os.getpid()), encoding="utf-8")
        return lock_path
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    return lock_path


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":  # pragma: no cover - específico de Windows
        import subprocess

        try:
            output = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
            ).stdout
            return str(pid) in output
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def diagnose(settings: Settings) -> int:
    """Imprime o status da configuração e das dependências opcionais."""

    print(f"LinguaBot {__version__} - diagnóstico")
    print("-" * 40)
    print(f"BOT_TOKEN definido? {'sim' if settings.token_available else 'não'}")
    print(f"Banco de dados: {settings.database_path}")
    print(f"Idioma de interface padrão: {settings.default_ui_lang}")
    print(f"LLM: {settings.llm_provider}")
    print(f"STT: {settings.stt_provider}")
    print(f"TTS: {settings.tts_provider}")

    for label, module in (
        ("python-telegram-bot", "telegram"),
        ("edge-tts", "edge_tts"),
        ("gTTS", "gtts"),
        ("vosk", "vosk"),
        ("soundfile", "soundfile"),
        ("imageio-ffmpeg", "imageio_ffmpeg"),
        ("Pillow", "PIL"),
        ("google-genai", "google.genai"),
    ):
        try:
            __import__(module)
            status = "instalado"
        except Exception:
            status = "ausente"
        print(f"  - {label}: {status}")

    if settings.problems:
        print("-" * 40)
        print("Avisos:")
        for problem in settings.problems:
            print(f"  * {problem}")
    return 0 if settings.token_available else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="linguabot", description="Bot de idiomas no Telegram.")
    parser.add_argument("--diagnose", action="store_true", help="Mostra o diagnóstico e sai.")
    parser.add_argument("--version", action="version", version=f"LinguaBot {__version__}")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    setup_logging(settings.log_level)

    if args.diagnose:
        return diagnose(settings)

    if not settings.bot_token:
        print("ERRO: BOT_TOKEN não configurado. Copie .env.example para .env e preencha.")
        print("Dica: rode 'python -m linguabot --diagnose' para verificar o ambiente.")
        return 1

    lock_path = Path(settings.database_path).parent / "linguabot.lock"
    lock = _acquire_lock(lock_path)
    if lock is None:
        print("Já existe uma instância do LinguaBot em execução. Encerrando.")
        return 1

    if settings.health_enabled:
        from .health import start_health_server

        start_health_server(settings.port)

    from .bot.application import run

    try:
        run(settings)
    finally:
        try:
            lock_path.unlink(missing_ok=True)
        except OSError:
            pass
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
