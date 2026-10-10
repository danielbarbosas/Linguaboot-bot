import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

BOT_TOKEN = os.getenv("BOT_TOKEN")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
@app.route('/')
def home():
    return "LinguaBoot Bot Online 24h!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧑 Adulto - Viagem/Trabalho", callback_data='adulto')],
        [InlineKeyboardButton("👶 Criança - Inglês Divertido", callback_data='crianca')]
    ]
    await update.message.reply_text("Bem-vindo ao LinguaBoot! Escolha o modo:", reply_markup=InlineKeyboardMarkup(keyboard))

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'adulto':
        context.user_data['modo'] = 'adulto'
        await query.edit_message_text("Modo ADULTO ativado! ✈️ Me diga o que quer aprender (ex: pedir comida no aeroporto)")
    else:
        context.user_data['modo'] = 'crianca'
        await query.edit_message_text("Modo CRIANÇA ativado! 🎈 Vamos aprender brincando! Me diga um tema (ex: animais)")

async def responder_ia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    modo = context.user_data.get('modo', 'adulto')
    texto = update.message.text
    if modo == 'adulto':
        prompt = f"Aja como professor de inglês para adulto viajando. Usuário disse: {texto}. Dê tradução, pronúncia simples e 2 frases úteis. Seja curto."
    else:
        prompt = f"Aja como professor divertido para criança de 7 anos. Tema: {texto}. Use emojis, palavras simples em inglês, e faça um mini-jogo. Seja curto e alegre."
    try:
        resp = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role":"user","content":prompt}])
        await update.message.reply_text(resp.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"Vamos praticar '{texto}' em inglês! Como você diria isso?")

def main_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(menu_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_ia))
    application.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    main_bot()
