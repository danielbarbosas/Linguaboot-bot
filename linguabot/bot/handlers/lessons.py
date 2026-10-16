"""Módulos de gramática, pronúncia e aprendizagem com imagens."""

from __future__ import annotations

import logging
import random

from telegram import Update
from telegram.ext import ContextTypes

from ...content.grammar import GRAMMAR, Exercise, Lesson, get_lesson, get_lessons
from ...content.languages import get_language
from ...content.vocabulary import Word, get_words
from ...models import LearnLang, LearningSession, Level, Modality, UserProfileData
from ...services.tutor import evaluate_pronunciation, pronunciation_feedback
from .. import keyboards as kb
from ..context import get_services, load_session, save_session
from ..texts import t
from .common import reply as reply_text
from .common import safe_edit, send_photo_from_service, send_voice

logger = logging.getLogger(__name__)


# ===========================================================================
# GRAMÁTICA
# ===========================================================================
async def start_grammar(update, context, profile: UserProfileData) -> None:
    if profile.learn_lang is None:
        await reply_text(update, t("choose_learn_lang", profile.ui_lang), reply_markup=kb.learn_lang_menu(profile.ui_lang))
        return
    lessons = get_lessons(profile.learn_lang, profile.level)
    if not lessons:
        await reply_text(update, t("grammar_no_lessons", profile.ui_lang), reply_markup=kb.back_to_menu(profile.ui_lang))
        return
    await reply_text(update, t("grammar_intro", profile.ui_lang), reply_markup=kb.grammar_lessons_menu(profile.ui_lang, lessons))


async def open_lesson(update, context, profile: UserProfileData, lesson_id: str) -> None:
    lesson = get_lesson(profile.learn_lang, lesson_id)
    if lesson is None:
        await safe_edit(update.callback_query, t("grammar_no_lessons", profile.ui_lang))
        return
    session = LearningSession(
        telegram_id=profile.telegram_id,
        mode=Modality.GRAMATICA,
        module="grammar",
        lesson_id=lesson_id,
        exercise_index=0,
    )
    save_session(context, session)

    text = f"📖 *{lesson.title}*\n\n{lesson.explanation}\n\n"
    if lesson.examples:
        text += "📝 *Exemplos:*\n" + "\n".join(f"• {src}  —  {dst}" for src, dst in lesson.examples)
    await safe_edit(update.callback_query, text)
    await _show_exercise(update, context, profile, lesson, 0)


async def _show_exercise(update, context, profile, lesson: Lesson, index: int) -> None:
    if index >= len(lesson.exercises):
        await reply_text(update, t("grammar_finish", profile.ui_lang), reply_markup=kb.back_to_menu(profile.ui_lang))
        _record(context, profile, "grammar", lesson.id, "completed", 1.0)
        return
    exercise = lesson.exercises[index]
    session = load_session(context, profile.telegram_id)
    session.exercise_index = index
    if exercise.kind == "multiple_choice":
        session.awaiting = None
        save_session(context, session)
        await reply_text(
            update,
            f"❓ {exercise.prompt}",
            reply_markup=kb.grammar_options_menu(profile.ui_lang, exercise.id, exercise.options),
        )
    else:
        session.awaiting = "grammar_answer"
        save_session(context, session)
        await reply_text(update, t("grammar_type_answer", profile.ui_lang, prompt=exercise.prompt))


async def answer_mc(update, context, profile, lesson: Lesson, exercise: Exercise, choice_index: int) -> None:
    query = update.callback_query
    chosen = exercise.options[choice_index] if 0 <= choice_index < len(exercise.options) else ""
    correct = chosen.strip().lower() == exercise.answer.strip().lower()
    if correct:
        await query.answer("✅")
        msg = t("grammar_answer_correct", profile.ui_lang, expl=exercise.explanation)
    else:
        await query.answer("❌")
        msg = t("grammar_answer_wrong", profile.ui_lang, resp=exercise.answer, expl=exercise.explanation)
    _record(context, profile, "grammar", exercise.id, "completed" if correct else "review", 1.0 if correct else 0.0)
    await reply_text(update, msg)
    await _show_exercise(update, context, profile, lesson, lesson.exercises.index(exercise) + 1)


async def grade_text_answer(update, context, profile, session: LearningSession, text: str) -> None:
    lesson = get_lesson(profile.learn_lang, session.lesson_id or "")
    if lesson is None or session.exercise_index >= len(lesson.exercises):
        await reply_text(update, t("menu_title", profile.ui_lang), reply_markup=kb.main_menu(profile.ui_lang))
        return
    exercise = lesson.exercises[session.exercise_index]
    correct = text.strip().lower() == exercise.answer.strip().lower()
    if correct:
        msg = t("grammar_answer_correct", profile.ui_lang, expl=exercise.explanation)
    else:
        msg = t("grammar_answer_wrong", profile.ui_lang, resp=exercise.answer, expl=exercise.explanation)
    _record(context, profile, "grammar", exercise.id, "completed" if correct else "review", 1.0 if correct else 0.0)
    session.awaiting = None
    save_session(context, session)
    await reply_text(update, msg)
    await _show_exercise(update, context, profile, lesson, session.exercise_index + 1)


# ===========================================================================
# PRONÚNCIA
# ===========================================================================
def _pick_word(profile: UserProfileData, kids: bool = False) -> Word | None:
    words = get_words(profile.learn_lang, level=profile.level, kids_only=kids)
    return random.choice(words) if words else None


