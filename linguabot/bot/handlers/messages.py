"""Tratamento de mensagens de texto e de voz."""

from __future__ import annotations

import logging
import os
import tempfile

from telegram import Update
from telegram.ext import ContextTypes

from ...models import Modality
from ...services import audio as audio_service
from .. import keyboards as kb
from ..context import ensure_profile, get_services, load_session
from ..texts import t
from . import conversation, kids, lessons
from .common import is_rate_limited, reply as reply_text

logger = logging.getLogger(__name__)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.text is None:
        return
    if is_rate_limited(context, update.effective_user.id):
        await update.message.reply_text(t("err_rate", "pt"))
        return

    profile = ensure_profile(update, context)
    session = load_session(context, profile.telegram_id)
    text = update.message.text

    if session.awaiting == "grammar_answer":
        await lessons.grade_text_answer(update, context, profile, session, text)
        return
    if session.mode is Modality.CONVERSACAO:
        await conversation.handle_text(update, context, profile, session, text)
        return
    if session.mode is Modality.INFANTIL:
        await kids.handle_text(update, context, profile, session, text)
        return
    if session.mode is Modality.PRONUNCIA:
        await reply_text(update, t("pron_send_voice", profile.ui_lang), reply_markup=kb.pronunciation_menu(profile.ui_lang))
        return

    from .actions import show_main_menu

    await show_main_menu(update, context, profile)


async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message is None:
        return
    if is_rate_limited(context, update.effective_user.id):
        await message.reply_text(t("err_rate", "pt"))
        return

    profile = ensure_profile(update, context)
    session = load_session(context, profile.telegram_id)

    media = message.voice or message.audio or message.video_note
    if media is None:
        return

    temp_path: str | None = None
    try:
        tg_file = await context.bot.get_file(media.file_id)
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".oga")
        handle.close()
        temp_path = handle.name
        await tg_file.download_to_drive(temp_path)

        if session.mode is Modality.INFANTIL:
            await kids.handle_voice(update, context, profile, session, temp_path)
        elif session.mode is Modality.PRONUNCIA or session.awaiting == "pronunciation":
            await lessons.evaluate_voice(update, context, profile, temp_path)
        elif session.mode is Modality.CONVERSACAO:
            await conversation.handle_voice(update, context, profile, session, temp_path)
        else:
            await reply_text(update, t("not_understood", profile.ui_lang))
    finally:
        audio_service.safe_unlink(temp_path)
