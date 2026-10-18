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

# Modelos grandes (mais precisos, ~2x melhor taxa de erro). Uso:
#     python scripts/download_vosk_models.py es:grande
LARGE_MODELS = {
    "en": "vosk-model-en-us-0.22",
    "es": "vosk-model-es-0.42",
    "fr": "vosk-model-fr-0.22",
    "de": "vosk-model-de-0.15",
    "it": "vosk-model-it-0.22",
    "pt": "vosk-model-pt-fb-v0.1.1-pruned",
}


def download(model_name: str, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / model_name
    if target.exists():
        print(f"[=] {model_name} já existe em {target}")
        return

    url = f"{BASE_URL}/{model_name}.zip"
    zip_path = dest_dir / f"{model_name}.zip"
    print(f"[down] Baixando {url}")
    urllib.request.urlretrieve(url, zip_path)

    print(f"[zip] Extraindo {zip_path.name}")
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(dest_dir)
    zip_path.unlink(missing_ok=True)
    print(f"[ok] {model_name} pronto em {target}")


def main(argv: list[str]) -> int:
    dest_dir = Path(os.getenv("VOSK_MODELS_DIR", "./models/vosk"))
    langs = argv or list(MODELS)
    unknown = [
        lang.split(":")[0]
        for lang in langs
        if lang.split(":")[0] not in MODELS or (lang.endswith(":grande") and lang.split(":")[0] not in LARGE_MODELS)
    ]
    if unknown:
        print(f"Idiomas desconhecidos: {', '.join(unknown)}")
        print(f"Disponíveis: {', '.join(MODELS)}")
        print("Use '<idioma>:grande' para o modelo grande (ex.: es:grande).")
        return 1
    for lang in langs:
        base, _, size = lang.partition(":")
        name = LARGE_MODELS[base] if size == "grande" else MODELS[base]
        download(name, dest_dir)
    print("Concluído. Defina STT_PROVIDER=vosk no .env.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
