import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

@app.route('/')
def home():
    return "LinguaBoot Bot Online 24h!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Eu sou o LinguaBoot 🤖📚\n\n"
        "Seu professor de idiomas!\n"
        "Me manda um áudio em inglês, espanhol, francês... que eu corrijo na hora!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Recebi! Em breve vou corrigir áudios também. Por enquanto, manda texto que a gente pratica!")

def run_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    run_flask()
