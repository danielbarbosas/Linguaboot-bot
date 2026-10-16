"""Ponto de entrada compatível: ``python bot.py``.

Todo o código do LinguaBot vive no pacote ``linguabot``. Este arquivo apenas
delega para o ponto de entrada oficial (``python -m linguabot``).
"""

from __future__ import annotations

import sys

from linguabot.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
