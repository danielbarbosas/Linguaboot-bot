"""Teclados inline (botões) do LinguaBot.

Todos os botões executam ações reais; o ``callback_data`` segue o padrão
``area:acao[:parametro]`` e é tratado pelo roteador central.
"""

from __future__ import annotations

from telegram import InlineKeyboardButton as Btn
from telegram import InlineKeyboardMarkup as Markup

from ..content.grammar import Lesson
from ..content.languages import list_languages
from ..models import LearnLang, Level, Modality, Profile, UILang, Voice
from .texts import t


def _rows(*rows: list[Btn]) -> Markup:
    return Markup([list(row) for row in rows])


# ---------------------------------------------------------------------------
def ui_lang_menu(prefix: str = "onb") -> Markup:
    return _rows(
        [Btn("🇧🇷 Português", callback_data=f"{prefix}:ui:pt")],
        [Btn("🇬🇧 English", callback_data=f"{prefix}:ui:en")],
        [Btn("🇪🇸 Español", callback_data=f"{prefix}:ui:es")],
    )


def learn_lang_menu(ui: UILang, prefix: str = "onb") -> Markup:
    rows = [
        [Btn(f"{lang.flag} {lang.name_pt}", callback_data=f"{prefix}:learn:{lang.code.value}")]
        for lang in list_languages()
    ]
    rows.append([Btn(t("btn_back", ui), callback_data="menu:main")])
    return _rows(*rows)


def level_menu(ui: UILang, prefix: str = "onb") -> Markup:
    return _rows(
        [Btn(t("level_iniciante", ui), callback_data=f"{prefix}:level:{Level.INICIANTE.value}")],
        [Btn(t("level_basico", ui), callback_data=f"{prefix}:level:{Level.BASICO.value}")],
        [Btn(t("level_intermediario", ui), callback_data=f"{prefix}:level:{Level.INTERMEDIARIO.value}")],
        [Btn(t("level_avancado", ui), callback_data=f"{prefix}:level:{Level.AVANCADO.value}")],
    )


def voice_menu(ui: UILang, prefix: str = "onb") -> Markup:
    return _rows(
        [Btn(t("voice_feminino", ui), callback_data=f"{prefix}:voice:{Voice.FEMININO.value}")],
        [Btn(t("voice_masculino", ui), callback_data=f"{prefix}:voice:{Voice.MASCULINO.value}")],
    )


def profile_menu(ui: UILang) -> Markup:
    return _rows(
        [Btn(t("profile_adulto", ui), callback_data=f"onb:profile:{Profile.ADULTO.value}")],
        [Btn(t("profile_infantil", ui), callback_data=f"onb:profile:{Profile.INFANTIL.value}")],
    )


def modality_menu(ui: UILang, prefix: str = "onb") -> Markup:
    return _rows(
        [Btn(t("mod_conversacao", ui), callback_data=f"{prefix}:mod:{Modality.CONVERSACAO.value}")],
        [Btn(t("mod_gramatica", ui), callback_data=f"{prefix}:mod:{Modality.GRAMATICA.value}")],
        [Btn(t("mod_pronuncia", ui), callback_data=f"{prefix}:mod:{Modality.PRONUNCIA.value}")],
        [Btn(t("mod_imagens", ui), callback_data=f"{prefix}:mod:{Modality.IMAGENS.value}")],
        [Btn(t("mod_exercicios", ui), callback_data=f"{prefix}:mod:{Modality.EXERCICIOS.value}")],
        [Btn(t("mod_infantil", ui), callback_data=f"{prefix}:mod:{Modality.INFANTIL.value}")],
    )


def goal_menu(ui: UILang) -> Markup:
    goals = [
        ("travel", "✈️ Viagem"),
        ("work", "💼 Trabalho"),
        ("study", "🎓 Estudos"),
        ("culture", "🎬 Cultura"),
        ("fun", "😄 Diversão"),
    ]
    rows = [[Btn(label, callback_data=f"onb:goal:{key}")] for key, label in goals]
    return _rows(*rows)


# ---------------------------------------------------------------------------
def resume_menu(ui: UILang) -> Markup:
    return _rows(
        [Btn(t("resume_continue", ui), callback_data="resume:continue")],
        [Btn(t("resume_restart", ui), callback_data="resume:restart")],
        [Btn(t("resume_settings", ui), callback_data="menu:settings")],
        [Btn(t("resume_progress", ui), callback_data="menu:progress")],
    )


def main_menu(ui: UILang, *, kids_enabled: bool = True) -> Markup:
    rows = [
        [Btn(t("mod_conversacao", ui), callback_data="go:conversation")],
        [Btn(t("mod_pronuncia", ui), callback_data="go:pronunciation")],
        [Btn(t("mod_gramatica", ui), callback_data="go:grammar")],
        [Btn(t("mod_imagens", ui), callback_data="go:images")],
    ]
    if kids_enabled:
        rows.append([Btn(t("mod_infantil", ui), callback_data="go:kids")])
    rows += [
        [Btn(t("mod_exercicios", ui), callback_data="go:assess")],
        [
            Btn(t("menu_progress", ui), callback_data="menu:progress"),
            Btn(t("menu_settings", ui), callback_data="menu:settings"),
        ],
        [Btn(t("menu_help", ui), callback_data="menu:help")],
    ]
    return _rows(*rows)


