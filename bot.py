import os
import io
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import google.generativeai as genai
import edge_tts

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)

user_sessions = {}

def get_user_data(user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "step": "idioma",
            "idioma": None,
            "publico": None,
            "nivel": None,
            "voz": "en-US-AriaNeural",
            "modo": "conversa",
            "historico": []
        }
    return user_sessions[user_id]

@app.route('/')
def home():
    return "LinguaBoot Bot Online 24h!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user_data(user_id)
    
    if not data["idioma"]:
        await enviar_passo_idioma(update, context)
    elif not data["publico"]:
        await enviar_passo_publico(update, context)
    elif not data["nivel"]:
        await enviar_passo_nivel(update, context)
    else:
        await enviar_menu_principal(update, context)

async def enviar_passo_idioma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "👋 Olá! Bem-vindo ao LinguaBoot 🤖📚\n\n**Passo 1/3:** Qual idioma você deseja praticar?"
    kb = [
        [InlineKeyboardButton("🇺🇸 Inglês", callback_data="set_idioma_Inglês"), InlineKeyboardButton("🇪🇸 Espanhol", callback_data="set_idioma_Espanhol")],
        [InlineKeyboardButton("🇫🇷 Francês", callback_data="set_idioma_Francês"), InlineKeyboardButton("🇮🇹 Italiano", callback_data="set_idioma_Italiano")]
    ]
    markup = InlineKeyboardMarkup(kb)
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=markup)
    elif update.callback_query:
        try:
            await update.callback_query.message.edit_text(msg, parse_mode="Markdown", reply_markup=markup)
        except Exception:
            pass

async def enviar_passo_publico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    data = get_user_data(user_id)
    msg = f"✅ Idioma: **{data['idioma']}**\n\n**Passo 2/3:** Qual é o perfil de aprendizado?"
    kb = [
        [InlineKeyboardButton("👤 Adulto", callback_data="set_publico_Adulto")],
        [InlineKeyboardButton("👧 Modo Kids (Crianças)", callback_data="set_publico_Kids")]
    ]
    try:
        await update.callback_query.message.edit_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    except Exception:
        pass

async def enviar_passo_nivel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    data = get_user_data(user_id)
    msg = f"✅ Idioma: **{data['idioma']}**\n✅ Público: **{data['publico']}**\n\n**Passo 3/3:** Escolha o seu nível de conhecimento:"
    kb = [
        [InlineKeyboardButton("Iniciante (A1-A2)", callback_data="set_nivel_Iniciante")],
        [InlineKeyboardButton("Intermediário (B1-B2)", callback_data="set_nivel_Intermediário")],
        [InlineKeyboardButton("Avançado (C1-C2)", callback_data="set_nivel_Avançado")]
    ]
    try:
        await update.callback_query.message.edit_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    except Exception:
        pass

