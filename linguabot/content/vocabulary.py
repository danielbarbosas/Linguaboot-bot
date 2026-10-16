"""Banco de vocabulário por idioma, categoria e nível.

Cada palavra traz tradução em português, dica fonética acessível (escrita de
forma simples, sem prometer notação fonética precisa), emoji e categoria.
Categorias infantis são marcadas com ``kids=True`` e as palavras seguras para
crianças com ``kid_safe=True``.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..models import LearnLang, Level


@dataclass(frozen=True)
class Word:
    term: str
    translation: str
    phonetic: str
    emoji: str
    category: str
    level: Level = Level.INICIANTE
    kid_safe: bool = True


ADULT_CATEGORIES = ("animals", "colors", "food", "objects", "places", "actions")
KID_CATEGORIES = ("animals", "colors", "numbers", "shapes", "food", "toys")


def _w(term, translation, phonetic, emoji, category, level=Level.INICIANTE, kid_safe=True):
    return Word(term, translation, phonetic, emoji, category, level, kid_safe)


# ---------------------------------------------------------------------------
# Inglês
# ---------------------------------------------------------------------------
_EN = [
    # animais
    _w("dog", "cachorro", "dóg", "🐶", "animals"),
    _w("cat", "gato", "két", "🐱", "animals"),
    _w("bird", "pássaro", "bârd", "🐦", "animals"),
    _w("fish", "peixe", "fich", "🐟", "animals"),
    _w("horse", "cavalo", "hórs", "🐴", "animals", Level.BASICO),
    # cores
    _w("red", "vermelho", "réd", "🔴", "colors"),
    _w("blue", "azul", "blú", "🔵", "colors"),
    _w("green", "verde", "grín", "🟢", "colors"),
    _w("yellow", "amarelo", "iélou", "🟡", "colors"),
    # números
    _w("one", "um", "uân", "1️⃣", "numbers"),
    _w("two", "dois", "tú", "2️⃣", "numbers"),
    _w("three", "três", "thrí", "3️⃣", "numbers"),
    # formas
    _w("circle", "círculo", "sârcol", "⭕", "shapes"),
    _w("square", "quadrado", "skuér", "⬜", "shapes"),
    _w("triangle", "triângulo", "tráiangol", "🔺", "shapes"),
    # comida
    _w("apple", "maçã", "épel", "🍎", "food"),
    _w("bread", "pão", "bréd", "🍞", "food"),
    _w("banana", "banana", "banâna", "🍌", "food"),
    _w("milk", "leite", "milk", "🥛", "food"),
    # objetos
    _w("book", "livro", "búk", "📚", "objects"),
    _w("chair", "cadeira", "tchér", "🪑", "objects", Level.BASICO),
    _w("table", "mesa", "têibol", "🪑", "objects", Level.BASICO),
    _w("car", "carro", "kár", "🚗", "objects"),
    # lugares
    _w("house", "casa", "háus", "🏠", "places"),
    _w("school", "escola", "skúl", "🏫", "places", Level.BASICO),
    _w("park", "parque", "párk", "🏞️", "places"),
    # ações
    _w("run", "correr", "rân", "🏃", "actions"),
    _w("jump", "pular", "djâmp", "🦘", "actions"),
    _w("eat", "comer", "ít", "🍽️", "actions"),
    _w("read", "ler", "ríd", "📖", "actions", Level.BASICO),
]

# ---------------------------------------------------------------------------
# Espanhol
# ---------------------------------------------------------------------------
_ES = [
    _w("perro", "cachorro", "pérro", "🐶", "animals"),
    _w("gato", "gato", "gáto", "🐱", "animals"),
    _w("pájaro", "pássaro", "páharo", "🐦", "animals"),
    _w("pez", "peixe", "péth", "🐟", "animals"),
    _w("rojo", "vermelho", "rrôho", "🔴", "colors"),
    _w("azul", "azul", "athúl", "🔵", "colors"),
    _w("verde", "verde", "bérde", "🟢", "colors"),
    _w("uno", "um", "úno", "1️⃣", "numbers"),
    _w("dos", "dois", "dós", "2️⃣", "numbers"),
    _w("tres", "três", "trés", "3️⃣", "numbers"),
    _w("círculo", "círculo", "thírculo", "⭕", "shapes"),
    _w("cuadrado", "quadrado", "cuadrádo", "⬜", "shapes"),
    _w("manzana", "maçã", "manthána", "🍎", "food"),
    _w("pan", "pão", "pán", "🍞", "food"),
    _w("libro", "livro", "líbro", "📚", "objects"),
    _w("casa", "casa", "cása", "🏠", "places"),
    _w("escuela", "escola", "escuela", "🏫", "places", Level.BASICO),
    _w("correr", "correr", "corrér", "🏃", "actions"),
    _w("comer", "comer", "comér", "🍽️", "actions"),
]

# ---------------------------------------------------------------------------
# Francês / Alemão / Italiano (vocabulário básico)
# ---------------------------------------------------------------------------
_FR = [
    _w("chien", "cachorro", "chiã", "🐶", "animals"),
    _w("chat", "gato", "chá", "🐱", "animals"),
    _w("rouge", "vermelho", "rrúj", "🔴", "colors"),
    _w("bleu", "azul", "blê", "🔵", "colors"),
    _w("pain", "pão", "pã", "🍞", "food"),
    _w("livre", "livro", "lívr", "📚", "objects"),
    _w("maison", "casa", "mezã", "🏠", "places"),
]

_DE = [
    _w("Hund", "cachorro", "hund", "🐶", "animals"),
    _w("Katze", "gato", "kátsa", "🐱", "animals"),
    _w("rot", "vermelho", "rôt", "🔴", "colors"),
    _w("blau", "azul", "blau", "🔵", "colors"),
    _w("Brot", "pão", "brôt", "🍞", "food"),
    _w("Buch", "livro", "búr", "📚", "objects"),
    _w("Haus", "casa", "haus", "🏠", "places"),
]

_IT = [
    _w("cane", "cachorro", "káne", "🐶", "animals"),
    _w("gatto", "gato", "gátto", "🐱", "animals"),
    _w("rosso", "vermelho", "rrósso", "🔴", "colors"),
    _w("blu", "azul", "blú", "🔵", "colors"),
    _w("pane", "pão", "páne", "🍞", "food"),
    _w("libro", "livro", "líbro", "📚", "objects"),
    _w("casa", "casa", "cása", "🏠", "places"),
]

VOCABULARY: dict[LearnLang, list[Word]] = {
    LearnLang.EN: _EN,
    LearnLang.ES: _ES,
    LearnLang.FR: _FR,
    LearnLang.DE: _DE,
    LearnLang.IT: _IT,
}


def get_words(
    lang: LearnLang,
    *,
    level: Level | None = None,
    category: str | None = None,
    kids_only: bool = False,
) -> list[Word]:
    """Filtra o vocabulário por idioma, nível, categoria e público."""

    words = VOCABULARY.get(lang, [])
    if kids_only:
        words = [w for w in words if w.kid_safe and w.category in KID_CATEGORIES]
    if category:
        words = [w for w in words if w.category == category]
    if level is not None:
        order = list(Level)
        max_index = order.index(level)
        words = [w for w in words if order.index(w.level) <= max_index]
    return words


def get_word(lang: LearnLang, term: str) -> Word | None:
    for word in VOCABULARY.get(lang, []):
        if word.term.lower() == term.lower():
            return word
    return None


def categories(lang: LearnLang, *, kids_only: bool = False) -> list[str]:
    words = get_words(lang, kids_only=kids_only)
    seen: list[str] = []
    for word in words:
        if word.category not in seen:
            seen.append(word.category)
    return seen
