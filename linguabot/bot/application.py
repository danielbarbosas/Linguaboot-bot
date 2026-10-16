"""Montagem da aplicação do Telegram (handlers, erros e polling)."""

from __future__ import annotations

import logging

from telegram import BotCommand, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ..config import Settings
from ..container import Services, build_services
from .handlers import commands, messages, router

logger = logging.getLogger(__name__)

COMMANDS = [
    BotCommand("start", "Iniciar ou retomar"),
    BotCommand("menu", "Menu principal"),
    BotCommand("ajuda", "Ajuda"),
    BotCommand("progresso", "Meu progresso"),
    BotCommand("config", "Configurações"),
    BotCommand("privacidade", "Privacidade"),
    BotCommand("meusdados", "Ver meus dados"),
    BotCommand("apagar", "Apagar meus dados"),
]


async def _on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Erro não tratado", exc_info=context.error)
    if isinstance(update, Update):
        try:
            if update.callback_query:
                await update.callback_query.answer("😥 Ocorreu um erro.")
            elif update.message:
                await update.message.reply_text("😥 Ocorreu um erro. Tente novamente.")
        except Exception:
            pass


async def _post_init(application: Application) -> None:
    try:
        await application.bot.set_my_commands(COMMANDS)
    except Exception as exc:  # pragma: no cover - depende de rede
        logger.warning("Não foi possível registrar os comandos: %s", exc)


def register_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", commands.start))
    application.add_handler(CommandHandler("menu", commands.menu))
    application.add_handler(CommandHandler(["ajuda", "help"], commands.ajuda))
    application.add_handler(CommandHandler("cancel", commands.cancel))
    application.add_handler(CommandHandler("progresso", commands.progresso))
    application.add_handler(CommandHandler("config", commands.config))
    application.add_handler(CommandHandler("privacidade", commands.privacidade))
    application.add_handler(CommandHandler("meusdados", commands.meusdados))
    application.add_handler(CommandHandler("apagar", commands.apagar))

    application.add_handler(CallbackQueryHandler(router.route))
    application.add_handler(
        MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO_NOTE, messages.on_voice)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, messages.on_text)
    )
    application.add_error_handler(_on_error)


def build_application(settings: Settings, services: Services | None = None) -> Application:
    if not settings.bot_token:
        raise RuntimeError(
            "BOT_TOKEN não configurado. Defina a variável de ambiente BOT_TOKEN."
        )
    services = services or build_services(settings)
    application = (
        ApplicationBuilder()
        .token(settings.bot_token)
        .post_init(_post_init)
        .build()
    )
    application.bot_data["services"] = services
    register_handlers(application)
    return application


def run(settings: Settings) -> None:
    """Executa o bot com long polling."""

    application = build_application(settings)
    logger.info("LinguaBot iniciado (long polling).")
    application.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
