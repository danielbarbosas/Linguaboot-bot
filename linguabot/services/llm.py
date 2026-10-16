"""Adaptadores de modelos de linguagem (LLM).

Todos são opcionais: se nenhum estiver disponível, o ``TutorService`` usa
respostas determinísticas por regras, e o bot continua funcionando offline.
"""

from __future__ import annotations

import logging
from typing import Protocol

from ..config import Settings

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    name: str

    @property
    def available(self) -> bool:
        ...

    def generate(self, prompt: str, system: str | None = None) -> str | None:
        ...


class NullLLM:
    """LLM nulo: sinaliza que não há geração de texto disponível."""

    name = "null"

    @property
    def available(self) -> bool:
        return False

    def generate(self, prompt: str, system: str | None = None) -> str | None:
        return None


class GeminiLLM:
    """Google Gemini via SDK oficial (opcional, requer GEMINI_API_KEY)."""

    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        self.model = model
        self._client = None
        if api_key:
            try:
                from google import genai

                self._client = genai.Client(api_key=api_key)
            except Exception as exc:  # pragma: no cover - depende do ambiente
                logger.warning("Gemini indisponível: %s", exc)
                self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def generate(self, prompt: str, system: str | None = None) -> str | None:
        if self._client is None:
            return None
        try:
            contents = f"{system}\n\n{prompt}" if system else prompt
            response = self._client.models.generate_content(
                model=self.model, contents=contents
            )
            text = getattr(response, "text", None)
            return text.strip() if text else None
        except Exception as exc:
            logger.warning("Falha do Gemini: %s", exc)
            return None


class OllamaLLM:
    """LLM local via Ollama (opcional, gratuito, roda na máquina do usuário)."""

    name = "ollama"

    def __init__(self, host: str, model: str, timeout: float = 60.0) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return True

    def generate(self, prompt: str, system: str | None = None) -> str | None:
        try:
            import requests

            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system or "",
                    "stream": False,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return (response.json().get("response") or "").strip() or None
        except Exception as exc:
            logger.warning("Falha do Ollama: %s", exc)
            return None


def build_llm(settings: Settings) -> LLMClient:
    if settings.llm_provider == "gemini":
        client = GeminiLLM(settings.gemini_api_key, settings.gemini_model)
        if client.available:
            return client
    elif settings.llm_provider == "ollama":
        return OllamaLLM(settings.ollama_host, settings.ollama_model)
    return NullLLM()