def settings_menu(ui: UILang) -> Markup:
    return _rows(
        [Btn(t("settings_ui_lang", ui), callback_data="set:ui")],
        [Btn(t("settings_learn_lang", ui), callback_data="set:learn")],
        [Btn(t("settings_level", ui), callback_data="set:level")],
        [Btn(t("settings_voice", ui), callback_data="set:voice")],
        [Btn(t("settings_modality", ui), callback_data="set:mod")],
        [Btn(t("settings_correction", ui), callback_data="set:corr")],
        [Btn(t("settings_privacy", ui), callback_data="menu:privacy")],
        [Btn(t("menu_main", ui), callback_data="menu:main")],
    )


def correction_menu(ui: UILang) -> Markup:
    return _rows(
        [Btn(t("corr_imediata", ui), callback_data="set:corr:imediata")],
        [Btn(t("corr_detalhada", ui), callback_data="set:corr:detalhada")],
        [Btn(t("btn_back", ui), callback_data="menu:settings")],
    )


# ---------------------------------------------------------------------------
def grammar_lessons_menu(ui: UILang, lessons: list[Lesson]) -> Markup:
    rows = [[Btn(f"📖 {le.title}", callback_data=f"gram:open:{le.id}")] for le in lessons]
    rows.append([Btn(t("btn_menu", ui), callback_data="menu:main")])
    return _rows(*rows)


def grammar_options_menu(ui: UILang, exercise_id: str, options: tuple[str, ...]) -> Markup:
    rows = [
        [Btn(opt, callback_data=f"gram:ans:{exercise_id}:{i}")]
        for i, opt in enumerate(options)
    ]
    rows.append([Btn(t("btn_menu", ui), callback_data="menu:main")])
    return _rows(*rows)


# ---------------------------------------------------------------------------
def pronunciation_menu(ui: UILang) -> Markup:
    return _rows(
        [Btn(t("pron_repeat", ui), callback_data="pron:repeat")],
        [Btn(t("pron_next", ui), callback_data="pron:next")],
        [Btn(t("btn_menu", ui), callback_data="menu:main")],
    )


def image_menu(ui: UILang) -> Markup:
    return _rows(
        [Btn(t("img_repeat", ui), callback_data="img:repeat")],
        [Btn(t("img_pronounce", ui), callback_data="img:pronounce")],
        [Btn(t("img_next", ui), callback_data="img:next")],
        [Btn(t("btn_menu", ui), callback_data="menu:main")],
    )


# ---------------------------------------------------------------------------
def kids_consent_menu(ui: UILang) -> Markup:
    return _rows(
        [Btn(t("kids_consent_btn", ui), callback_data="kids:consent")],
        [Btn(t("btn_menu", ui), callback_data="menu:main")],
    )


def kids_activity_menu(ui: UILang) -> Markup:
    return _rows(
        [Btn(t("img_repeat", ui), callback_data="kid:repeat")],
        [Btn(t("img_next", ui), callback_data="kid:next")],
        [Btn(t("btn_menu", ui), callback_data="menu:main")],
    )


# ---------------------------------------------------------------------------
def assessment_start_menu(ui: UILang) -> Markup:
    return _rows(
        [Btn(t("assess_start", ui), callback_data="assess:start")],
        [Btn(t("btn_menu", ui), callback_data="menu:main")],
    )


def assessment_options_menu(ui: UILang, index: int, options: tuple[str, ...]) -> Markup:
    rows = [
        [Btn(opt, callback_data=f"assess:ans:{index}:{i}")] for i, opt in enumerate(options)
    ]
    return _rows(*rows)


def progress_menu(ui: UILang) -> Markup:
    return _rows(
        [Btn(t("mod_exercicios", ui), callback_data="go:assess")],
        [Btn(t("menu_main", ui), callback_data="menu:main")],
    )


def privacy_menu(ui: UILang) -> Markup:
    return _rows(
        [Btn("📂 Meus dados", callback_data="priv:view")],
        [Btn("🗑️ Apagar meus dados", callback_data="priv:delete")],
        [Btn(t("menu_main", ui), callback_data="menu:main")],
    )


def confirm_delete_menu(ui: UILang) -> Markup:
    return _rows(
        [Btn(t("privacy_confirm_yes", ui), callback_data="priv:confirm")],
        [Btn(t("privacy_cancel", ui), callback_data="menu:privacy")],
    )


def back_to_menu(ui: UILang) -> Markup:
    return _rows([Btn(t("menu_main", ui), callback_data="menu:main")])
