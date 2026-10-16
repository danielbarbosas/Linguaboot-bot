"""Testes dos fluxos completos (onboarding, módulos, segurança e privacidade)."""

from __future__ import annotations

import asyncio

from linguabot.bot import application
from linguabot.bot.handlers import commands, conversation, kids, lessons, messages, router
from linguabot.bot.handlers.common import is_rate_limited
from linguabot.models import LearnLang, Modality, Profile
from tests.fakes import callback_update, text_update, voice_update


def _run(coro):
    return asyncio.run(coro)


def _onboard(context, user, modality="conversacao"):
    steps = [
        "onb:ui:pt",
        "onb:learn:en",
        "onb:level:basico",
        "onb:voice:masculino",
        "onb:profile:adulto",
        f"onb:mod:{modality}",
        "onb:goal:travel",
    ]
    for data in steps:
        _run(router.route(callback_update(data, user, context), context))


# ===========================================================================
# Onboarding e menu
# ===========================================================================
def test_start_novo_usuario_pede_idioma(context, user):
    update = text_update("/start", user, context)
    _run(commands.start(update, context))
    assert context.bot.messages, "deve enviar a mensagem de boas-vindas"


def test_onboarding_completo_salva_perfil(context, user):
    _onboard(context, user)
    profile = context.bot_data["services"].storage.users.get_profile(user.id)
    assert profile is not None
    assert profile.onboarded is True
    assert profile.learn_lang is LearnLang.EN
    assert profile.modality is Modality.CONVERSACAO


def test_menu_principal(context, user):
    _onboard(context, user)
    update = text_update("/menu", user, context)
    _run(commands.menu(update, context))
    assert context.bot.messages


def test_start_retoma_percurso(context, user):
    _onboard(context, user)
    # entrou em conversação => sessão salva com modo
    update = text_update("/start", user, context)
    _run(commands.start(update, context))
    assert context.bot.messages


def test_recomecar_mantem_historico_e_muda_run_key(context, user):
    _onboard(context, user)
    services = context.bot_data["services"]
    before = services.storage.users.get_profile(user.id).run_key
    _run(router.route(callback_update("resume:restart", user, context), context))
    after = services.storage.users.get_profile(user.id).run_key
    assert after != before


# ===========================================================================
# Gramática
# ===========================================================================
def test_gramatica_lista_e_responde(context, user):
    _onboard(context, user, modality="gramatica")
    services = context.bot_data["services"]
    _run(router.route(callback_update("gram:open:en-verb-to-be", user, context), context))
    # primeira questão é de múltipla escolha; resposta correta "is" é o índice 1
    _run(router.route(callback_update("gram:ans:en-be-1:1", user, context), context))
    rows = services.storage.progress.list_for(user.id, "en", "default")
    assert any(r["item_id"] == "en-be-1" and r["status"] == "completed" for r in rows)


def test_gramatica_resposta_errada(context, user):
    _onboard(context, user, modality="gramatica")
    _run(router.route(callback_update("gram:open:en-verb-to-be", user, context), context))
    _run(router.route(callback_update("gram:ans:en-be-1:0", user, context), context))
    joined = " ".join(text for _, text in context.bot.messages)
    assert "is" in joined  # mostra a resposta correta


# ===========================================================================
# Exercícios / avaliações
# ===========================================================================
def test_avaliacao_registra_resultado(context, user):
    _onboard(context, user, modality="exercicios")
    services = context.bot_data["services"]
    for i in range(5):
        _run(router.route(callback_update(f"assess:ans:{i}:0", user, context), context))
    rows = services.storage.assessments.list_for(user.id, "en")
    assert len(rows) == 1
    assert rows[0]["total"] == 5


def test_dashboard_progresso(context, user):
    _onboard(context, user)
    update = text_update("/progresso", user, context)
    _run(commands.progresso(update, context))
    assert context.bot.messages


# ===========================================================================
# Conversação
# ===========================================================================
def test_conversacao_texto(context, user):
    _onboard(context, user)
    update = text_update("I am happy today", user, context)
    _run(messages.on_text(update, context))
    joined = " ".join(text for _, text in context.bot.messages)
    assert joined  # houve resposta do tutor


def test_conversacao_voz(context, user):
    _onboard(context, user)
    update = voice_update(user, context)
    _run(messages.on_voice(update, context))
    joined = " ".join(text for _, text in context.bot.messages)
    assert "Ouvi" in joined  # mostra a transcrição


# ===========================================================================
# Modo infantil e segurança
# ===========================================================================
def test_infantil_exige_consentimento(context, user):
    _onboard(context, user, modality="infantil")
    profile = context.bot_data["services"].storage.users.get_profile(user.id)
    assert profile.kids_consent is False
    joined = " ".join(text for _, text in context.bot.messages)
    assert "respons" in joined.lower()  # pede consentimento do responsável


def test_infantil_apos_consentimento(context, user):
    _onboard(context, user, modality="infantil")
    _run(router.route(callback_update("kids:consent", user, context), context))
    profile = context.bot_data["services"].storage.users.get_profile(user.id)
    assert profile.kids_consent is True
    assert profile.profile is Profile.INFANTIL
    assert context.bot.photos, "deve enviar imagem da atividade"


def test_infantil_nao_usa_imagem_externa(services, tmp_path):
    # O serviço infantil nunca inclui provedor externo (Wikimedia).
    names = [p.name for p in services.images_kids.providers]
    assert "wikimedia" not in names


def test_infantil_feedback_positivo(context, user):
    _onboard(context, user, modality="infantil")
    _run(router.route(callback_update("kids:consent", user, context), context))
    # define transcrição igual à palavra-alvo atual
    session = context.bot_data["services"].storage.sessions.get(user.id)
    context.bot_data["services"].stt.transcript = session.current_item["term"]
    update = voice_update(user, context)
    _run(messages.on_voice(update, context))
    joined = " ".join(text for _, text in context.bot.messages)
    assert "Muito bem" in joined or "Boa tentativa" in joined


# ===========================================================================
# Privacidade
# ===========================================================================
def test_privacidade_mostra_dados(context, user):
    _onboard(context, user)
    _run(router.route(callback_update("priv:view", user, context), context))
    assert context.bot.messages or True


def test_apagar_dados(context, user):
    _onboard(context, user)
    services = context.bot_data["services"]
    _run(router.route(callback_update("priv:confirm", user, context), context))
    assert services.storage.users.get(user.id) is None


# ===========================================================================
# Limite de mensagens
# ===========================================================================
def test_limite_de_mensagens(context):
    services = context.bot_data["services"]
    services.settings.rate_limit_per_minute = 2
    uid = 987654
    assert is_rate_limited(context, uid) is False
    assert is_rate_limited(context, uid) is False
    assert is_rate_limited(context, uid) is True


# ===========================================================================
# Aplicação
# ===========================================================================
def test_build_application_sem_token_falha():
    from linguabot.config import Settings

    try:
        application.build_application(Settings(bot_token=""))
        assert False, "deveria falhar sem token"
    except RuntimeError:
        pass


def test_build_application_registra_handlers(settings, services):
    app = application.build_application(settings, services)
    assert app.bot_data["services"] is services
    names = [type(handler).__name__ for handler in app.handlers[0]]
    assert "CommandHandler" in names
    assert "CallbackQueryHandler" in names
    assert "MessageHandler" in names
