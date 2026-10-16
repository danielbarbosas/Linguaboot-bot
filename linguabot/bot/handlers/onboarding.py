"""Configuração inicial (onboarding) e fluxo de retomada/recomeço."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from ...models import Level, Modality, Profile, UILang, UserProfileData, Voice
from .. import keyboards as kb
from ..context import clear_session, get_services, save_session
from ..texts import t
from .common import safe_edit
from .common import reply as reply_text

logger = logging.getLogger(__name__)


async def begin_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE, profile: UserProfileData) -> None:
    """Inicia o questionário de configuração."""

    await reply_text(update, t("welcome_new", profile.ui_lang, nome=profile.first_name or "amigo"),
                     reply_markup=kb.ui_lang_menu())


# ---------------------------------------------------------------------------
# Etapas
# ---------------------------------------------------------------------------
async def set_ui_lang(update, context, profile, params):
    code = params[0]
    services = get_services(context)
    ui = UILang(code)
    services.storage.users.update(profile.telegram_id, ui_lang=ui.value)
    profile.ui_lang = ui
    await safe_edit(update.callback_query, t("choose_learn_lang", ui), reply_markup=kb.learn_lang_menu(ui))


async def set_learn_lang(update, context, profile, params):
    from ...models import LearnLang

    lang = LearnLang(params[0])
    services = get_services(context)
    services.storage.users.update(profile.telegram_id, learn_lang=lang.value)
    profile.learn_lang = lang
    await safe_edit(update.callback_query, t("choose_level", profile.ui_lang), reply_markup=kb.level_menu(profile.ui_lang))


async def set_level(update, context, profile, params):
    level = Level(params[0])
    services = get_services(context)
    services.storage.users.update(profile.telegram_id, level=level.value)
    profile.level = level
    await safe_edit(update.callback_query, t("choose_voice", profile.ui_lang), reply_markup=kb.voice_menu(profile.ui_lang))


async def set_voice(update, context, profile, params):
    voice = Voice(params[0])
    services = get_services(context)
    services.storage.users.update(profile.telegram_id, voice=voice.value)
    profile.voice = voice
    note = ""
    if not services.speech.supports_gender:
        note = "\n\n" + t("err_voice_gender", profile.ui_lang)
    await safe_edit(
        update.callback_query,
        t("choose_profile", profile.ui_lang) + note,
        reply_markup=kb.profile_menu(profile.ui_lang),
    )


async def set_profile(update, context, profile, params):
    prof = Profile(params[0])
    services = get_services(context)
    services.storage.users.update(profile.telegram_id, profile=prof.value)
    profile.profile = prof
    await safe_edit(update.callback_query, t("choose_modality", profile.ui_lang), reply_markup=kb.modality_menu(profile.ui_lang))


async def set_modality(update, context, profile, params):
    mod = Modality(params[0])
    services = get_services(context)
    services.storage.users.update(profile.telegram_id, modality=mod.value)
    profile.modality = mod
    await safe_edit(update.callback_query, t("choose_goal", profile.ui_lang), reply_markup=kb.goal_menu(profile.ui_lang))


async def set_goal(update, context, profile, params):
    goal = params[0]
    services = get_services(context)
    services.storage.users.update(
        profile.telegram_id, goal=goal, onboarded=1, profile=profile.profile.value
    )
    profile.goal = goal
    profile.onboarded = True
    await safe_edit(update.callback_query, t("onboard_done", profile.ui_lang, nome=profile.first_name or "amigo"))

    from .actions import enter_modality

    await enter_modality(update, context, profile, profile.modality or Modality.CONVERSACAO)


# ---------------------------------------------------------------------------
# Retomada / recomeço
# ---------------------------------------------------------------------------
async def show_resume(update, context, profile) -> None:
    await reply_text(update, t("resume_title", profile.ui_lang), reply_markup=kb.resume_menu(profile.ui_lang))


async def resume_continue(update, context, profile, params):
    from .actions import enter_modality

    services = get_services(context)
    session = services.storage.sessions.get(profile.telegram_id)
    if session and session.mode:
        await enter_modality(update, context, profile, session.mode)
    else:
        await safe_edit(update.callback_query, t("menu_title", profile.ui_lang), reply_markup=kb.main_menu(profile.ui_lang, kids_enabled=services.settings.kids_mode_enabled))


async def resume_restart(update, context, profile, params):
    services = get_services(context)
    run = int(profile.run_key) if profile.run_key.isdigit() else 1
    new_run = str(run + 1)
    services.storage.users.update(profile.telegram_id, run_key=new_run, modality=None)
    profile.run_key = new_run
    profile.modality = None
    clear_session(context, profile.telegram_id)
    await safe_edit(update.callback_query, t("choose_learn_lang", profile.ui_lang), reply_markup=kb.learn_lang_menu(profile.ui_lang))
