"""Roteador central de callbacks (botões).

Formato do ``callback_data``: ``area:acao[:parametro...]``.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from ...models import Modality, UserProfileData
from ..context import ensure_profile
from ..texts import t
from . import actions, kids, lessons, onboarding, progress, settings
from .common import reply as reply_text

logger = logging.getLogger(__name__)

# Mapeia os botões do menu para as modalidades internas.
_GO_MAP = {
    "conversation": Modality.CONVERSACAO,
    "pronunciation": Modality.PRONUNCIA,
    "grammar": Modality.GRAMATICA,
    "images": Modality.IMAGENS,
    "kids": Modality.INFANTIL,
    "assess": Modality.EXERCICIOS,
}


async def route(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    try:
        await query.answer()
    except Exception:
        pass

    profile = ensure_profile(update, context)
    data = query.data or ""
    parts = data.split(":")
    area = parts[0]
    action = parts[1] if len(parts) > 1 else ""
    params = parts[2:]

    try:
        if area == "menu":
            await _menu(update, context, profile, action)
        elif area == "onb":
            await _onboarding(update, context, profile, action, params)
        elif area == "set":
            await _settings(update, context, profile, action, params)
        elif area == "resume":
            await _resume(update, context, profile, action)
        elif area == "go":
            modality = _GO_MAP.get(action)
            if modality is None:
                await reply_text(update, t("not_understood", profile.ui_lang))
            else:
                await actions.enter_modality(update, context, profile, modality)
        elif area == "gram":
            await _grammar(update, context, profile, action, params)
        elif area == "pron":
            if action == "repeat":
                await lessons.pronunciation_repeat(update, context, profile)
            elif action == "next":
                await lessons.pronunciation_next(update, context, profile)
        elif area == "img":
            if action == "repeat":
                await lessons.image_repeat(update, context, profile)
            elif action == "pronounce":
                await lessons.image_pronounce(update, context, profile)
            elif action == "next":
                await lessons.image_next(update, context, profile)
        elif area == "kids":
            if action == "consent":
                await kids.grant_consent(update, context, profile)
        elif area == "kid":
            if action == "next":
                await kids.next_activity(update, context, profile)
            elif action == "repeat":
                await kids.repeat(update, context, profile)
        elif area == "assess":
            await _assess(update, context, profile, action, params)
        elif area == "priv":
            await _privacy(update, context, profile, action)
        else:
            await reply_text(update, t("not_understood", profile.ui_lang))
    except Exception:  # pragma: no cover - proteção geral
        logger.exception("Erro ao tratar callback %s", data)
        await reply_text(update, t("err_generic", profile.ui_lang))


# ---------------------------------------------------------------------------
async def _menu(update, context, profile: UserProfileData, action: str) -> None:
    if action == "main":
        await actions.show_main_menu(update, context, profile)
    elif action == "help":
        await reply_text(update, t("help", profile.ui_lang))
    elif action == "settings":
        await settings.show_settings(update, context, profile)
    elif action == "progress":
        await progress.dashboard(update, context, profile)
    elif action == "privacy":
        await settings.show_privacy(update, context, profile)


async def _onboarding(update, context, profile, action, params) -> None:
    mapping = {
        "ui": onboarding.set_ui_lang,
        "learn": onboarding.set_learn_lang,
        "level": onboarding.set_level,
        "voice": onboarding.set_voice,
        "profile": onboarding.set_profile,
        "mod": onboarding.set_modality,
        "goal": onboarding.set_goal,
    }
    handler = mapping.get(action)
    if handler:
        await handler(update, context, profile, params)


async def _settings(update, context, profile, action, params) -> None:
    simple = {
        "ui": settings.choose_ui,
        "learn": settings.choose_learn,
        "level": settings.choose_level,
        "voice": settings.choose_voice,
        "mod": settings.choose_mod,
        "corr": settings.choose_corr,
    }
    apply_map = {
        "ui": settings.apply_ui,
        "learn": settings.apply_learn,
        "level": settings.apply_level,
        "voice": settings.apply_voice,
        "mod": settings.apply_mod,
        "corr": settings.apply_corr,
    }
    if params:
        handler = apply_map.get(action)
    else:
        handler = simple.get(action)
    if handler:
        await handler(update, context, profile, params)


async def _resume(update, context, profile, action) -> None:
    if action == "continue":
        await onboarding.resume_continue(update, context, profile, [])
    elif action == "restart":
        await onboarding.resume_restart(update, context, profile, [])


async def _grammar(update, context, profile, action, params) -> None:
    if action == "open":
        await lessons.open_lesson(update, context, profile, params[0])
    elif action == "ans":
        exercise_id, choice = params[0], int(params[1])
        found = lessons.find_exercise(profile.learn_lang, exercise_id)
        if found:
            lesson, exercise = found
            await lessons.answer_mc(update, context, profile, lesson, exercise, choice)


async def _assess(update, context, profile, action, params) -> None:
    if action == "start":
        await progress.start_assessment(update, context, profile)
    elif action == "ans":
        index, choice = int(params[0]), int(params[1])
        await progress.answer(update, context, profile, index, choice)


async def _privacy(update, context, profile, action) -> None:
    if action == "view":
        await settings.view_data(update, context, profile)
    elif action == "delete":
        await settings.ask_delete(update, context, profile)
    elif action == "confirm":
        await settings.confirm_delete(update, context, profile)
