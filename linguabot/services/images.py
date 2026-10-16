"""Fornecimento de imagens sem depender de API paga.

Ordem de preferência:
1. ``LocalAssetsProvider``   - imagens curadas em ``ASSETS_DIR`` (ideal para crianças).
2. ``WikimediaProvider``     - fotos livres do Wikimedia Commons (sem chave; só para adultos).
3. ``GeneratedCardProvider`` - cartão gerado localmente com Pillow (sempre funciona, offline).

Para o modo infantil nunca usamos imagens externas aleatórias: preferimos
assets curados e, na ausência deles, um cartão gerado.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)

_CATEGORY_COLORS = {
    "animals": (255, 224, 178),
    "colors": (214, 234, 248),
    "numbers": (209, 242, 209),
    "shapes": (240, 219, 255),
    "food": (255, 228, 225),
    "objects": (224, 247, 250),
    "places": (232, 245, 233),
    "actions": (255, 249, 196),
}


@dataclass
class ImageResult:
    path: str
    source: str
    attribution: str | None = None


class ImageProvider(Protocol):
    def get_image(self, term: str, category: str, emoji: str, translation: str) -> ImageResult | None:
        ...


class LocalAssetsProvider:
    """Usa imagens curadas em disco (ex.: assets/images/<categoria>/<termo>.jpg)."""

    name = "local"

    def __init__(self, assets_dir: str) -> None:
        self.assets_dir = Path(assets_dir)

    def get_image(self, term: str, category: str, emoji: str, translation: str) -> ImageResult | None:
        if not self.assets_dir.exists():
            return None
        candidates = [
            self.assets_dir / category / f"{term.lower()}.jpg",
            self.assets_dir / category / f"{term.lower()}.png",
            self.assets_dir / f"{term.lower()}.jpg",
            self.assets_dir / f"{term.lower()}.png",
        ]
        for candidate in candidates:
            if candidate.is_file():
                return ImageResult(str(candidate), self.name)
        return None


class GeneratedCardProvider:
    """Gera um cartão ilustrado localmente com Pillow (offline e seguro)."""

    name = "generated"

    def __init__(self, cache_dir: str) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_image(self, term: str, category: str, emoji: str, translation: str) -> ImageResult | None:
        try:
            from PIL import Image, ImageDraw, ImageFont
        except Exception:  # pragma: no cover - Pillow opcional
            return None

        key = hashlib.sha1(f"{term}|{emoji}".encode()).hexdigest()[:16]
        out = self.cache_dir / f"card_{key}.png"
        if out.exists():
            return ImageResult(str(out), self.name)

        width, height = 640, 480
        bg = _CATEGORY_COLORS.get(category, (238, 238, 238))
        image = Image.new("RGB", (width, height), bg)
        draw = ImageDraw.Draw(image)

        emoji_font = _load_font(150, emoji=True)
        title_font = _load_font(72)
        small_font = _load_font(36)

        if emoji_font:
            _draw_centered(draw, emoji, width, 150, emoji_font, (30, 30, 30))
        _draw_centered(draw, term.upper(), width, 300, title_font, (20, 20, 20))
        _draw_centered(draw, translation, width, 390, small_font, (70, 70, 70))

        image.save(out)
        return ImageResult(str(out), self.name)


class WikimediaProvider:
    """Baixa uma foto livre do Wikimedia Commons (sem chave de API)."""

    name = "wikimedia"
    API = "https://commons.wikimedia.org/w/api.php"

    def __init__(self, cache_dir: str, timeout: float = 10.0) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout

    def get_image(self, term: str, category: str, emoji: str, translation: str) -> ImageResult | None:
        try:
            import requests
        except Exception:  # pragma: no cover
            return None

        key = hashlib.sha1(term.lower().encode()).hexdigest()[:16]
        out = self.cache_dir / f"wiki_{key}.jpg"
        if out.exists():
            return ImageResult(str(out), self.name)

        try:
            response = requests.get(
                self.API,
                params={
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": f"filetype:bitmap {term}",
                    "gsrnamespace": "6",
                    "gsrlimit": "1",
                    "prop": "imageinfo",
                    "iiprop": "url|extmetadata",
                    "iiurlwidth": "640",
                },
                headers={"User-Agent": "LinguaBot/2.0 (educational bot)"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            pages = response.json().get("query", {}).get("pages", {})
            for page in pages.values():
                info = (page.get("imageinfo") or [{}])[0]
                thumb = info.get("thumburl") or info.get("url")
                if not thumb:
                    continue
                attribution = None
                meta = info.get("extmetadata") or {}
                artist = meta.get("Artist", {}).get("value")
                if artist:
                    attribution = f"Imagem: {_strip_html(artist)} (Wikimedia Commons)"
                image_bytes = requests.get(
                    thumb,
                    headers={"User-Agent": "LinguaBot/2.0 (educational bot)"},
                    timeout=self.timeout,
                )
                image_bytes.raise_for_status()
                out.write_bytes(image_bytes.content)
                return ImageResult(str(out), self.name, attribution)
        except Exception as exc:  # pragma: no cover - depende de rede
            logger.warning("Falha ao buscar imagem para %s: %s", term, exc)
        return None


class ImageService:
    """Combina provedores na ordem de preferência."""

    def __init__(self, providers: list[ImageProvider]) -> None:
        self.providers = providers

    def get_image(self, *, term: str, category: str, emoji: str, translation: str) -> ImageResult | None:
        for provider in self.providers:
            result = provider.get_image(term, category, emoji, translation)
            if result:
                return result
        return None


def build_image_service(
    assets_dir: str,
    cache_dir: str,
    *,
    allow_external: bool = True,
) -> ImageService:
    """Monta o serviço de imagens; ``allow_external=False`` para o modo infantil."""

    providers: list[ImageProvider] = [LocalAssetsProvider(assets_dir)]
    if allow_external:
        providers.append(WikimediaProvider(cache_dir))
    providers.append(GeneratedCardProvider(cache_dir))
    return ImageService(providers)


# ---------------------------------------------------------------------------
# Helpers de desenho
# ---------------------------------------------------------------------------
def _load_font(size: int, emoji: bool = False):
    from PIL import ImageFont

    candidates: list[str] = []
    if emoji:
        candidates += [
            r"C:\Windows\Fonts\seguiemj.ttf",
            "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
            "/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf",
        ]
    candidates += [
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default()
    except Exception:  # pragma: no cover
        return None


def _draw_centered(draw, text: str, width: int, y: int, font, color) -> None:
    if font is None or not text:
        return
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
    except Exception:
        text_width = width // 2
    draw.text(((width - text_width) / 2, y), text, font=font, fill=color)


def _strip_html(value: str) -> str:
    import re

    return re.sub(r"<[^>]+>", "", value).strip()
