import os, logging, threading, tempfile, random
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from gTTS import gTTS
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print(f"=== CHECK ENV ===")
print(f"BOT_TOKEN existe? {bool(BOT_TOKEN)}")
print(f"GEMINI_API_KEY existe? {bool(GEMINI_API_KEY)}")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

app = Flask(__name__)

@app.route("/")
def home():
    return "LinguaBoot COMPLETO Online!"

# BANCO DE DADOS EM MEMÓRIA
user_data = {}

ADULT_IMAGES = {
    "apple": "https://loremflickr.com/400/400/apple",
    "dog": "https://loremflickr.com/400/400/dog",
    "house": "https://loremflickr.com/400/400/house",
    "car": "https://loremflickr.com/400/400/car",
    "book": "https://loremflickr.com/400/400/book",
    "water": "https://loremflickr.com/400/400/water"
}

CHILD_IMAGES = {
    "cat": "https://loremflickr.com/400/400/cat,cute",
    "ball": "https://loremflickr.com/400/400/ball,colorful",
    "sun": "https://loremflickr.com/400/400/sun,cartoon",
    "banana": "https://loremflickr.com/400/400/banana,cute",
    "fish": "https://loremflickr.com/400/400/fish,cartoon"
}

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {"level": "iniciante", "voice": "mulher", "mode": "menu", "lang": "english", "current_word": None, "child_index": 0, "xp": 0}
    return user_data[uid]

def get_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 1. Conversa Livre", callback_data="mode_free")],
        [InlineKeyboardButton("📚 2. Gramática", callback_data="mode_grammar")],
        [InlineKeyboardButton("🗣️ 3. Pronúncia com Imagem", callback_data="mode_pronuncia")],
        [InlineKeyboardButton("🏆 4. Nível", callback_data="menu_level")],
        [InlineKeyboardButton("🎙️ 5. Voz Homem/Mulher", callback_data="menu_voice")],
        [InlineKeyboardButton("👶 6. Modo Infantil", callback_data="mode_infantil")],
    ])

def get_level_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌱 Iniciante", callback_data="level_iniciante")],
        [InlineKeyboardButton("🌿 Intermediário", callback_data="level_intermediario")],
        [InlineKeyboardButton("🌳 Avançado", callback_data="level_avancado")],
        [InlineKeyboardButton("⬅️ Voltar Menu", callback_data="main_menu")]
    ])

def get_voice_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👩 Voz Mulher", callback_data="voice_mulher")],
        [InlineKeyboardButton("👨 Voz Homem", callback_data="voice_homem")],
        [InlineKeyboardButton("⬅️ Voltar Menu", callback_data="main_menu")]
    ])

def gemini_text(prompt):
    try:
        if not client:
            return "ERRO: GEMINI_API_KEY não configurada no Render!"
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        logger.error(f"Erro Gemini Text: {e}")
        return f"Erro Gemini: {e}"

def transcribe_audio(path):
    try:
        if not client:
            return None
        uploaded = client.files.upload(
            file=path,
            config=types.UploadFileConfig(mime_type="audio/ogg")
        )
        r = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=["Transcreva exatamente o que foi falado em inglês, só a transcrição.", uploaded]
        )
        return r.text.strip()
    except Exception as e:
        logger.error(f"Erro transcrição: {e}")
        return None

