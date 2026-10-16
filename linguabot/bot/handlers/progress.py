"""Exercícios/avaliações e painel de progresso."""

from __future__ import annotations

import random

from telegram import Update
from telegram.ext import ContextTypes

from ...content.languages import get_language
from ...content.vocabulary import get_words
from ...models import LearningSession, Modality, UserProfileData
from .. import keyboards as kb
from ..context import get_services, load_session, save_session
from ..texts import t
from .common import reply as reply_text, safe_edit

QUESTIONS_PER_TEST = 5


def _build_questions(profile: UserProfileData) -> list[dict]:
    if profile.learn_lang is None:
        return []
    words = get_words(profile.learn_lang, level=profile.level)
    if len(words) < 3:
        return []
    sample = random.sample(words, min(QUESTIONS_PER_TEST, len(words)))
    questions = []
    for word in sample:
        distractors = [w.term for w in words if w.term != word.term]
        options = random.sample(distractors, min(2, len(distractors))) + [word.term]
        random.shuffle(options)
        questions.append(
            {
                "prompt": f"Como se diz “{word.translation}”?",
                "answer": word.term,
                "options": options,
            }
        )
    return questions


async def start_assessment(update, context, profile: UserProfileData) -> None:
    if profile.learn_lang is None:
        await reply_text(update, t("choose_learn_lang", profile.ui_lang), reply_markup=kb.learn_lang_menu(profile.ui_lang))
        return
    questions = _build_questions(profile)
    if not questions:
        await reply_text(update, t("grammar_no_lessons", profile.ui_lang), reply_markup=kb.back_to_menu(profile.ui_lang))
        return
    session = load_session(context, profile.telegram_id)
    session.mode = Modality.EXERCICIOS
    session.module = "assessment"
    session.exercise_index = 0
    session.current_item = {"questions": questions, "score": 0}
    session.awaiting = "assessment"
    save_session(context, session)
    await _show_question(update, context, profile, session)


async def _show_question(update, context, profile, session: LearningSession) -> None:
    questions = session.current_item.get("questions", [])
    index = session.exercise_index
    if index >= len(questions):
        await _finish(update, context, profile, session)
        return
    question = questions[index]
    text = t(
        "assess_question",
        profile.ui_lang,
        n=index + 1,
        total=len(questions),
        prompt=question["prompt"],
    )
    markup = kb.assessment_options_menu(profile.ui_lang, index, tuple(question["options"]))
    await reply_text(update, text, reply_markup=markup)


async def answer(update, context, profile, index: int, choice_index: int) -> None:
    query = update.callback_query
    session = load_session(context, profile.telegram_id)
    questions = session.current_item.get("questions", [])
    if index >= len(questions):
        await safe_edit(query, t("err_generic", profile.ui_lang))
        return
    question = questions[index]
    options = question["options"]
    chosen = options[choice_index] if 0 <= choice_index < len(options) else ""
    correct = chosen.strip().lower() == question["answer"].strip().lower()
    if correct:
        session.current_item["score"] = session.current_item.get("score", 0) + 1
        await query.answer("✅")
    else:
        await query.answer(f"❌ {question['answer']}")
    session.exercise_index = index + 1
    save_session(context, session)
    await _show_question(update, context, profile, session)


async def _finish(update, context, profile, session: LearningSession) -> None:
    services = get_services(context)
    questions = session.current_item.get("questions", [])
    score = int(session.current_item.get("score", 0))
    total = len(questions)
    pct = round(score / total * 100) if total else 0
    lang = profile.learn_lang.value if profile.learn_lang else "en"
    services.storage.assessments.add(
        profile.telegram_id, lang, "vocabulario", score, total,
        {"pct": pct}, run_key=profile.run_key,
    )
    services.storage.users.add_xp(profile.telegram_id, score * 3)

    lang_name = get_language(profile.learn_lang).name_pt if profile.learn_lang else "idioma"
    msg = t("assess_result", profile.ui_lang, score=score, total=total, pct=pct)
    if pct < 60:
        msg += "\n" + t("assess_recommend", profile.ui_lang, tema=f"vocabulário de {lang_name}")
    await safe_edit(update.callback_query, msg, reply_markup=kb.progress_menu(profile.ui_lang))
    session.awaiting = None
    save_session(context, session)


async def dashboard(update, context, profile: UserProfileData) -> None:
    services = get_services(context)
    if profile.learn_lang is None:
        await reply_text(update, t("progress_none", profile.ui_lang), reply_markup=kb.back_to_menu(profile.ui_lang))
        return
    lang = profile.learn_lang.value
    summary = services.storage.progress.summary(profile.telegram_id, lang, profile.run_key)
    assessments = services.storage.assessments.list_for(profile.telegram_id, lang, limit=5)
    row = services.storage.users.get(profile.telegram_id)
    xp = int(row["xp"]) if row else 0
    lang_name = get_language(profile.learn_lang).name_pt
    level = profile.level.value if profile.level else "-"

    text = t(
        "progress_title", profile.ui_lang
    ) + "\n\n" + t(
        "progress_line", profile.ui_lang, idioma=lang_name, nivel=level,
        xp=xp, concluidas=summary["completed"], avaliacoes=len(assessments),
    )
    if assessments:
        lines = ["\n📝 Últimas avaliações:"]
        for a in assessments:
            lines.append(f"• {a['created_at'][:10]}: {int(a['score'])}/{a['total']}")
        text += "\n" + "\n".join(lines)
    await reply_text(update, text, reply_markup=kb.progress_menu(profile.ui_lang))
