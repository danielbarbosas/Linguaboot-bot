"""Baixa os modelos Vosk (reconhecimento de fala local e gratuito).

Uso:
    python scripts/download_vosk_models.py            # baixa todos os idiomas
    python scripts/download_vosk_models.py en es      # baixa idiomas específicos

Os modelos são gravados em VOSK_MODELS_DIR (padrão: ./models/vosk). São
pesados (dezenas de MB). Nenhum custo envolvido; o uso é offline.
"""

from __future__ import annotations

import os
import sys
import urllib.request
import zipfile
from pathlib import Path

# Espelho oficial dos modelos pequenos do Vosk.
BASE_URL = "https://alphacephei.com/vosk/models"

MODELS = {
    "en": "vosk-model-small-en-us-0.15",
    "es": "vosk-model-small-es-0.42",
    "fr": "vosk-model-small-fr-0.22",
    "de": "vosk-model-small-de-0.15",
    "it": "vosk-model-small-it-0.22",
    "pt": "vosk-model-small-pt-0.3",
}


def download(model_name: str, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / model_name
    if target.exists():
        print(f"[=] {model_name} já existe em {target}")
        return

    url = f"{BASE_URL}/{model_name}.zip"
    zip_path = dest_dir / f"{model_name}.zip"
    print(f"[↓] Baixando {url}")
    urllib.request.urlretrieve(url, zip_path)

    print(f"[⇢] Extraindo {zip_path.name}")
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(dest_dir)
    zip_path.unlink(missing_ok=True)
    print(f"[✓] {model_name} pronto em {target}")


def main(argv: list[str]) -> int:
    dest_dir = Path(os.getenv("VOSK_MODELS_DIR", "./models/vosk"))
    langs = argv or list(MODELS)
    unknown = [lang for lang in langs if lang not in MODELS]
    if unknown:
        print(f"Idiomas desconhecidos: {', '.join(unknown)}")
        print(f"Disponíveis: {', '.join(MODELS)}")
        return 1
    for lang in langs:
        download(MODELS[lang], dest_dir)
    print("Concluído. Defina STT_PROVIDER=vosk no .env.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