def create_audio_file(text, voice_choice, is_child=False):
    try:
        tld = "co.uk" if voice_choice == "homem" else "com"
        slow = True if is_child else False
        clean_text = text[:200].rsplit('.', 1)[0] if len(text) > 200 else text
        tts = gTTS(text=clean_text, lang='en', tld=tld, slow=slow)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(tmp.name)
        return tmp.name
    except Exception as e:
        logger.error(f"Erro gTTS: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_user(update.effective_user.id)
    await update.message.reply_text(
        f"Olá {update.effective_user.first_name}! Eu sou o LinguaBoot 🤖✨\n\nEscolha o que quer praticar hoje:",
        reply_markup=get_menu()
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    d = get_user(uid)
    data = q.data

    if data == "main_menu":
        d["mode"] = "menu"
        await q.edit_message_text("Menu Principal - Escolha:", reply_markup=get_menu())
    elif data == "menu_level":
        await q.edit_message_text(f"Nível atual: {d['level'].upper()}\nEscolha seu nível:", reply_markup=get_level_menu())
    elif data.startswith("level_"):
        d["level"] = data.split("_")[1]
        await q.edit_message_text(f"✅ Nível {d['level']} ativado!", reply_markup=get_menu())
    elif data == "menu_voice":
        await q.edit_message_text(f"Voz atual: {d['voice']}\nEscolha quem vai responder:", reply_markup=get_voice_menu())
    elif data.startswith("voice_"):
        d["voice"] = data.split("_")[1]
        await q.edit_message_text(f"✅ Voz {d['voice']} ativada! Agora vou falar como {d['voice']}.", reply_markup=get_menu())
    elif data == "mode_free":
        d["mode"] = "free"
        await q.edit_message_text("💬 MODO CONVERSA LIVRE\nMande áudio ou texto em inglês e eu corrijo e respondo por áudio!\n\nMande sua primeira frase:", reply_markup=get_menu())
    elif data == "mode_grammar":
        d["mode"] = "grammar"
        prompt = f"Ensine gramática em inglês para nível {d['level']}. Dê 1 regra curta com exemplo e 1 exercício."
        resp = gemini_text(prompt)
        await q.edit_message_text(f"📚 MODO GRAMÁTICA - Nível {d['level']}\n\n{resp}\n\nResponda o exercício por texto ou áudio!", reply_markup=get_menu())
    elif data == "mode_pronuncia":
        d["mode"] = "pronuncia"
        word, url = random.choice(list(ADULT_IMAGES.items()))
        d["current_word"] = word
        await context.bot.send_photo(chat_id=uid, photo=url, caption=f"🗣️ O que é isso? Pronuncie em inglês: **{word.upper()}**\n\nMande um áudio falando essa palavra!")
        await q.edit_message_text("Imagem enviada! 👇 Pronuncie a palavra da imagem por áudio.", reply_markup=get_menu())
    elif data == "mode_infantil":
        d["mode"] = "infantil"
        d["child_index"] = 0
        word, url = list(CHILD_IMAGES.items())[0]
        d["current_word"] = word
        audio_path = create_audio_file(f"Hello! What is this? Say {word}!", d["voice"], is_child=True)
        await context.bot.send_photo(chat_id=uid, photo=url, caption=f"👶 MODO INFANTIL - O que é isso?\nDiga: {word.upper()} 🥰")
        if audio_path:
            with open(audio_path, 'rb') as voice_file:
                await context.bot.send_voice(chat_id=uid, voice=voice_file)
            os.unlink(audio_path)
        await q.edit_message_text("👶 Modo Infantil iniciado! Olha a imagem acima!", reply_markup=get_menu())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    d = get_user(uid)
    text = update.message.text
    if d["mode"] == "free":
        prompt = f"Você é professor de inglês amigável nível {d['level']}. Aluno disse: '{text}'. Corrija se tiver erro, explique curto, e continue a conversa. Responda em inglês + tradução curta PT-BR."
        resp = gemini_text(prompt)
        await update.message.reply_text(resp)
        audio_path = create_audio_file(resp, d["voice"])
        if audio_path:
            with open(audio_path, 'rb') as voice_file:
                await context.bot.send_voice(chat_id=uid, voice=voice_file)
            os.unlink(audio_path)
    elif d["mode"] == "grammar":
        prompt = f"Aluno nível {d['level']} respondeu exercício: '{text}'. Avalie, corrija se errou, parabenize se acertou e mande próximo exercício."
        resp = gemini_text(prompt)
        await update.message.reply_text(resp, reply_markup=get_menu())
    else:
        await update.message.reply_text("Escolha uma opção no menu /start", reply_markup=get_menu())

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    d = get_user(uid)
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
    
    try:
        file = await context.bot.get_file(update.message.voice.file_id)
        await file.download_to_drive(tf.name)
        transcricao = transcribe_audio(tf.name)
    finally:
        if os.path.exists(tf.name):
            os.unlink(tf.name)

    if not transcricao:
        await update.message.reply_text("Não entendi o áudio, tente de novo! 🎤", reply_markup=get_menu())
        return

    if d["mode"] == "pronuncia":
        target = d.get("current_word", "")
        prompt = f"Aluno deveria pronunciar '{target}' e disse '{transcricao}'. A pronúncia está correta? Responda curto com emojis."
        avaliacao = gemini_text(prompt)
        await update.message.reply_text(f"Você disse: '{transcricao}'\n\n{avaliacao}")
        
        audio_path = create_audio_file(f"The correct pronunciation is {target}.", d["voice"])
        if audio_path:
            with open(audio_path, 'rb') as voice_file:
                await context.bot.send_voice(chat_id=uid, voice=voice_file)
            os.unlink(audio_path)
            
        word, url = random.choice(list(ADULT_IMAGES.items()))
        d["current_word"] = word
        await context.bot.send_photo(chat_id=uid, photo=url, caption=f"Próxima! Pronuncie: {word.upper()} 🗣️")

    elif d["mode"] == "infantil":
        target = d.get("current_word", "")
        acertou = target.lower() in transcricao.lower()
        if acertou:
            msg = f"🎉 Muito bem! Você disse {target} perfeitamente! 👏🥰"
            audio_path = create_audio_file(f"Very good! You said {target}! Excellent!", d["voice"], is_child=True)
        else:
            msg = f"Quase! Você disse '{transcricao}'. Tente dizer: {target}. Você consegue! 💪"
            audio_path = create_audio_file(f"Almost! Say {target}. Repeat after me! {target}", d["voice"], is_child=True)
            
        await update.message.reply_text(msg)
        if audio_path:
            with open(audio_path, 'rb') as voice_file:
                await context.bot.send_voice(chat_id=uid, voice=voice_file)
            os.unlink(audio_path)
            
        d["child_index"] = (d["child_index"] + 1) % len(CHILD_IMAGES)
        word, url = list(CHILD_IMAGES.items())[d["child_index"]]
        d["current_word"] = word
        await context.bot.send_photo(chat_id=uid, photo=url, caption=f"👶 Agora essa! Diga: {word.upper()}")

    elif d["mode"] == "free":
        prompt = f"Aluno nível {d['level']} disse por voz: '{transcricao}'. Corrija pronúncia e responda continuando conversa. Curto."
        resp = gemini_text(prompt)
        await update.message.reply_text(f"Ouvi: '{transcricao}'\n\n{resp}")
        
        audio_path = create_audio_file(resp, d["voice"])
        if audio_path:
            with open(audio_path, 'rb') as voice_file:
                await context.bot.send_voice(chat_id=uid, voice=voice_file)
            os.unlink(audio_path)
    else:
        await update.message.reply_text("Primeiro escolha um modo no /start", reply_markup=get_menu())

def run_bot():
    if not BOT_TOKEN:
        print("ERRO FATAL: BOT_TOKEN vazio no Environment!")
        return
    print("=== BOT INICIADO - POLLING COMPLETO ===")
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(buttons))
    app_bot.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app_bot.run_polling(drop_pending_updates=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
