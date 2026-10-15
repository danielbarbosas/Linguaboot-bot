import os
import logging
import threading
import tempfile
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import google.generativeai as genai

# --- CONFIG ---
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "LinguaBoot MENU Online!"

user_data = {}

def get_user_lang(user_id):
    return user_data.get(user_id, {}).get("lang", "english")

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🇺🇸 Inglês", callback_data='lang_english')],
        [InlineKeyboardButton("🇪🇸 Espanhol", callback_data='lang_spanish')],
        [InlineKeyboardButton("🏆 Meu Nível", callback_data='my_level'),
         InlineKeyboardButton("❓ Ajuda", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_lang_menu():
    keyboard = [
        [InlineKeyboardButton("🇺🇸 English", callback_data='lang_english')],
        [InlineKeyboardButton("🇪🇸 Español", callback_data='lang_spanish')],
        [InlineKeyboardButton("⬅️ Voltar", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- GEMINI ---
def correct_gemini(text, lang):
    prompt = f"""
    Você é LinguaBoot, professor nativo de {lang}.
    Aluno: "{text}"
    Responda:
    📝 Corrigido:
    🇧🇷 Tradução:
    📚 Explicação curta:
    🗣️ Pronúncia:
    ⭐ Nota 0-10
    Seja animado com emojis.
    """
    try:
        r = model.generate_content(prompt)
        return r.text
    except Exception as e:
        logging.error(e)
        return f"Recebi: {text} - Continue! 🚀"

def transcribe_gemini(file_path, lang):
    try:
        audio = genai.upload_file(file_path)
        prompt = f"Transcreva o áudio em {lang}, corrija, traduza pro pt-br, explique o erro, dê nota 0-10. Use emojis."
        r = model.generate_content([prompt, audio])
        return r.text
    except Exception as e:
        logging.error(e)
        return None

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data:
        user_data[user_id] = {"lang": "english", "level": 1, "xp": 0}

    await update.message.reply_text(
        "👋 Olá! Eu sou o *LinguaBoot com MENU* 🤖✨\n\n"
        "Escolha uma opção abaixo:",
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {"lang": "english", "level": 1, "xp": 0}

    if query.data == 'main_menu':
        await query.edit_message_text("👋 Menu Principal:", reply_markup=get_main_menu())

    elif query.data.startswith('lang_'):
        lang = query.data.split('_')[1]
        user_data[user_id]['lang'] = lang
        flag = "🇺🇸 Inglês" if lang == "english" else "🇪🇸 Espanhol"
        await query.edit_message_text(
            f"✅ Modo {flag} ativado!\n\nAgora me mande um ÁUDIO ou TEXTO em {flag}!",
            reply_markup=get_main_menu()
        )

    elif query.data == 'my_level':
        data = user_data[user_id]
        await query.edit_message_text(
            f"🏆 *Seu Progresso:*\n\nNível: {data['level']}\nXP: {data['xp']}\nIdioma: {data['lang']}",
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

    elif query.data == 'help':
        await query.edit_message_text(
            "📚 *Como usar:*\n\n1. Escolha o idioma no menu\n2. Mande áudio\n3. Receba correção com nota\n4. Ganhe XP!",
            reply_markup=get_main_menu(),
            parse_mode='Markdown'
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)

    if user_id not in user_data:
        user_data[user_id] = {"lang": lang, "level": 1, "xp": 0}

    await update.message.reply_text("Analisando com Gemini... 🤔")
    correction = correct_gemini(update.message.text, lang)

    user_data[user_id]['xp'] += 10
    if user_data[user_id]['xp'] >= 100:
        user_data[user_id]['level'] += 1
        user_data[user_id]['xp'] = 0

    await update.message.reply_text(correction)
    await update.message.reply_text(
        f"✨ +10 XP! Nível: {user_data[user_id]['level']}",
        reply_markup=get_main_menu()
    )

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    await update.message.reply_text("🎧 Recebi seu áudio! Transcrevendo...")

    try:
        file = await context.bot.get_file(update.message.voice.file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tf:
            await file.download_to_drive(tf.name)
            temp_path = tf.name

        result = transcribe_gemini(temp_path, lang)
        os.unlink(temp_path)

        if not result:
            await update.message.reply_text("Não entendi o áudio, tenta de novo? 🎤", reply_markup=get_main_menu())
            return

        if user_id not in user_data:
            user_data[user_id] = {"lang": lang, "level": 1, "xp": 0}
        user_data[user_id]['xp'] += 20

        await update.message.reply_text(result)
        await update.message.reply_text(
            f"🎙️ +20 XP por áudio! Total: {user_data[user_id]['xp']} XP",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        logging.error(e)
        await update.message.reply_text("Erro no áudio, manda de novo!", reply_markup=get_main_menu())

def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logging.info("Bot LinguaBoot MENU - polling...")
    app.run_polling()

# --- FIX RENDER - FORA DO IF ---
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)
