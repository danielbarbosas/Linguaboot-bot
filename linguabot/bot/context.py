"""Contêiner de serviços e utilitários de estado por usuário."""

from __future__ import annotations

from typing import TYPE_CHECKING

from telegram import Update
from telegram.ext import ContextTypes

from ..container import Services
from ..models import LearningSession, Level, UILang, UserProfileData

if TYPE_CHECKING:  # pragma: no cover
    from ..container import Services as _Services  # noqa: F401


def get_services(context: ContextTypes.DEFAULT_TYPE) -> Services:
    return context.bot_data["services"]


def ensure_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> UserProfileData:
    """Garante que o usuário existe no banco e retorna seu perfil."""

    services = get_services(context)
    user = update.effective_user
    services.storage.users.ensure_user(
        user.id,
        username=user.username,
        first_name=user.first_name,
        default_ui_lang=services.settings.default_ui_lang,
    )
    profile = services.storage.users.get_profile(user.id)
    assert profile is not None  # acabou de ser criado
    return profile


def ui_lang(profile: UserProfileData | None) -> UILang:
    return profile.ui_lang if profile else UILang.PT


def default_level(level: Level | None) -> Level:
    return level or Level.INICIANTE


def load_session(context: ContextTypes.DEFAULT_TYPE, telegram_id: int) -> LearningSession:
    services = get_services(context)
    session = services.storage.sessions.get(telegram_id)
    return session or LearningSession(telegram_id=telegram_id)


def save_session(context: ContextTypes.DEFAULT_TYPE, session: LearningSession) -> None:
    get_services(context).storage.sessions.save(session)


def clear_session(context: ContextTypes.DEFAULT_TYPE, telegram_id: int) -> None:
    get_services(context).storage.sessions.clear(telegram_id)
