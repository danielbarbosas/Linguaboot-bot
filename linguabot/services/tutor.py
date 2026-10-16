"""Serviço pedagógico: correção, conversação e avaliação de pronúncia.

Princípios de honestidade técnica:
- A avaliação de pronúncia compara o TEXTO reconhecido com o esperado. Isso
  NÃO mede fonemas nem entonação. Quando não há confiança, dizemos isso.
- Sem um LLM configurado, a correção de conversação é limitada a regras
  simples e explícitas (nunca fingimos uma análise gramatical completa).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from ..models import CorrectionMode, Level, Modality
from .llm import LLMClient


# ---------------------------------------------------------------------------
# Avaliação de pronúncia (baseada em texto)
# ---------------------------------------------------------------------------
@dataclass
class PronResult:
    status: str  # "ok" | "close" | "different" | "unknown"
    similarity: float
    heard: str
    target: str
    missing: list[str] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)

    @property
    def confident(self) -> bool:
        return self.status != "unknown"


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def evaluate_pronunciation(target: str, recognized: str | None) -> PronResult:
    """Compara a fala reconhecida com a palavra/frase esperada."""

    if not recognized or not recognized.strip():
        return PronResult("unknown", 0.0, recognized or "", target)

    norm_target = _normalize(target)
    norm_heard = _normalize(recognized)
    similarity = SequenceMatcher(None, norm_target, norm_heard).ratio()

    target_words = norm_target.split()
    heard_words = norm_heard.split()
    missing = [w for w in target_words if w not in heard_words]
    extra = [w for w in heard_words if w not in target_words]

    if norm_target == norm_heard or similarity >= 0.9:
        status = "ok"
    elif similarity >= 0.6:
        status = "close"
    else:
        status = "different"

    return PronResult(status, round(similarity, 3), recognized, target, missing, extra)


def pronunciation_feedback(result: PronResult, phonetic: str | None = None) -> str:
    """Gera feedback textual honesto a partir do resultado."""

    if result.status == "unknown":
        return (
            "🎧 Não consegui reconhecer a fala com confiança "
            "(pode ser ruído, áudio curto ou limitação do reconhecimento). "
            "Tente gravar de novo, num lugar mais silencioso."
        )

    lines: list[str] = [f"🎤 Ouvi: “{result.heard}”", f"🎯 Esperado: “{result.target}”"]

    if result.status == "ok":
        lines.append("✅ Muito bom! A fala reconhecida corresponde ao esperado.")
    elif result.status == "close":
        lines.append("🙂 Quase lá! Foi bem parecido, dá para ajustar um detalhe.")
    else:
        lines.append("🔁 Vamos tentar de novo com calma.")

    if result.missing:
        lines.append("Antes faltou: " + ", ".join(result.missing))
    if result.extra:
        lines.append("Sobrou/pareceu: " + ", ".join(result.extra))
    if phonetic:
        lines.append(f"💡 Dica de pronúncia: “{phonetic}”")

    lines.append(
        "ℹ️ Esta avaliação compara o texto reconhecido, não mede fonemas nem entonação."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Correção por regras (fallback offline, sobretudo para inglês)
# ---------------------------------------------------------------------------
_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bi is\b"), "i am"),
    (re.compile(r"\bi are\b"), "i am"),
    (re.compile(r"\b(he|she|it) are\b"), r"\1 is"),
    (re.compile(r"\b(he|she|it) (do)\b"), r"\1 does"),
    (re.compile(r"\bthey is\b"), "they are"),
    (re.compile(r"\bwe is\b"), "we are"),
    (re.compile(r"\ba apple\b"), "an apple"),
]


def rule_corrections(text: str) -> list[str]:
    """Retorna sugestões simples de correção (limitadas)."""

    suggestions: list[str] = []
    lowered = text.lower()
    for pattern, replacement in _RULES:
        if pattern.search(lowered):
            fixed = pattern.sub(replacement, lowered)
            suggestions.append(fixed.strip().capitalize())
    if text and text[0].islower():
        suggestions.append(text[0].upper() + text[1:])
    return list(dict.fromkeys(suggestions))


# ---------------------------------------------------------------------------
# Tutor (conversação / infantil)
# ---------------------------------------------------------------------------
_TOPICS = [
    "your favorite food",
    "your daily routine",
    "a place you would like to visit",
    "your hobbies",
    "last weekend",
]


class TutorService:
    def __init__(self, llm: LLMClient, learn_lang_name: str = "inglês") -> None:
        self.llm = llm
        self.learn_lang_name = learn_lang_name

    # ------------------------------------------------------------------
    def conversation(
        self,
        *,
        student_text: str,
        level: Level | None,
        correction_mode: CorrectionMode = CorrectionMode.IMEDIATA,
        ui_lang: str = "pt",
    ) -> str:
        system = (
            f"Você é um professor de {self.learn_lang_name} amigável, para o nível "
            f"{(level.value if level else 'iniciante')}. "
            "Responda no idioma estudado e depois explique a correção em português. "
            "Seja breve."
        )
        if correction_mode == CorrectionMode.DETALHADA:
            system += " Explique a correção com detalhes e dê uma alternativa mais natural."
        else:
            system += " Destaque apenas a correção mais importante e siga a conversa."

        prompt = f'O aluno escreveu: "{student_text}". Corrija se necessário e continue a conversa.'
        reply = self.llm.generate(prompt, system=system)
        if reply:
            return reply

        # Fallback offline: honesto e útil.
        parts = []
        corrections = rule_corrections(student_text)
        if corrections:
            parts.append("✍️ Sugestões: " + " | ".join(corrections))
        parts.append(
            "💬 Boa! Continue praticando. Conte-me mais: "
            f"what about {_TOPICS[len(student_text) % len(_TOPICS)]}?"
        )
        if not self.llm.available:
            parts.append(
                "ℹ️ A correção automática detalhada está limitada (nenhum modelo de "
                "linguagem configurado)."
            )
        return "\n".join(parts)

    # ------------------------------------------------------------------
    def kids_message(self, *, child_text: str, target: str, accepted: bool) -> str:
        if accepted:
            return f"🎉 Muito bem! Você disse {target}! 👏"
        return f"⭐ Boa tentativa! Vamos ouvir de novo: {target}. Você consegue! 💪"
