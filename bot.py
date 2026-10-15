import os, logging, threading, tempfile, random
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from gtts import gTTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print(f"=== CHECK ENV ===")
print(f"BOT_TOKEN existe? {bool(BOT_TOKEN)}")
print(f"GEMINI_API_KEY existe? {bool(GEMINI_API_KEY)}")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

app = Flask(__name__)
@app.route("/")
def home(): return "LinguaBoot ONLINE - Verifique Environment!"

user_data = {}
ADULT_IMAGES = {"apple":"https://loremflickr.com/400/400/apple","dog":"https://loremflickr.com/400/400/dog","house":"https://loremflickr.com/400/400/house"}
CHILD_IMAGES = {"cat":"https://loremflickr.com/400/400/cat,cute","ball":"https://loremflickr.com/400/400/ball,colorful","sun":"https://loremflickr.com/400/400/sun,cartoon"}

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {"level":"iniciante","voice":"mulher","mode":"menu","current_word":None,"child_index":0}
    return user_data[uid]

def get_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 1. Conversa Livre", callback_data="mode_free")],
        [InlineKeyboardButton("📚 2. Gramática", callback_data="mode_grammar")],
        [InlineKeyboardButton("🗣️ 3. Pronúncia", callback_data="mode_pronuncia")],
        [InlineKeyboardButton("🏆 4. Nível", callback_data="menu_level")],
        [InlineKeyboardButton("🎙️ 5. Voz", callback_data="menu_voice")],
        [InlineKeyboardButton("👶 6. Infantil", callback_data="mode_infantil")],
    ])

def get_level_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🌱 Iniciante", callback_data="level_iniciante")],[InlineKeyboardButton("🌿 Interm.", callback_data="level_intermediario")],[InlineKeyboardButton("🌳 Avançado", callback_data="level_avancado")],[InlineKeyboardButton("⬅️ Voltar", callback_data="main_menu")]])

def get_voice_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("👩 Mulher", callback_data="voice_mulher")],[InlineKeyboardButton("👨 Homem", callback_data="voice_homem")],[InlineKeyboardButton("⬅️ Voltar", callback_data="main_menu")]])

def gemini_text(p):
    if not model: return "ERRO: GEMINI_API_KEY não configurada no Render!"
    try: return model.generate_content(p).text
    except Exception as e: return f"Erro Gemini: {e}"

async def start(update, context):
    get_user(update.effective_user.id)
    await update.message.reply_text("Olá! LinguaBoot completo 🤖\nEscolha:", reply_markup=get_menu())

async def buttons(update, context):
    q=update.callback_query; await q.answer(); uid=q.from_user.id; d=get_user(uid); data=q.data
    if data=="main_menu": await q.edit_message_text("Menu:", reply_markup=get_menu())
    elif data=="menu_level": await q.edit_message_text(f"Nível: {d['level']}", reply_markup=get_level_menu())
    elif data.startswith("level_"): d["level"]=data.split("_")[1]; await q.edit_message_text(f"✅ Nível {d['level']}", reply_markup=get_menu())
    elif data=="menu_voice": await q.edit_message_text(f"Voz: {d['voice']}", reply_markup=get_voice_menu())
    elif data.startswith("voice_"): d["voice"]=data.split("_")[1]; await q.edit_message_text(f"✅ Voz {d['voice']}", reply_markup=get_menu())
    elif data=="mode_free": d["mode"]="free"; await q.edit_message_text("💬 Mande áudio/texto em inglês! Eu respondo com áudio.", reply_markup=get_menu())
    elif data=="mode_grammar": d["mode"]="grammar"; r=gemini_text(f"Ensine gramática nível {d['level']} com exercício"); await q.edit_message_text(r, reply_markup=get_menu())
    elif data=="mode_pronuncia": d["mode"]="pronuncia"; w,u=random.choice(list(ADULT_IMAGES.items())); d["current_word"]=w; await context.bot.send_photo(uid, photo=u, caption=f"Pronuncie: {w.upper()}"); await q.edit_message_text("Imagem enviada!", reply_markup=get_menu())
    elif data=="mode_infantil": d["mode"]="infantil"; w,u=list(CHILD_IMAGES.items())[0]; d["current_word"]=w; await context.bot.send_photo(uid, photo=u, caption=f"👶 Diga: {w.upper()}"); await q.edit_message_text("Modo infantil!", reply_markup=get_menu())

async def handle_text(update, context):
    d=get_user(update.effective_user.id)
    resp=gemini_text(f"Corrija '{update.message.text}' nível {d['level']} e responda curto com emoji")
    await update.message.reply_text(resp, reply_markup=get_menu())

async def handle_voice(update, context):
    d=get_user(update.effective_user.id)
    tf=tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
    file=await context.bot.get_file(update.message.voice.file_id)
    await file.download_to_drive(tf.name)
    try:
        f=genai.upload_file(tf.name) if model else None
        trans=model.generate_content(["Transcreva", f]).text if model else "teste"
    except: trans="erro"
    os.unlink(tf.name)
    await update.message.reply_text(f"Ouvi: {trans}\nMuito bem! ✅", reply_markup=get_menu())
    # audio de volta
    try:
        tld="co.uk" if d["voice"]=="homem" else "com"
        tts=gTTS(text=f"Very good! You said {trans}", lang='en', tld=tld)
        tmp=tempfile.NamedTemporaryFile(delete=False, suffix=".mp3"); tts.save(tmp.name)
        await context.bot.send_voice(chat_id=update.effective_user.id, voice=open(tmp.name,'rb')); os.unlink(tmp.name)
    except: pass

def run_bot():
    if not BOT_TOKEN:
        print("ERRO FATAL: BOT_TOKEN não existe no Environment do Render!")
        return
    print("=== BOT INICIADO - POLLING ===")
    a=ApplicationBuilder().token(BOT_TOKEN).build()
    a.add_handler(CommandHandler("start", start))
    a.add_handler(CallbackQueryHandler(buttons))
    a.add_handler(MessageHandler(filters.VOICE, handle_voice))
    a.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    a.run_polling(drop_pending_updates=True)

threading.Thread(target=run_bot, daemon=True).start()

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
