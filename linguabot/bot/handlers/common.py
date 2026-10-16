"""Funções auxiliares compartilhadas pelos handlers."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from telegram import Message, Update
from telegram.ext import ContextTypes

from ...models import UILang, UserProfileData, Voice
from ...services import audio as audio_service
from ..context import get_services
from ..texts import t

_RATE_LIMIT: dict[int, deque[float]] = defaultdict(deque)


def is_rate_limited(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Controle simples de antiflood em memória (não é dado de domínio)."""

    limit = get_services(context).settings.rate_limit_per_minute
    if limit <= 0:
        return False
    now = time.monotonic()
    bucket = _RATE_LIMIT[user_id]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= limit:
        return True
    bucket.append(now)
    return False


async def send_voice(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str,
    profile: UserProfileData,
    *,
    caption: str | None = None,
) -> bool:
    """Sintetiza ``text`` e envia como mensagem de voz. Retorna sucesso."""

    services = get_services(context)
    voice = profile.voice or Voice.FEMININO
    lang = profile.learn_lang.value if profile.learn_lang else "en"
    path = await services.speech.synthesize_voice(text, lang, voice)
    if not path:
        return False
    try:
        with open(path, "rb") as handle:
            if path.endswith(".ogg"):
                await context.bot.send_voice(chat_id=chat_id, voice=handle, caption=caption)
            else:
                await context.bot.send_audio(chat_id=chat_id, audio=handle, caption=caption)
        return True
    finally:
        audio_service.safe_unlink(path)


async def send_photo_from_service(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    *,
    profile: UserProfileData,
    term: str,
    category: str,
    emoji: str,
    translation: str,
    caption: str,
    reply_markup=None,
    kids: bool = False,
) -> bool:
    services = get_services(context)
    provider = services.images_kids if kids else services.images_adult
    result = provider.get_image(term=term, category=category, emoji=emoji, translation=translation)
    if result is None:
        await context.bot.send_message(chat_id=chat_id, text=caption, reply_markup=reply_markup)
        return False
    text = caption
    if result.attribution:
        text = f"{caption}\n\n{result.attribution}"
    try:
        with open(result.path, "rb") as handle:
            await context.bot.send_photo(
                chat_id=chat_id, photo=handle, caption=text, reply_markup=reply_markup
            )
    except Exception:
        await context.bot.send_message(chat_id=chat_id, text=caption, reply_markup=reply_markup)
    return True


async def reply(update: Update, text: str, **kwargs) -> Message | None:
    """Responde no contexto certo (mensagem ou callback), com tolerância a erros."""

    query = update.callback_query
    try:
        if query is not None:
            return await query.message.reply_text(text, **kwargs)
        if update.message is not None:
            return await update.message.reply_text(text, **kwargs)
    except Exception:
        return None
    return None


async def safe_edit(query, text: str, **kwargs) -> None:
    """Edita a mensagem do callback; ignora erros de mensagem idêntica."""

    try:
        await query.edit_message_text(text, **kwargs)
    except Exception:
        pass


def ui_of(context: ContextTypes.DEFAULT_TYPE) -> UILang:
    return UILang.PT
