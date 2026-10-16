"""Configuração de logging do LinguaBot.

Garante que tokens e dados sensíveis nunca apareçam nos logs.
"""

from __future__ import annotations

import logging
import re

_TOKEN_PATTERN = re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{30,}\b")


class _RedactFilter(logging.Filter):
    """Remove possíveis tokens do Telegram do texto dos logs."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D102
        try:
            message = record.getMessage()
        except Exception:  # pragma: no cover - defensivo
            return True
        if _TOKEN_PATTERN.search(message):
            record.msg = _TOKEN_PATTERN.sub("***TOKEN-OCULTO***", message)
            record.args = ()
        return True


def setup_logging(level: str = "INFO") -> None:
    """Configura o logging raiz com filtro de segredos."""

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Evita handlers duplicados em recarregamentos.
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    handler.addFilter(_RedactFilter())
    root.addHandler(handler)

    # Bibliotecas verbosas demais.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