async def enviar_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    data = get_user_data(user_id)
    
    idioma = data['idioma'] or "Inglês"
    publico = data['publico'] or "Adulto"
    nivel = data['nivel'] or "Iniciante"
    tipo_voz = "Masculina" if any(v in data['voz'] for v in ['Guy', 'Alvaro', 'Henri', 'Diego']) else "Feminina"
    
    msg = (
        f"🎯 **Perfil Configurado com Sucesso!**\n\n"
        f"• **Idioma:** {idioma}\n"
        f"• **Público:** {publico}\n"
        f"• **Nível:** {nivel}\n"
        f"• **Voz:** {tipo_voz}\n"
        f"• **Modo Ativo:** {data['modo'].capitalize()}\n\n"
        f"Escolha um modo de estudo abaixo para praticar:"
    )

    kb = [
        [InlineKeyboardButton("🗣️ Modo Conversa Livre", callback_data="set_modo_conversa")],
        [
            InlineKeyboardButton("✍️ Teste Escrito", callback_data="set_modo_teste_escrita"),
            InlineKeyboardButton("🎙️ Teste Pronúncia", callback_data="set_modo_teste_pronuncia")
        ],
        [
            InlineKeyboardButton("🎙️ Tipo de Voz (M/F)", callback_data="menu_voz"),
            InlineKeyboardButton("⚙️ Refazer Configuração", callback_data="reset_config")
        ]
    ]

    markup = InlineKeyboardMarkup(kb)
    try:
        if update.message:
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=markup)
        elif update.callback_query:
            await update.callback_query.message.edit_text(msg, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        print(f"Edição de menu ignorada (conteúdo idêntico): {e}", flush=True)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = get_user_data(user_id)
    cb = query.data

    if cb.startswith("set_idioma_"):
        data["idioma"] = cb.replace("set_idioma_", "")
        voices = {"Inglês": "en-US-AriaNeural", "Espanhol": "es-ES-ElviraNeural", "Francês": "fr-FR-DeniseNeural", "Italiano": "it-IT-ElsaNeural"}
        data["voz"] = voices.get(data["idioma"], "en-US-AriaNeural")
        await enviar_passo_publico(update, context)
        return

    if cb.startswith("set_publico_"):
        data["publico"] = cb.replace("set_publico_", "")
        await enviar_passo_nivel(update, context)
        return

    if cb.startswith("set_nivel_"):
        data["nivel"] = cb.replace("set_nivel_", "")
        data["step"] = "pronto"
        await enviar_menu_principal(update, context)
        return

    if cb.startswith("set_modo_"):
        modo_limpo = cb.replace("set_modo_", "")
        data["modo"] = modo_limpo
        
        nomes_modos = {
            "conversa": "Conversa Livre 🗣️",
            "teste_escrita": "Teste Escrito ✍️",
            "teste_pronuncia": "Teste de Pronúncia 🎙️"
        }
        nome_exibicao = nomes_modos.get(modo_limpo, modo_limpo.capitalize())
        
        msg = (
            f"✅ **Modo ativo:** {nome_exibicao}\n\n"
            f"Já pode mandar uma mensagem de texto ou gravar um áudio no idioma **{data['idioma'] or 'Inglês'}** para começar a praticar!"
        )
        kb = [[InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="voltar_menu")]]
        
        try:
            await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        except Exception:
            pass
        return

    if cb == "reset_config":
        data["idioma"] = None
        data["publico"] = None
        data["nivel"] = None
        await enviar_passo_idioma(update, context)
        return

    if cb == "menu_voz":
        kb = [
            [InlineKeyboardButton("👩 Feminina", callback_data="set_voz_fem")],
            [InlineKeyboardButton("👨 Masculina", callback_data="set_voz_masc")],
            [InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="voltar_menu")]
        ]
        try:
            await query.edit_message_text("Escolha o tipo de voz do seu tutor:", reply_markup=InlineKeyboardMarkup(kb))
        except Exception:
            pass
        return

    if cb in ["set_voz_fem", "set_voz_masc"]:
        idioma_atual = data["idioma"] or "Inglês"
        if cb == "set_voz_fem":
            voices = {"Inglês": "en-US-AriaNeural", "Espanhol": "es-ES-ElviraNeural", "Francês": "fr-FR-DeniseNeural", "Italiano": "it-IT-ElsaNeural"}
        else:
            voices = {"Inglês": "en-US-GuyNeural", "Espanhol": "es-ES-AlvaroNeural", "Francês": "fr-FR-HenriNeural", "Italiano": "it-IT-DiegoNeural"}
            
        data["voz"] = voices.get(idioma_atual, "en-US-AriaNeural")
        
        # Confirmação visual da alteração da voz
        msg_confirmacao = f"✅ Voz alterada para **{'Feminina' if cb == 'set_voz_fem' else 'Masculina'}** com sucesso!"
        kb = [[InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data="voltar_menu")]]
        try:
            await query.edit_message_text(msg_confirmacao, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
        except Exception:
            await enviar_menu_principal(update, context)
        return

    if cb == "voltar_menu":
        await enviar_menu_principal(update, context)
        return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user_data(user_id)
    
    if not data["idioma"] or not data["publico"] or not data["nivel"]:
        await start(update, context)
        return

    contents = []

    if update.message.voice or update.message.audio:
        await update.message.reply_text("🎙️ Ouvindo seu áudio...")
        try:
            file_id = (update.message.voice or update.message.audio).file_id
            new_file = await context.bot.get_file(file_id)
            audio_bytes = await new_file.download_as_bytearray()
            
            contents.append({
                "mime_type": "audio/ogg",
                "data": bytes(audio_bytes)
            })
            contents.append("Transcreva o áudio enviado pelo aluno e responda em seguida mantendo o papel de professor de idiomas.")
        except Exception as e:
            print(f"ERRO AUDIO: {e}", flush=True)
            await update.message.reply_text("Erro ao carregar o áudio. Tente novamente!")
            return
    else:
        contents.append(update.message.text)

    system_prompt = (
        f"Você é o LinguaBoot, um tutor de idiomas especialista.\n"
        f"• Idioma das aulas: {data['idioma']}\n"
        f"• Nível do aluno: {data['nivel']}\n"
        f"• Público: {data['publico']}\n"
        f"• Modo atual: {data['modo']}\n\n"
    )

    if data["publico"] == "Kids":
        system_prompt += "Mantenha o tom extremamente lúdico, amigável e simples para crianças.\n"
    
    if data["modo"] == "conversa":
        system_prompt += f"Converse naturalmente sobre qualquer assunto no idioma {data['idioma']}. Ao final, adicione '💡 Dica do Professor:' com correções gentis em português."
    elif data["modo"] == "teste_escrita":
        system_prompt += f"Aplique um teste de escrita em {data['idioma']}. Avalie o texto (nota 0 a 10) e envie nova pergunta."
    elif data["modo"] == "teste_pronuncia":
        system_prompt += f"Avalie a pronúncia do áudio em {data['idioma']}. Transcreva o que entendeu e passe uma nova frase para repetir."

    resposta_ia = None
    modelos = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]

    for m in modelos:
        try:
            model = genai.GenerativeModel(model_name=m, system_instruction=system_prompt)
            response = model.generate_content(contents)
            resposta_ia = response.text
            break
        except Exception as e:
            print(f"Erro no modelo {m}: {e}", flush=True)

    if not resposta_ia:
        await update.message.reply_text("Erro na API do Gemini. Verifique se a chave GEMINI_API_KEY está correta no Render.")
        return

    try:
        await update.message.reply_text(resposta_ia)

        communicate = edge_tts.Communicate(resposta_ia, data["voz"])
        speech_bytes = bytearray()
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                speech_bytes.extend(chunk["data"])

        speech_buffer = io.BytesIO(speech_bytes)
        speech_buffer.name = "response.mp3"
        await update.message.reply_voice(voice=speech_buffer)

    except Exception as e:
        print(f"ERRO TTS: {e}", flush=True)

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("ERRO: BOT_TOKEN ausente!", flush=True)
        exit(1)

    threading.Thread(target=run_flask, daemon=True).start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.ALL, handle_message))

    print("LinguaBoot rodando com sucesso!", flush=True)
    application.run_polling(drop_pending_updates=True)
