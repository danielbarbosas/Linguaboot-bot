"""Modelos de domínio do LinguaBot (enums e estruturas de dados)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class UILang(str, Enum):
    """Idioma da interface (menus, mensagens)."""

    PT = "pt"
    EN = "en"
    ES = "es"


class LearnLang(str, Enum):
    """Idioma que o usuário deseja aprender."""

    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"


class Level(str, Enum):
    """Nível de proficiência do aluno (referência informal ao QECR)."""

    INICIANTE = "iniciante"      # ~A1
    BASICO = "basico"            # ~A2
    INTERMEDIARIO = "intermediario"  # ~B1-B2
    AVANCADO = "avancado"        # ~C1


class Voice(str, Enum):
    """Gênero da voz de referência."""

    FEMININO = "feminino"
    MASCULINO = "masculino"


class Profile(str, Enum):
    """Perfil do usuário."""

    ADULTO = "adulto"
    INFANTIL = "infantil"


class Modality(str, Enum):
    """Modalidade / atividade de aprendizagem."""

    CONVERSACAO = "conversacao"
    PRONUNCIA = "pronuncia"
    GRAMATICA = "gramatica"
    IMAGENS = "imagens"
    EXERCICIOS = "exercicios"
    INFANTIL = "infantil"


class CorrectionMode(str, Enum):
    """Modo de correção na conversação livre."""

    IMEDIATA = "imediata"
    DETALHADA = "detalhada"


@dataclass
class UserProfileData:
    """Perfil persistido de um usuário."""

    telegram_id: int
    ui_lang: UILang = UILang.PT
    learn_lang: LearnLang | None = None
    level: Level | None = None
    voice: Voice = Voice.FEMININO
    profile: Profile = Profile.ADULTO
    modality: Modality | None = None
    correction_mode: CorrectionMode = CorrectionMode.IMEDIATA
    goal: str | None = None
    kids_consent: bool = False
    onboarded: bool = False
    run_key: str = "default"
    id: int | None = None
    first_name: str | None = None


@dataclass
class LearningSession:
    """Estado de uma sessão de aprendizagem, persistível e retomável."""

    telegram_id: int
    mode: Modality | None = None
    module: str | None = None
    lesson_id: str | None = None
    exercise_index: int = 0
    current_item: dict[str, Any] = field(default_factory=dict)
    awaiting: str | None = None  # o que o bot espera (ex.: "pronunciation", "answer")
    updated_at: str | None = None
