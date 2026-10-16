"""Despachante de modalidades e menu principal."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from ...models import Modality, UserProfileData
from .. import keyboards as kb
from ..context import get_services
from ..texts import t
from .common import reply as reply_text


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, profile: UserProfileData) -> None:
    services = get_services(context)
    await reply_text(
        update,
        t("menu_title", profile.ui_lang),
        reply_markup=kb.main_menu(profile.ui_lang, kids_enabled=services.settings.kids_mode_enabled),
    )


async def enter_modality(
    update: Update, context: ContextTypes.DEFAULT_TYPE, profile: UserProfileData, modality: Modality
) -> None:
    """Entra na modalidade escolhida. Cada módulo cuida do próprio fluxo."""

    from . import conversation, kids, lessons, progress

    if modality is Modality.CONVERSACAO:
        await conversation.start_conversation(update, context, profile)
    elif modality is Modality.GRAMATICA:
        await lessons.start_grammar(update, context, profile)
    elif modality is Modality.PRONUNCIA:
        await lessons.start_pronunciation(update, context, profile)
    elif modality is Modality.IMAGENS:
        await lessons.start_images(update, context, profile)
    elif modality is Modality.INFANTIL:
        await kids.start_kids(update, context, profile)
    elif modality is Modality.EXERCICIOS:
        await progress.start_assessment(update, context, profile)
    else:
        await show_main_menu(update, context, profile)
