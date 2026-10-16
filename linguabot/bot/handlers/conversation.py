"""Conversação livre."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from ...models import CorrectionMode, LearningSession, Modality, UserProfileData
from .. import keyboards as kb
from ..context import get_services, load_session, save_session
from ..texts import t
from .common import reply as reply_text, send_voice


async def start_conversation(update, context, profile: UserProfileData) -> None:
    session = load_session(context, profile.telegram_id)
    session.mode = Modality.CONVERSACAO
    session.module = "conversation"
    session.awaiting = None
    save_session(context, session)
    await reply_text(update, t("conv_intro", profile.ui_lang), reply_markup=kb.back_to_menu(profile.ui_lang))
    await reply_text(update, t("conv_correction_note", profile.ui_lang))


async def handle_text(update, context, profile: UserProfileData, session: LearningSession, text: str) -> None:
    services = get_services(context)
    tutor = services.tutor_for(profile)
    reply = tutor.conversation(
        student_text=text,
        level=profile.level,
        correction_mode=profile.correction_mode,
        ui_lang=profile.ui_lang.value,
    )
    await update.message.reply_text(reply)
    services.storage.users.add_xp(profile.telegram_id, 2)


async def handle_voice(
    update, context, profile: UserProfileData, session: LearningSession, audio_path: str
) -> None:
    import asyncio

    services = get_services(context)
    if not services.stt.available:
        await reply_text(update, t("err_no_stt", profile.ui_lang), reply_markup=kb.back_to_menu(profile.ui_lang))
        return
    lang = profile.learn_lang.value if profile.learn_lang else "en"
    transcription = await asyncio.to_thread(services.stt.transcribe, audio_path, lang)
    if not transcription:
        await reply_text(update, t("err_no_stt", profile.ui_lang))
        return

    tutor = services.tutor_for(profile)
    reply = tutor.conversation(
        student_text=transcription,
        level=profile.level,
        correction_mode=profile.correction_mode,
        ui_lang=profile.ui_lang.value,
    )
    await reply_text(update, f"🎤 Ouvi: “{transcription}”\n\n{reply}")
    await reply_text(update, t("conv_correction_note", profile.ui_lang))
    await send_voice(context, profile.telegram_id, transcription, profile)
