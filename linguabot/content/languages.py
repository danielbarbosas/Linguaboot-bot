"""Idiomas suportados e metadados de vozes / modelos.

As vozes listadas são da Microsoft Edge (pacote ``edge-tts``), gratuito e sem
chave de API. Cada idioma tem pelo menos uma voz masculina e uma feminina,
para que a escolha de voz realmente altere o áudio gerado.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..models import LearnLang, Voice


@dataclass(frozen=True)
class Language:
    code: LearnLang
    name_pt: str
    name_native: str
    flag: str
    gtts_code: str
    edge_voices: dict[Voice, str]
    vosk_model: str | None
    vosk_model_large: str | None = None
    has_grammar: bool = False
    has_vocabulary: bool = False
    extra: dict[str, str] = field(default_factory=dict)


LANGUAGES: dict[LearnLang, Language] = {
    LearnLang.EN: Language(
        code=LearnLang.EN,
        name_pt="Inglês",
        name_native="English",
        flag="🇬🇧",
        gtts_code="en",
        edge_voices={
            Voice.FEMININO: "en-US-AriaNeural",
            Voice.MASCULINO: "en-US-GuyNeural",
        },
        vosk_model="vosk-model-small-en-us-0.15",
        vosk_model_large="vosk-model-en-us-0.22",
        has_grammar=True,
        has_vocabulary=True,
    ),
    LearnLang.ES: Language(
        code=LearnLang.ES,
        name_pt="Espanhol",
        name_native="Español",
        flag="🇪🇸",
        gtts_code="es",
        edge_voices={
            Voice.FEMININO: "es-ES-ElviraNeural",
            Voice.MASCULINO: "es-ES-AlvaroNeural",
        },
        vosk_model="vosk-model-small-es-0.42",
        vosk_model_large="vosk-model-es-0.42",
        has_grammar=True,
        has_vocabulary=True,
    ),
    LearnLang.FR: Language(
        code=LearnLang.FR,
        name_pt="Francês",
        name_native="Français",
        flag="🇫🇷",
        gtts_code="fr",
        edge_voices={
            Voice.FEMININO: "fr-FR-DeniseNeural",
            Voice.MASCULINO: "fr-FR-HenriNeural",
        },
        vosk_model="vosk-model-small-fr-0.22",
        vosk_model_large="vosk-model-fr-0.22",
        has_vocabulary=True,
    ),
    LearnLang.DE: Language(
        code=LearnLang.DE,
        name_pt="Alemão",
        name_native="Deutsch",
        flag="🇩🇪",
        gtts_code="de",
        edge_voices={
            Voice.FEMININO: "de-DE-KatjaNeural",
            Voice.MASCULINO: "de-DE-ConradNeural",
        },
        vosk_model="vosk-model-small-de-0.15",
        vosk_model_large="vosk-model-de-0.15",
        has_vocabulary=True,
    ),
    LearnLang.IT: Language(
        code=LearnLang.IT,
        name_pt="Italiano",
        name_native="Italiano",
        flag="🇮🇹",
        gtts_code="it",
        edge_voices={
            Voice.FEMININO: "it-IT-ElsaNeural",
            Voice.MASCULINO: "it-IT-DiegoNeural",
        },
        vosk_model="vosk-model-small-it-0.22",
        vosk_model_large="vosk-model-it-0.22",
        has_vocabulary=True,
    ),
}


def get_language(code: LearnLang | str) -> Language:
    """Retorna os metadados de um idioma; aceita o enum ou a string."""

    if isinstance(code, str):
        code = LearnLang(code)
    return LANGUAGES[code]


def list_languages() -> list[Language]:
    return list(LANGUAGES.values())
