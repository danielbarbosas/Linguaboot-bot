import os
import io
import re
import asyncio
import tempfile
from flask import Flask
import threading
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
        }
    return user_sessions[user_id]

def limpar_texto_para_tts(texto):
    texto_limpo = re.sub(r'[*_~`#]', '', texto)
    return texto_limpo[:500]

@app.route('/')
def home():
    return "LinguaBoot Online"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user_data(user_id)
    
    if not data["idioma"]:
        await enviar_passo_idioma(update, context)
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
        await update.callback_query.message.edit_text(msg, parse_mode="Markdown", reply_markup=markup)

async def enviar_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🎯 **LinguaBoot Prontinho!**\n\nPode enviar qualquer mensagem de texto ou áudio para conversar comigo!"
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = get_user_data(user_id)
    cb = query.data

    if cb.startswith("set_idioma_"):
        data["idioma"] = cb.replace("set_idioma_", "")
        await enviar_menu_principal(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        await update.message.reply_text("Por favor, envie uma mensagem de texto!")
        return

    texto_usuario = update.message.text
    user_id = update.effective_user.id
    data = get_user_data(user_id)
    idioma = data["idioma"] or "Inglês"

    # Envia confirmação imediata para testar a resposta do Telegram
    msg_espera = await update.message.reply_text("🤔 A pensar na resposta...")

    try:
        # Chamada direta e simplificada do Gemini
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"Você é um tutor de {idioma}. Responda de forma curta e amigável ao aluno: {texto_usuario}"
        
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
        
        resposta_ia = response.text if response and response.text else "Não consegui gerar a resposta."

        # Atualiza a mensagem no Telegram com a resposta da IA
        await msg_espera.edit_text(resposta_ia)

        # Geração do áudio
        try:
            texto_tts = limpar_texto_para_tts(resposta_ia)
            communicate = edge_tts.Communicate(texto_tts, data["voz"])
            speech_bytes = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    speech_bytes.extend(chunk["data"])

            if speech_bytes:
                speech_buffer = io.BytesIO(speech_bytes)
                speech_buffer.name = "response.mp3"
                await update.message.reply_voice(voice=speech_buffer)
        except Exception as e_tts:
            print(f"Erro TTS: {e_tts}")

    except Exception as e:
        print(f"Erro Gemini: {e}")
        await msg_espera.edit_text(f"⚠️ Erro ao consultar o Gemini: {e}")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

if __name__ == "__main__":
    if not BOT_TOKEN or not GEMINI_API_KEY:
        print("ERRO: Tokens ausentes!")
        exit(1)

    threading.Thread(target=run_flask, daemon=True).start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot em execução...")
    application.run_polling(drop_pending_updates=True)
