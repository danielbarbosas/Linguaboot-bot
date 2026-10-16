"""Aulas de gramática por idioma e nível, com exercícios interativos."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..models import LearnLang, Level


@dataclass(frozen=True)
class Exercise:
    id: str
    kind: str  # "multiple_choice" | "fill_blank"
    prompt: str
    options: tuple[str, ...] = ()
    answer: str = ""
    explanation: str = ""


@dataclass(frozen=True)
class Lesson:
    id: str
    lang: LearnLang
    level: Level
    title: str
    explanation: str
    examples: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    exercises: tuple[Exercise, ...] = field(default_factory=tuple)


def _mc(eid, prompt, options, answer, explanation=""):
    return Exercise(eid, "multiple_choice", prompt, tuple(options), answer, explanation)


def _fb(eid, prompt, answer, explanation=""):
    return Exercise(eid, "fill_blank", prompt, (), answer, explanation)


_EN_LESSONS = [
    Lesson(
        id="en-verb-to-be",
        lang=LearnLang.EN,
        level=Level.INICIANTE,
        title="O verbo TO BE (am / is / are)",
        explanation=(
            "O verbo TO BE significa ser/estar. No presente ele muda conforme o sujeito:\n"
            "• I am (eu sou/estou)\n• You/We/They are\n• He/She/It is\n\n"
            "É a base para quase tudo em inglês."
        ),
        examples=(
            ("I am a student.", "Eu sou um estudante."),
            ("She is happy.", "Ela está feliz."),
            ("They are at home.", "Eles estão em casa."),
        ),
        exercises=(
            _mc("en-be-1", "Complete: She ___ my friend.", ("am", "is", "are"), "is",
                "Com 'she' (3ª pessoa do singular) usamos 'is'."),
            _mc("en-be-2", "Complete: We ___ tired.", ("am", "is", "are"), "are",
                "Com 'we' usamos 'are'."),
            _fb("en-be-3", "Escreva a forma correta de TO BE: I ___ from Brazil.", "am",
                "Com 'I' sempre usamos 'am'."),
        ),
    ),
    Lesson(
        id="en-present-simple",
        lang=LearnLang.EN,
        level=Level.BASICO,
        title="Presente simples (hábitos e rotina)",
        explanation=(
            "O presente simples descreve rotinas e fatos. Regras rápidas:\n"
            "• He / She / It → verbo + s (he works)\n"
            "• I / You / We / They → verbo normal (I work)\n"
            "• Negativa: don't / doesn't (I don't work / he doesn't work)\n"
            "• Pergunta: Do / Does (Do you work? Does she work?)"
        ),
        examples=(
            ("I work every day.", "Eu trabalho todos os dias."),
            ("She studies English.", "Ela estuda inglês."),
            ("They don't watch TV.", "Eles não assistem TV."),
        ),
        exercises=(
            _mc("en-ps-1", "Complete: He ___ English every night.", ("study", "studies", "studys"),
                "studies", "Verbos terminados em 'y' após consoante → 'ies' com he/she/it."),
            _mc("en-ps-2", "Qual a negativa correta de 'She likes coffee'?",
                ("She don't like coffee.", "She doesn't likes coffee.", "She doesn't like coffee."),
                "She doesn't like coffee.", "Na negativa com 'doesn't' o verbo fica na forma base."),
            _fb("en-ps-3", "Complete a pergunta: ___ you speak Spanish?", "Do",
                "Perguntas no presente simples com 'you' começam com 'Do'."),
        ),
    ),
    Lesson(
        id="en-plurals",
        lang=LearnLang.EN,
        level=Level.INICIANTE,
        title="Plural dos substantivos",
        explanation=(
            "Regra geral: acrescenta-se -s (book → books).\n"
            "Terminados em -s, -x, -ch, -sh: acrescenta-se -es (box → boxes).\n"
            "Terminados em consoante + y: -y → -ies (city → cities)."
        ),
        examples=(
            ("one book, two books", "um livro, dois livros"),
            ("one box, two boxes", "uma caixa, duas caixas"),
            ("one city, two cities", "uma cidade, duas cidades"),
        ),
        exercises=(
            _mc("en-pl-1", "Qual é o plural de 'city'?", ("citys", "cities", "cityes"), "cities",
                "Consoante + y → troca o 'y' por 'ies'."),
            _fb("en-pl-2", "Plural de 'box': ___", "boxes",
                "Terminados em -x recebem 'es'."),
        ),
    ),
]

_ES_LESSONS = [
    Lesson(
        id="es-ser-estar",
        lang=LearnLang.ES,
        level=Level.INICIANTE,
        title="SER x ESTAR",
        explanation=(
            "Espanhol tem dois verbos para 'ser/estar':\n"
            "• SER → características permanentes (Soy brasileño.)\n"
            "• ESTAR → estados temporários e localização (Estoy cansado. / Estoy en casa.)"
        ),
        examples=(
            ("Yo soy estudiante.", "Eu sou estudante."),
            ("Estoy muy feliz.", "Estou muito feliz."),
            ("Ella está en el parque.", "Ela está no parque."),
        ),
        exercises=(
            _mc("es-se-1", "Complete: Yo ___ cansado hoy.", ("soy", "estoy", "es"), "estoy",
                "Estado temporário → ESTAR."),
            _mc("es-se-2", "Complete: Ella ___ profesora.", ("es", "está", "estoy"), "es",
                "Profissão/identidade → SER."),
        ),
    ),
    Lesson(
        id="es-genero",
        lang=LearnLang.ES,
        level=Level.BASICO,
        title="Gênero dos substantivos (el / la)",
        explanation=(
            "Em espanhol os substantivos são masculinos (el) ou femininos (la).\n"
            "Muitas palavras terminadas em -o são masculinas; em -a, femininas.\n"
            "Há exceções: el día, la mano."
        ),
        examples=(
            ("el libro", "o livro"),
            ("la casa", "a casa"),
            ("el problema", "o problema (exceção)"),
        ),
        exercises=(
            _mc("es-g-1", "Qual artigo? ___ mesa está sucia.", ("El", "La", "Los"), "La",
                "'Mesa' termina em -a, geralmente feminino → 'La'."),
            _mc("es-g-2", "Qual artigo? ___ problema es difícil.", ("El", "La", "Las"), "El",
                "'Problema' é masculino mesmo terminando em -a (exceção)."),
        ),
    ),
]

GRAMMAR: dict[LearnLang, list[Lesson]] = {
    LearnLang.EN: _EN_LESSONS,
    LearnLang.ES: _ES_LESSONS,
}


def get_lessons(lang: LearnLang, level: Level | None = None) -> list[Lesson]:
    lessons = GRAMMAR.get(lang, [])
    if level is not None:
        order = list(Level)
        max_index = order.index(level)
        lessons = [le for le in lessons if order.index(le.level) <= max_index]
    return lessons


def get_lesson(lang: LearnLang, lesson_id: str) -> Lesson | None:
    for lesson in GRAMMAR.get(lang, []):
        if lesson.id == lesson_id:
            return lesson
    return None
