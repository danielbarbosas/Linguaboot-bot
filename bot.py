import os
import logging
import threading
import tempfile
import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import google.generativeai as genai

# =============================================================================
# CONFIG - LINGUABOOT MENU - VERSAO QUE RODOU
# =============================================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model_flash = genai.GenerativeModel("gemini-1.5-flash")

app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "LinguaBoot MENU Online!"

@app_flask.route("/health")
def health():
    return {"status": "ok", "bot": "linguaboot-menu"}

# =============================================================================
# BANCO MEMORIA - MENU
# =============================================================================
user_data = {}
user_history = {}
daily_streak = {}

def get_user_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"lang": "english", "level": 1, "xp": 0, "total_audios": 0, "total_texts": 0, "joined": str(datetime.datetime.now())}
    return user_data[user_id]

def get_user_lang(user_id):
    return get_user_data(user_id).get("lang", "english")

def add_xp(user_id, amount):
    data = get_user_data(user_id)
    data["xp"] += amount
    leveled_up = False
    if data["xp"] >= 100:
        data["level"] += 1
        data["xp"] -= 100
        leveled_up = True
    return leveled_up, data["level"], data["xp"]

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🇺🇸 Inglês", callback_data="lang_english")],
        [InlineKeyboardButton("🇪🇸 Espanhol", callback_data="lang_spanish")],
        [InlineKeyboardButton("🏆 Meu Nível", callback_data="my_level"), InlineKeyboardButton("📊 Stats", callback_data="my_stats")],
        [InlineKeyboardButton("🔥 Streak", callback_data="streak"), InlineKeyboardButton("❓ Ajuda", callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)

# =============================================================================
# GEMINI FUNCOES
# =============================================================================
def correct_text_gemini(text, lang="english"):
    lang_name = "Inglês" if lang == "english" else "Espanhol"
    prompt = f'Você é LinguaBoot professor de {lang_name}. Aluno: "{text}". Responda: 📝 Corrigido: 🇧🇷 Tradução: 📚 Explicação: 🗣️ Pronúncia: ⭐ Nota 0-10. Use emojis.'
    try:
        r = model_flash.generate_content(prompt)
        return r.text
    except Exception as e:
        logger.error(e)
        return f"Recebi: {text} - Continue! 🚀"

def transcribe_gemini(file_path, lang="english"):
    try:
        audio = genai.upload_file(file_path)
        lang_name = "Inglês" if lang == "english" else "Espanhol"
        prompt = f"Transcreva áudio em {lang_name}, corrija, traduza PT-BR, explique erro, nota 0-10. Use emojis."
        r = model_flash.generate_content([prompt, audio])
        return r.text
    except Exception as e:
        logger.error(e)
        return None

# =============================================================================
# HANDLERS MENU
# =============================================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user_data(user_id)
    await update.message.reply_text(
        f"Olá {update.effective_user.first_name}! Sou o LinguaBoot MENU 🤖✨\n\nEscolha abaixo:",
        reply_markup=get_main_menu()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 1. Escolha idioma 2. Mande áudio 3. Ganhe XP! Áudio=20XP Texto=10XP", reply_markup=get_main_menu())

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = get_user_data(user_id)
    action = query.data

    if action == "main_menu":
        await query.edit_message_text("👋 Menu Principal:", reply_markup=get_main_menu())
    elif action.startswith("lang_"):
        lang = action.split("_")[1]
        data["lang"] = lang
        flag = "🇺🇸 Inglês" if lang == "english" else "🇪🇸 Espanhol"
        await query.edit_message_text(f"✅ Modo {flag} ativado!\nMande áudio ou texto!", reply_markup=get_main_menu())
    elif action == "my_level":
        await query.edit_message_text(f"🏆 Nível: {data['level']}\nXP: {data['xp']}/100\nIdioma: {data['lang']}", reply_markup=get_main_menu())
    elif action == "my_stats":
        await query.edit_message_text(f"📊 Áudios: {data['total_audios']}\nTextos: {data['total_texts']}\nDesde: {data['joined'][:10]}", reply_markup=get_main_menu())
    elif action == "streak":
        streak = daily_streak.get(user_id, 0)
        await query.edit_message_text(f"🔥 Streak: {streak} dias!", reply_markup=get_main_menu())
    elif action == "help":
        await query.edit_message_text("📚 Escolha idioma, mande áudio, ganhe XP!", reply_markup=get_main_menu())

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_lang = get_user_lang(user_id)
    data = get_user_data(user_id)
    await update.message.reply_text("🤔 Analisando com Gemini... ✨")
    correction = correct_text_gemini(update.message.text, user_lang)
    data["total_texts"] += 1
    leveled_up, level, xp = add_xp(user_id, 10)
    await update.message.reply_text(correction)
    if leveled_up:
        await update.message.reply_text(f"🎉 LEVEL UP! Nível {level}! 🚀", reply_markup=get_main_menu())
    else:
        await update.message.reply_text(f"✨ +10 XP! ({xp}/100) Nível: {level}", reply_markup=get_main_menu())

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_lang = get_user_lang(user_id)
    data = get_user_data(user_id)
    await update.message.reply_text("🎧 Recebi áudio! Transcrevendo... ✨")
    temp_path = None
    try:
        f = await context.bot.get_file(update.message.voice.file_id if update.message.voice else update.message.audio.file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tf:
            await f.download_to_drive(tf.name)
            temp_path = tf.name
        result = transcribe_gemini(temp_path, user_lang)
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        if not result:
            await update.message.reply_text("😕 Não entendi, tenta de novo! 🎤", reply_markup=get_main_menu())
            return
        data["total_audios"] += 1
        daily_streak[user_id] = daily_streak.get(user_id, 0) + 1
        leveled_up, level, xp = add_xp(user_id, 20)
        await update.message.reply_text(result)
        if leveled_up:
            await update.message.reply_text(f"🎉 LEVEL UP! Nível {level}! 🚀🎙️", reply_markup=get_main_menu())
        else:
            await update.message.reply_text(f"🎙️ +20 XP! ({xp}/100) Nível: {level} | Streak: {daily_streak[user_id]} 🔥", reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Erro audio: {e}")
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        await update.message.reply_text("❌ Erro no áudio, mande de novo!", reply_markup=get_main_menu())

def run_telegram_bot():
    logger.info("Iniciando LinguaBoot MENU com Gemini...")
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback_handler))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    logger.info("Bot MENU polling iniciado!")
    application.run_polling(drop_pending_updates=True)

# FIX RENDER - TEM QUE FICAR FORA DO IF - ESSA FOI A CORREÇÃO QUE FEZ RODAR
bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
bot_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)
