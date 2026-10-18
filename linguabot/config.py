"""Carregamento e validação de configuração do LinguaBot.

Toda a configuração vem de variáveis de ambiente (com suporte a arquivo
``.env`` via python-dotenv). Nenhum segredo é gravado no código.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

def _load_env_files() -> None:
    """Carrega as chaves de configuração.

    Ordem de precedência (o primeiro valor encontrado vence):
    1. ``chaves/.env``  – pasta de segredos ao lado do código (recomendada)
    2. ``./.env``       – diretório atual
    3. ``<projeto>/.env``
    """

    try:  # python-dotenv é opcional em tempo de import
        from dotenv import load_dotenv
    except Exception:  # pragma: no cover - apenas conveniência
        return

    try:
        project_root = Path(__file__).resolve().parent.parent
    except Exception:  # pragma: no cover - defensivo
        project_root = Path.cwd()

    for candidate in (
        project_root / "chaves" / ".env",
        Path.cwd() / ".env",
        project_root / ".env",
    ):
        try:
            if candidate.is_file():
                load_dotenv(candidate, override=False)
        except Exception:  # pragma: no cover - defensivo
            continue


_load_env_files()


class ConfigError(RuntimeError):
    """Erro de configuração que impede a inicialização."""


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on", "sim"}


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"Variável {name} deve ser um número inteiro.") from exc


@dataclass
class Settings:
    """Configuração imutável da aplicação."""

    bot_token: str = ""
    database_path: str = "./data/linguabot.db"
    default_ui_lang: str = "pt"
    log_level: str = "INFO"
    rate_limit_per_minute: int = 30

    llm_provider: str = "none"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    stt_provider: str = "vosk"
    vosk_models_dir: str = "./models/vosk"

    tts_provider: str = "edge"
    tts_rate: str = "-25%"
    piper_exe: str = ""
    piper_models_dir: str = "./models/piper"

    assets_dir: str = "./assets/images"

    health_enabled: bool = False
    port: int = 10000

    kids_mode_enabled: bool = True

    problems: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    @classmethod
    def from_env(cls) -> "Settings":
        settings = cls(
            bot_token=os.getenv("BOT_TOKEN", "").strip(),
            database_path=os.getenv("DATABASE_PATH", "./data/linguabot.db").strip(),
            default_ui_lang=os.getenv("DEFAULT_UI_LANG", "pt").strip().lower(),
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
            rate_limit_per_minute=_get_int("RATE_LIMIT_PER_MINUTE", 30),
            llm_provider=os.getenv("LLM_PROVIDER", "none").strip().lower(),
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip(),
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434").strip(),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2").strip(),
            stt_provider=os.getenv("STT_PROVIDER", "vosk").strip().lower(),
            vosk_models_dir=os.getenv("VOSK_MODELS_DIR", "./models/vosk").strip(),
            tts_provider=os.getenv("TTS_PROVIDER", "edge").strip().lower(),
            tts_rate=os.getenv("TTS_RATE", "-25%").strip(),
            piper_exe=os.getenv("PIPER_EXE", "").strip(),
            piper_models_dir=os.getenv("PIPER_MODELS_DIR", "./models/piper").strip(),
            assets_dir=os.getenv("ASSETS_DIR", "./assets/images").strip(),
            health_enabled=_get_bool("HEALTH_ENABLED", False),
            port=_get_int("PORT", 10000),
            kids_mode_enabled=_get_bool("KIDS_MODE_ENABLED", True),
        )
        settings.validate()
        return settings

    # ------------------------------------------------------------------
    def validate(self) -> None:
        """Valida a configuração e registra problemas não fatais.

        O token é obrigatório apenas para executar o bot de verdade; a
        ausência dele vira um problema registrado (permite rodar testes e
        diagnósticos sem token).
        """
        self.problems.clear()
        if not self.bot_token:
            self.problems.append(
                "BOT_TOKEN não definido. O bot não iniciará a conexão com o Telegram."
            )
        if self.llm_provider not in {"none", "gemini", "ollama"}:
            self.problems.append(f"LLM_PROVIDER inválido: {self.llm_provider!r}.")
        if self.stt_provider not in {"none", "vosk", "gemini"}:
            self.problems.append(f"STT_PROVIDER inválido: {self.stt_provider!r}.")
        if self.tts_provider not in {"edge", "gtts", "piper"}:
            self.problems.append(f"TTS_PROVIDER inválido: {self.tts_provider!r}.")
        if self.llm_provider == "gemini" and not self.gemini_api_key:
            self.problems.append(
                "LLM_PROVIDER=gemini mas GEMINI_API_KEY está vazio; usando regras offline."
            )
        if self.stt_provider == "gemini" and not self.gemini_api_key:
            self.problems.append(
                "STT_PROVIDER=gemini mas GEMINI_API_KEY está vazio; usando STT desativado."
            )
        if self.tts_provider == "piper" and not self.piper_exe:
            self.problems.append(
                "TTS_PROVIDER=piper mas PIPER_EXE está vazio; usando gTTS como alternativa."
            )

    # ------------------------------------------------------------------
    @property
    def database_file(self) -> Path:
        return Path(self.database_path)

    @property
    def token_available(self) -> bool:
        return bool(self.bot_token)
