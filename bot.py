import os
import logging
import threading
import tempfile
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# --- CONFIG ---
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN or not GEMINI_API_KEY:
    logging.error("Faltando BOT_TOKEN ou GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "LinguaBoot com Gemini Online!"

user_languages = {}
user_levels = {}

# --- FUNÇÕES GEMINI ---
def transcribe_and_correct_gemini(file_path, lang="english"):
    try:
        # Gemini 1.5 consegue ler áudio direto
        audio_file = genai.upload_file(file_path)
        
        prompt = f"""
        Você é o LinguaBoot, professor de idiomas nativo de {lang}.
        
        1. Transcreva o áudio exatamente
        2. Corrija a gramática
        3. Traduza para português
        4. Explique o erro principal
        5. Dê dica de pronúncia
        6. Dê nota 0-10
        
        Seja animado, use emojis. Se não entender o áudio, diga.
        """
        
        response = model.generate_content([prompt, audio_file])
        return response.text
    except Exception as e:
        logging.error(f"Erro Gemini Audio: {e}")
        return None

def correct_text_gemini(text, lang="english"):
    try:
        prompt = f"""
        Você é o LinguaBoot, professor de {lang} super divertido.

        Aluno escreveu/falou: "{text}"

        Responda com:
        📝 Frase corrigida:
        🇧🇷 Tradução:
        📚 Correção explicada:
        🗣️ Dica de pronúncia:
        ⭐ Nota 0-10 + motivação

        Use emojis e seja curto e animado.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Erro Gemini Text: {e}")
        return f"Recebi: {text}\nContinue praticando! 🚀"

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_levels[user_id] = 1
    await update.message.reply_text(
        "Olá! Eu sou o LinguaBoot com Gemini 🤖✨\n\n"
        "Seu professor de idiomas turbinado com Google Gemini!\n\n"
        "🎙️ Mande ÁUDIO em Inglês ou Espanhol\n"
        "📝 Ou digite um texto\n"
        "Eu corrijo, traduzo e dou nota!\n\n"
        "Comandos:\n"
        "/english - Inglês 🇺🇸\n"
        "/spanish - Espanhol 🇪🇸\n"
        "/level - Ver seu nível\n"
        "/help - Ajuda"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Como usar o LinguaBoot Gemini:\n\n"
        "1. Escolha /english ou /spanish\n"
        "2. Mande um áudio falando\n"
        "3. Eu transcrevo e corrijo com Gemini 1.5\n"
        "4. Ganhe XP e suba de nível!\n\n"
        "Dica: Quanto mais você pratica, mais XP ganha!"
    )

async def set_english(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_languages[update.effective_user.id] = "english"
    await update.message.reply_text("Modo Inglês ativado! 🇺🇸 Mande seu áudio ou texto!")

async def set_spanish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_languages[update.effective_user.id] = "spanish"
    await update.message.reply_text("Modo Espanhol ativado! 🇪🇸 Mande seu áudio ou texto!")

async def level_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    level = user_levels.get(user_id, 1)
    await update.message.reply_text(f"🏆 Seu nível atual: {level}\nContinue praticando pra subir!")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "english")
    
    await update.message.reply_text("Analisando com Gemini... 🤔✨")
    
    correction = correct_text_gemini(update.message.text, lang)
    
    # Sistema de XP simples
    user_levels[user_id] = user_levels.get(user_id, 1) + 1
    
    await update.message.reply_text(correction)
    await update.message.reply_text(f"✨ +1 XP! Você está no nível {user_levels[user_id]}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = user_languages.get(user_id, "english")
    
    await update.message.reply_text("Recebi seu áudio! Gemini está transcrevendo... 🎧✨")

    try:
        file = await context.bot.get_file(update.message.voice.file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tf:
            await file.download_to_drive(tf.name)
            temp_path = tf.name

        result = transcribe_and_correct_gemini(temp_path, lang)
        os.unlink(temp_path)

        if not result:
            await update.message.reply_text("Não consegui entender o áudio, tenta de novo? 🎤")
            return

        user_levels[user_id] = user_levels.get(user_id, 1) + 2
        await update.message.reply_text(result)
        await update.message.reply_text(f"🎙️ +2 XP por áudio! Nível: {user_levels[user_id]}")

    except Exception as e:
        logging.error(f"Erro voice: {e}")
        await update.message.reply_text("Deu um erro no áudio, tenta mandar de novo!")

def run_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("english", set_english))
    application.add_handler(CommandHandler("spanish", set_spanish))
    application.add_handler(CommandHandler("level", level_cmd))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.AUDIO, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logging.info("Bot LinguaBoot Gemini started - polling...")
    application.run_polling()

# --- RENDER FIX - TEM QUE FICAR FORA DO IF ---
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)
