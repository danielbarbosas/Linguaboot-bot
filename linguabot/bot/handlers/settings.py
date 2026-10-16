"""Configurações do usuário e privacidade (LGPD)."""

from __future__ import annotations

import json

from telegram import Update
from telegram.ext import ContextTypes

from ...models import CorrectionMode, LearnLang, Level, Modality, UILang, UserProfileData, Voice
from .. import keyboards as kb
from ..context import get_services
from ..texts import t
from .common import reply as reply_text, safe_edit


# ---------------------------------------------------------------------------
# Menus de configuração
# ---------------------------------------------------------------------------
async def show_settings(update, context, profile: UserProfileData, params=None) -> None:
    await safe_edit(update.callback_query, t("settings_title", profile.ui_lang), reply_markup=kb.settings_menu(profile.ui_lang))


async def choose_ui(update, context, profile, params=None) -> None:
    await safe_edit(update.callback_query, t("choose_ui_lang", profile.ui_lang), reply_markup=kb.ui_lang_menu("set"))


async def apply_ui(update, context, profile, params) -> None:
    services = get_services(context)
    ui = UILang(params[0])
    services.storage.users.update(profile.telegram_id, ui_lang=ui.value)
    profile.ui_lang = ui
    await safe_edit(update.callback_query, t("saved", ui), reply_markup=kb.settings_menu(ui))


async def choose_learn(update, context, profile, params=None) -> None:
    await safe_edit(update.callback_query, t("choose_learn_lang", profile.ui_lang), reply_markup=kb.learn_lang_menu(profile.ui_lang, "set"))


async def apply_learn(update, context, profile, params) -> None:
    services = get_services(context)
    lang = LearnLang(params[0])
    services.storage.users.update(profile.telegram_id, learn_lang=lang.value)
    profile.learn_lang = lang
    await safe_edit(update.callback_query, t("saved", profile.ui_lang), reply_markup=kb.settings_menu(profile.ui_lang))


async def choose_level(update, context, profile, params=None) -> None:
    await safe_edit(update.callback_query, t("choose_level", profile.ui_lang), reply_markup=kb.level_menu(profile.ui_lang, "set"))


async def apply_level(update, context, profile, params) -> None:
    services = get_services(context)
    level = Level(params[0])
    services.storage.users.update(profile.telegram_id, level=level.value)
    profile.level = level
    await safe_edit(update.callback_query, t("saved", profile.ui_lang), reply_markup=kb.settings_menu(profile.ui_lang))


async def choose_voice(update, context, profile, params=None) -> None:
    note = t("choose_voice", profile.ui_lang)
    if not get_services(context).speech.supports_gender:
        note += "\n\n" + t("err_voice_gender", profile.ui_lang)
    await safe_edit(update.callback_query, note, reply_markup=kb.voice_menu(profile.ui_lang, "set"))


async def apply_voice(update, context, profile, params) -> None:
    services = get_services(context)
    voice = Voice(params[0])
    services.storage.users.update(profile.telegram_id, voice=voice.value)
    profile.voice = voice
    await safe_edit(update.callback_query, t("saved", profile.ui_lang), reply_markup=kb.settings_menu(profile.ui_lang))


async def choose_mod(update, context, profile, params=None) -> None:
    await safe_edit(update.callback_query, t("choose_modality", profile.ui_lang), reply_markup=kb.modality_menu(profile.ui_lang, "set"))


async def apply_mod(update, context, profile, params) -> None:
    services = get_services(context)
    mod = Modality(params[0])
    services.storage.users.update(profile.telegram_id, modality=mod.value)
    profile.modality = mod
    await safe_edit(update.callback_query, t("saved", profile.ui_lang), reply_markup=kb.settings_menu(profile.ui_lang))


async def choose_corr(update, context, profile, params=None) -> None:
    await safe_edit(update.callback_query, t("settings_correction", profile.ui_lang), reply_markup=kb.correction_menu(profile.ui_lang))


async def apply_corr(update, context, profile, params) -> None:
    services = get_services(context)
    mode = CorrectionMode(params[0])
    services.storage.users.update(profile.telegram_id, correction_mode=mode.value)
    profile.correction_mode = mode
    await safe_edit(update.callback_query, t("saved", profile.ui_lang), reply_markup=kb.settings_menu(profile.ui_lang))


# ---------------------------------------------------------------------------
# Privacidade
# ---------------------------------------------------------------------------
async def show_privacy(update, context, profile: UserProfileData, params=None) -> None:
    await safe_edit(update.callback_query, t("privacy_title", profile.ui_lang) + "\n\n" + t("privacy_body", profile.ui_lang), reply_markup=kb.privacy_menu(profile.ui_lang))


async def view_data(update, context, profile: UserProfileData, params=None) -> None:
    services = get_services(context)
    data = services.storage.users.export(profile.telegram_id)
    summary = {
        "perfil": data.get("users", [{}])[0] if data.get("users") else {},
        "progresso_registros": len(data.get("progress", [])),
        "avaliacoes": len(data.get("assessments", [])),
        "consentimentos": data.get("consents", []),
    }
    text = "📂 *Seus dados*\n\n" + "```\n" + json.dumps(summary, ensure_ascii=False, indent=2, default=str)[:3500] + "\n```"
    await safe_edit(update.callback_query, text, reply_markup=kb.privacy_menu(profile.ui_lang))


async def ask_delete(update, context, profile: UserProfileData, params=None) -> None:
    await safe_edit(update.callback_query, t("privacy_confirm", profile.ui_lang), reply_markup=kb.confirm_delete_menu(profile.ui_lang))


async def confirm_delete(update, context, profile: UserProfileData, params=None) -> None:
    services = get_services(context)
    services.storage.users.delete(profile.telegram_id)
    await safe_edit(update.callback_query, t("privacy_deleted", profile.ui_lang), reply_markup=kb.back_to_menu(profile.ui_lang))


async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE, profile: UserProfileData) -> None:
    await reply_text(update, t("privacy_title", profile.ui_lang) + "\n\n" + t("privacy_body", profile.ui_lang), reply_markup=kb.privacy_menu(profile.ui_lang))


async def my_data_command(update: Update, context: ContextTypes.DEFAULT_TYPE, profile: UserProfileData) -> None:
    await view_data(update, context, profile)


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE, profile: UserProfileData) -> None:
    await reply_text(update, t("privacy_confirm", profile.ui_lang), reply_markup=kb.confirm_delete_menu(profile.ui_lang))
