"""Textos da interface em português, inglês e espanhol.

Use ``t("chave", "pt")`` para obter o texto e ``t("chave", "en", nome="Ana")``
para interpolar. Chaves ausentes caem para o português.
"""

from __future__ import annotations

from typing import Any

from ..models import UILang

MESSAGES: dict[str, dict[str, str]] = {
    "pt": {
        # boas-vindas / retomada
        "welcome_new": (
            "Olá, {nome}! Eu sou o *LinguaBot* 🤖✨\n"
            "Vou te ajudar a aprender idiomas direto aqui no Telegram.\n\n"
            "Vamos fazer uma configuração rápida."
        ),
        "welcome_back": "Olá de novo, {nome}! 👋 Que bom te ver.",
        "resume_title": "Você tem um aprendizado em andamento. O que deseja fazer?",
        "resume_continue": "▶️ Continuar de onde parei",
        "resume_restart": "🔄 Recomeçar aprendizado",
        "resume_settings": "⚙️ Alterar minhas configurações",
        "resume_progress": "📊 Ver meu progresso",
        "resume_none": "Não encontrei um percurso salvo. Vamos começar!",
        # ajuda
        "help": (
            "📖 *Como usar o LinguaBot*\n\n"
            "• /start – início e retomada\n"
            "• /menu – menu principal\n"
            "• /progresso – seu progresso\n"
            "• /config – alterar idioma, nível e voz\n"
            "• /privacidade – como tratamos seus dados\n"
            "• /apagar – apagar seus dados\n\n"
            "Você pode escrever *texto* ou enviar *mensagens de voz* 🎤."
        ),
        # onboarding
        "choose_ui_lang": "🌍 Primeiro, escolha o idioma da *interface*:",
        "choose_learn_lang": "🌍 Qual idioma você quer *aprender*?",
        "choose_level": "📊 Qual é o seu nível?",
        "choose_voice": "🎙️ Escolha a voz de referência (áudio):",
        "choose_profile": "👤 Escolha o perfil:",
        "choose_modality": "📚 Qual modalidade você quer começar?",
        "choose_goal": "🎯 Qual seu objetivo principal?",
        "onboard_done": "✅ Tudo pronto, {nome}! Seu percurso foi salvo.",
        # níveis
        "level_iniciante": "🌱 Iniciante",
        "level_basico": "🌿 Básico",
        "level_intermediario": "🌳 Intermediário",
        "level_avancado": "🏔️ Avançado",
        # vozes / perfis
        "voice_feminino": "👩 Feminina",
        "voice_masculino": "👨 Masculina",
        "profile_adulto": "🧑 Adulto",
        "profile_infantil": "🧒 Infantil",
        # modalidades
        "mod_conversacao": "💬 Conversação livre",
        "mod_gramatica": "📖 Gramática",
        "mod_pronuncia": "🗣️ Pronúncia",
        "mod_imagens": "🖼️ Imagens",
        "mod_exercicios": "📝 Exercícios",
        "mod_infantil": "🧸 Modo infantil",
        # menu
        "menu_title": "🏠 *Menu principal* – escolha uma opção:",
        "menu_main": "🏠 Menu principal",
        "menu_settings": "⚙️ Configurações",
        "menu_progress": "📊 Meu progresso",
        "menu_help": "📖 Ajuda",
        "settings_title": "⚙️ *Configurações* – o que deseja alterar?",
        "settings_ui_lang": "🌐 Idioma da interface",
        "settings_learn_lang": "🌍 Idioma estudado",
        "settings_level": "📊 Nível",
        "settings_voice": "🎙️ Voz",
        "settings_modality": "📚 Modalidade",
        "settings_correction": "✍️ Modo de correção",
        "settings_privacy": "🔒 Privacidade",
        "corr_imediata": "⚡ Imediata (resumida)",
        "corr_detalhada": "🔍 Detalhada",
        "saved": "✅ Preferência atualizada!",
        # conversação
        "conv_intro": (
            "💬 *Conversação livre*\n"
            "Escreva ou mande um áudio no idioma estudado. "
            "Eu respondo e corrijo o que for mais importante."
        ),
        "conv_correction_note": "ℹ️ Em áudios, avalio a *transcrição* (texto); não meço sua pronúncia.",
        # gramática
        "grammar_intro": "📖 *Gramática* – escolha uma lição:",
        "grammar_no_lessons": "Ainda não há lições de gramática para este idioma/nível.",
        "grammar_answer_correct": "✅ Correto! {expl}",
        "grammar_answer_wrong": "❌ Não foi dessa vez. Resposta: *{resp}*\n{expl}",
        "grammar_your_answer": "Sua resposta para: {prompt}",
        "grammar_type_answer": "✍️ Digite sua resposta para: {prompt}",
        "grammar_next": "➡️ Próximo",
        "grammar_finish": "🎉 Você concluiu esta lição!",
        # pronúncia
        "pron_intro": "🗣️ *Pronúncia* – ouça e repita.",
        "pron_send_voice": "🎤 Agora mande um *áudio* dizendo a palavra.",
        "pron_repeat": "🔁 Ouvir novamente",
        "pron_next": "➡️ Próxima",
        # imagens
        "img_intro": "🖼️ *Aprender com imagens*",
        "img_caption": "{emoji} *{word}*\n🇧🇷 {translation}",
        "img_repeat": "🔊 Ouvir",
        "img_pronounce": "🎤 Pronunciar",
        "img_next": "➡️ Próxima",
        # infantil
        "kids_intro": (
            "🧒 *Modo infantil*\n"
            "Atividades curtas, com elogios e sem pedir dados pessoais.\n\n"
            "Um responsável deve confirmar abaixo."
        ),
        "kids_consent_btn": "✅ Sou responsável e autorizo",
        "kids_start_btn": "🧸 Começar",
        "kids_need_consent": "Para usar o modo infantil precisamos do consentimento de um responsável.",
        "kids_caption": "{emoji} O que é isso? Diga: *{word}* 🥰",
        "kids_correct": "🎉 Muito bem! Você disse {word}! 👏",
        "kids_retry": "⭐ Boa tentativa! Vamos ouvir de novo: {word}. Você consegue! 💪",
        # exercícios / avaliações
        "assess_intro": "📝 *Exercícios e avaliações* – vamos começar!",
        "assess_question": "Pergunta {n}/{total}\n\n{prompt}",
        "assess_result": "📊 Você acertou {score} de {total} ({pct}%).",
        "assess_recommend": "Sugestão: revise {tema}.",
        "assess_start": "▶️ Começar avaliação",
        # progresso
        "progress_title": "📊 *Seu progresso*",
        "progress_line": "• {idioma}\n   Nível: {nivel}\n   XP: {xp}\n   Lições concluídas: {concluidas}\n   Avaliações: {avaliacoes}",
        "progress_none": "Você ainda não tem progresso registrado. Comece uma atividade no /menu!",
        # privacidade
        "privacy_title": "🔒 *Privacidade*",
        "privacy_body": (
            "• Guardamos apenas o necessário: idioma, nível, preferências, progresso e histórico de avaliações.\n"
            "• Áudios de voz são processados e *descartados* após o uso; não são armazenados.\n"
            "• Não pedimos dados pessoais de crianças.\n"
            "• Você pode ver (/meusdados) e apagar (/apagar) seus dados a qualquer momento."
        ),
        "privacy_deleted": "🗑️ Todos os seus dados foram apagados.",
        "privacy_confirm": "⚠️ Tem certeza? Isso apaga seu perfil, progresso e histórico.",
        "privacy_confirm_yes": "🗑️ Sim, apagar tudo",
        "privacy_cancel": "↩️ Cancelar",
        "privacy_footer": "ℹ️ Projeto informativo; não é certificação oficial de proficiência.",
        # genéricos / erros
        "btn_back": "⬅️ Voltar",
        "btn_menu": "🏠 Menu",
        "btn_cancel": "✖️ Cancelar",
        "err_generic": "😥 Ocorreu um erro. Tente novamente.",
        "err_rate": "⏳ Calma! Você está enviando mensagens rápido demais. Aguarde um instante.",
        "err_no_stt": "🎤 O reconhecimento de voz está indisponível no momento.",
        "err_no_tts": "🔇 Não consegui gerar o áudio agora.",
        "err_voice_gender": "ℹ️ O motor de voz atual não permite escolher o gênero; usei a voz padrão.",
        "not_understood": "Escolha uma opção no /menu 🙂",
    },
    "en": {
        "welcome_new": (
            "Hi, {nome}! I'm *LinguaBot* 🤖✨\n"
            "I'll help you learn languages right here on Telegram.\n\n"
            "Let's do a quick setup."
        ),
        "welcome_back": "Welcome back, {nome}! 👋",
        "resume_title": "You have learning in progress. What would you like to do?",
        "resume_continue": "▶️ Continue where I left off",
        "resume_restart": "🔄 Restart learning",
        "resume_settings": "⚙️ Change my settings",
        "resume_progress": "📊 View my progress",
        "choose_ui_lang": "🌍 First, choose the *interface* language:",
        "menu_title": "🏠 *Main menu* – pick an option:",
        "btn_menu": "🏠 Menu",
        "btn_back": "⬅️ Back",
        "saved": "✅ Preference updated!",
        "help": (
            "📖 *How to use LinguaBot*\n\n"
            "• /start – start / resume\n• /menu – main menu\n"
            "• /progresso – your progress\n• /config – settings\n\n"
            "You can send *text* or *voice messages* 🎤."
        ),
    },
    "es": {
        "welcome_new": (
            "¡Hola, {nome}! Soy *LinguaBot* 🤖✨\n"
            "Te ayudaré a aprender idiomas aquí en Telegram.\n\n"
            "Hagamos una configuración rápida."
        ),
        "welcome_back": "¡Hola de nuevo, {nome}! 👋",
        "resume_title": "Tienes un aprendizaje en curso. ¿Qué quieres hacer?",
        "resume_continue": "▶️ Continuar donde lo dejé",
        "resume_restart": "🔄 Reiniciar aprendizaje",
        "resume_settings": "⚙️ Cambiar mis ajustes",
        "resume_progress": "📊 Ver mi progreso",
        "choose_ui_lang": "🌍 Primero, elige el idioma de la *interfaz*:",
        "menu_title": "🏠 *Menú principal* – elige una opción:",
        "btn_menu": "🏠 Menú",
        "btn_back": "⬅️ Volver",
        "saved": "✅ ¡Preferencia actualizada!",
    },
}


def t(key: str, lang: UILang | str = UILang.PT, **kwargs: Any) -> str:
    """Retorna o texto traduzido (fallback para português)."""

    code = lang.value if isinstance(lang, UILang) else str(lang)
    table = MESSAGES.get(code, {})
    template = table.get(key) or MESSAGES["pt"].get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError):
            return template
    return template
