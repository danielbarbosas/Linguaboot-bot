"""Comandos do Telegram (/start, /menu, /ajuda, etc.)."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from .. import keyboards as kb
from ..context import ensure_profile, get_services, load_session
from ..texts import t
from . import actions, onboarding, progress, settings
from .common import reply as reply_text

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = ensure_profile(update, context)
    if not profile.onboarded:
        await onboarding.begin_onboarding(update, context, profile)
        return

    session = load_session(context, profile.telegram_id)
    if session.mode is not None or session.awaiting:
        await reply_text(update, t("welcome_back", profile.ui_lang, nome=profile.first_name or "amigo"))
        await onboarding.show_resume(update, context, profile)
        return

    await reply_text(update, t("welcome_back", profile.ui_lang, nome=profile.first_name or "amigo"))
    await actions.show_main_menu(update, context, profile)


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = ensure_profile(update, context)
    await actions.show_main_menu(update, context, profile)


async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = ensure_profile(update, context)
    await reply_text(update, t("help", profile.ui_lang))


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = ensure_profile(update, context)
    await actions.show_main_menu(update, context, profile)


async def progresso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = ensure_profile(update, context)
    await progress.dashboard(update, context, profile)


async def config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = ensure_profile(update, context)
    await reply_text(update, t("settings_title", profile.ui_lang), reply_markup=kb.settings_menu(profile.ui_lang))


async def privacidade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = ensure_profile(update, context)
    await settings.privacy_command(update, context, profile)


async def meusdados(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = ensure_profile(update, context)
    await settings.my_data_command(update, context, profile)


async def apagar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    profile = ensure_profile(update, context)
    await settings.delete_command(update, context, profile)