async def _present_word(update, context, profile, word: Word, *, with_image: bool, kids: bool = False) -> None:
    session = load_session(context, profile.telegram_id)
    session.mode = Modality.INFANTIL if kids else Modality.PRONUNCIA
    session.module = "pronunciation" if not kids else "kids"
    session.awaiting = "pronunciation"
    session.current_item = {
        "term": word.term,
        "translation": word.translation,
        "phonetic": word.phonetic,
        "emoji": word.emoji,
        "category": word.category,
    }
    save_session(context, session)

    caption = t("img_caption", profile.ui_lang, emoji=word.emoji, word=word.term, translation=word.translation)
    if with_image:
        await send_photo_from_service(
            context, profile.telegram_id, profile=profile, term=word.term,
            category=word.category, emoji=word.emoji, translation=word.translation,
            caption=caption, reply_markup=kb.pronunciation_menu(profile.ui_lang), kids=kids,
        )
    else:
        await reply_text(update, caption, reply_markup=kb.pronunciation_menu(profile.ui_lang))

    await send_voice(context, profile.telegram_id, word.term, profile)
    await reply_text(update, t("pron_send_voice", profile.ui_lang))


async def start_pronunciation(update, context, profile: UserProfileData) -> None:
    word = _pick_word(profile)
    if word is None:
        await reply_text(update, t("grammar_no_lessons", profile.ui_lang), reply_markup=kb.back_to_menu(profile.ui_lang))
        return
    await _present_word(update, context, profile, word, with_image=True)


async def pronunciation_next(update, context, profile, params=None) -> None:
    word = _pick_word(profile)
    if word is None:
        return
    await _present_word(update, context, profile, word, with_image=True)


async def pronunciation_repeat(update, context, profile, params=None) -> None:
    session = load_session(context, profile.telegram_id)
    term = session.current_item.get("term")
    if term:
        await send_voice(context, profile.telegram_id, term, profile)


async def evaluate_voice(update, context, profile, audio_path: str) -> None:
    services = get_services(context)
    session = load_session(context, profile.telegram_id)
    item = session.current_item or {}
    term = item.get("term", "")
    phonetic = item.get("phonetic")
    lang = profile.learn_lang.value if profile.learn_lang else "en"

    if not services.stt.available:
        await reply_text(update, t("err_no_stt", profile.ui_lang), reply_markup=kb.pronunciation_menu(profile.ui_lang))
        return

    import asyncio

    recognized = await asyncio.to_thread(services.stt.transcribe, audio_path, lang)
    result = evaluate_pronunciation(term, recognized)
    feedback = pronunciation_feedback(result, phonetic)
    _record(context, profile, "pronunciation", term, "completed" if result.status == "ok" else "review", result.similarity)
    await reply_text(update, feedback, reply_markup=kb.pronunciation_menu(profile.ui_lang))
    if result.status in {"ok", "close"}:
        services.storage.users.add_xp(profile.telegram_id, 5)
    await send_voice(context, profile.telegram_id, term, profile)


# ===========================================================================
# IMAGENS
# ===========================================================================
async def start_images(update, context, profile: UserProfileData) -> None:
    word = _pick_word(profile)
    if word is None:
        await reply_text(update, t("grammar_no_lessons", profile.ui_lang), reply_markup=kb.back_to_menu(profile.ui_lang))
        return
    session = load_session(context, profile.telegram_id)
    session.mode = Modality.IMAGENS
    session.module = "images"
    session.awaiting = None
    session.current_item = {
        "term": word.term, "translation": word.translation, "phonetic": word.phonetic,
        "emoji": word.emoji, "category": word.category,
    }
    save_session(context, session)
    caption = t("img_caption", profile.ui_lang, emoji=word.emoji, word=word.term, translation=word.translation)
    await send_photo_from_service(
        context, profile.telegram_id, profile=profile, term=word.term, category=word.category,
        emoji=word.emoji, translation=word.translation, caption=caption,
        reply_markup=kb.image_menu(profile.ui_lang),
    )
    await send_voice(context, profile.telegram_id, word.term, profile)


async def image_next(update, context, profile, params=None) -> None:
    await start_images(update, context, profile)


async def image_repeat(update, context, profile, params=None) -> None:
    session = load_session(context, profile.telegram_id)
    term = session.current_item.get("term")
    if term:
        await send_voice(context, profile.telegram_id, term, profile)


async def image_pronounce(update, context, profile, params=None) -> None:
    session = load_session(context, profile.telegram_id)
    item = session.current_item or {}
    if not item.get("term"):
        await start_pronunciation(update, context, profile)
        return
    session.awaiting = "pronunciation"
    session.module = "pronunciation"
    save_session(context, session)
    await reply_text(update, t("pron_send_voice", profile.ui_lang), reply_markup=kb.pronunciation_menu(profile.ui_lang))


# ===========================================================================
# utilitário
# ===========================================================================
def _record(context, profile, module: str, item_id: str, status: str, score: float) -> None:
    services = get_services(context)
    lang = profile.learn_lang.value if profile.learn_lang else "en"
    services.storage.progress.record(
        profile.telegram_id, lang, module, item_id, status=status, score=score, run_key=profile.run_key
    )


def find_exercise(lang: LearnLang, exercise_id: str) -> tuple[Lesson, Exercise] | None:
    for lesson in GRAMMAR.get(lang, []):
        for exercise in lesson.exercises:
            if exercise.id == exercise_id:
                return lesson, exercise
    return None
