import os
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
print(f"BOT_TOKEN existe? {bool(BOT_TOKEN)}", flush=True)

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

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    print(f"Iniciando Flask na porta {port}", flush=True)
    # use_reloader=False é fundamental para não duplicar threads no Flask
    app.run(host="0.0.0.0", port=port, use_reloader=False)

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("ERRO: BOT_TOKEN não encontrado!", flush=True)
        exit(1)

    # Inicia o Flask em uma thread separada em segundo plano
    threading.Thread(target=run_flask, daemon=True).start()

    # Executa o Bot na thread principal (onde os sinais e o event loop funcionam perfeitamente)
    print("Iniciando bot do Telegram...", flush=True)
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    
    print("Bot rodando - polling...", flush=True)
    application.run_polling(drop_pending_updates=True)
