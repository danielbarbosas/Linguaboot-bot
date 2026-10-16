"""Modo infantil: atividades curtas, seguras e com reforço positivo.

Salvaguardas: nenhum dado pessoal é solicitado; imagens vêm de assets
curados ou são geradas localmente (nunca busca externa aleatória); áudios do
usuário não são armazenados; é exigido consentimento de um responsável.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from ...models import LearningSession, Modality, UserProfileData
from ...services.tutor import evaluate_pronunciation
from .. import keyboards as kb
from ..context import get_services, load_session, save_session
from ..texts import t
from .common import reply as reply_text, send_photo_from_service, send_voice
from .lessons import _pick_word

logger = logging.getLogger(__name__)


async def start_kids(update, context, profile: UserProfileData) -> None:
    services = get_services(context)
    if not services.settings.kids_mode_enabled:
        await reply_text(update, t("not_understood", profile.ui_lang), reply_markup=kb.main_menu(profile.ui_lang, kids_enabled=False))
        return
    if not profile.kids_consent:
        await reply_text(update, t("kids_intro", profile.ui_lang), reply_markup=kb.kids_consent_menu(profile.ui_lang))
        return
    await _next_activity(update, context, profile)


async def grant_consent(update, context, profile: UserProfileData, params=None) -> None:
    services = get_services(context)
    services.storage.users.set_consent(profile.telegram_id, "kids", True)
    services.storage.users.update(profile.telegram_id, kids_consent=1, profile="infantil")
    profile.kids_consent = True
    await _next_activity(update, context, profile)


async def _next_activity(update, context, profile: UserProfileData) -> None:
    word = _pick_word(profile, kids=True)
    if word is None:
        await reply_text(update, t("grammar_no_lessons", profile.ui_lang), reply_markup=kb.back_to_menu(profile.ui_lang))
        return
    session = load_session(context, profile.telegram_id)
    session.mode = Modality.INFANTIL
    session.module = "kids"
    session.awaiting = "pronunciation"
    session.current_item = {
        "term": word.term, "translation": word.translation,
        "emoji": word.emoji, "category": word.category,
    }
    save_session(context, session)

    caption = t("kids_caption", profile.ui_lang, emoji=word.emoji, word=word.term.upper())
    await send_photo_from_service(
        context, profile.telegram_id, profile=profile, term=word.term, category=word.category,
        emoji=word.emoji, translation=word.translation, caption=caption,
        reply_markup=kb.kids_activity_menu(profile.ui_lang), kids=True,
    )
    await send_voice(context, profile.telegram_id, word.term, profile)


async def next_activity(update, context, profile, params=None) -> None:
    await _next_activity(update, context, profile)


async def repeat(update, context, profile, params=None) -> None:
    session = load_session(context, profile.telegram_id)
    term = session.current_item.get("term")
    if term:
        await send_voice(context, profile.telegram_id, term, profile)


async def handle_voice(update, context, profile, session: LearningSession, audio_path: str) -> None:
    import asyncio

    services = get_services(context)
    target = session.current_item.get("term", "")
    if not services.stt.available:
        await reply_text(update, t("kids_retry", profile.ui_lang, word=target), reply_markup=kb.kids_activity_menu(profile.ui_lang))
        return
    lang = profile.learn_lang.value if profile.learn_lang else "en"
    recognized = await asyncio.to_thread(services.stt.transcribe, audio_path, lang)

    result = evaluate_pronunciation(target, recognized)
    # Tolerância para fala infantil: aceitamos "ok" e "close".
    if result.status in {"ok", "close"}:
        await reply_text(update, t("kids_correct", profile.ui_lang, word=target))
        services.storage.users.add_xp(profile.telegram_id, 5)
    elif result.status == "unknown":
        await reply_text(update, t("kids_retry", profile.ui_lang, word=target))
    else:
        await reply_text(update, t("kids_retry", profile.ui_lang, word=target))
    await send_voice(context, profile.telegram_id, target, profile)


async def handle_text(update, context, profile, session: LearningSession, text: str) -> None:
    target = session.current_item.get("term", "")
    if target and target.lower() in text.lower():
        await reply_text(update, t("kids_correct", profile.ui_lang, word=target))
        get_services(context).storage.users.add_xp(profile.telegram_id, 3)
    else:
        await reply_text(update, t("kids_retry", profile.ui_lang, word=target))
    await send_voice(context, profile.telegram_id, target, profile)
