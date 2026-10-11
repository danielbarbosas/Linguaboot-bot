import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
print(f"BOT_TOKEN existe? {bool(BOT_TOKEN)}")

app = Flask(__name__)

@app.route('/')
def home():
    return "LinguaBoot Bot Online 24h!"

async def start(update: Update, context):
    await update.message.reply_text(
        "Olá! Eu sou o LinguaBoot 🤖📚\n\n"
        "Seu professor de idiomas!\n"
        "Me manda um áudio em inglês, espanhol..."
    )

async def handle_message(update: Update, context):
    await update.message.reply_text("Recebi sua mensagem! Processando...")

def run_bot():
    print("Iniciando bot do Telegram...")
    if not BOT_TOKEN:
        print("ERRO: BOT_TOKEN não encontrado!")
        return
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    print("Bot started - polling...")
    application.run_polling(stop_signals=None, close_loop=False)

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    run_flask()
