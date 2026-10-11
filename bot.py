import os
import io
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = Flask(__name__)

user_sessions = {}

def get_user_data(user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "idioma": "Inglês",
            "nivel": "Iniciante",
            "publico": "Adulto",
            "voz": "nova",
            "modo": "conversa",
            "historico": []
        }
    return user_sessions[user_id]

@app.route('/')
def home():
    return "LinguaBoot Bot Online 24h!"

# --- MENU INTERATIVO ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user_data(user_id)
    
    mensagem = (
        f"Olá! Eu sou o LinguaBoot 🤖📚\n\n"
        f"Seu tutor de idiomas interativo!\n\n"
        f"⚙️ Sua Configuração Atual:\n"
        f"• Público: {data['publico']}\n"
        f"• Idioma: {data['idioma']}\n"
        f"• Nível: {data['nivel']}\n"
        f"• Voz: {'Feminina' if data['voz'] == 'nova' else 'Masculina'}\n"
        f"• Modo: {data['modo'].capitalize()}\n\n"
        f"Escolha uma opção abaixo para ajustar o bot ou começar a praticar!"
    )

    keyboard = [
        [InlineKeyboardButton("🗣️ Modo Conversa Livre", callback_data="set_modo_conversa")],
        [
            InlineKeyboardButton("✍️ Teste Escrito", callback_data="set_modo_teste_escrita"),
            InlineKeyboardButton("🎙️ Teste Pronúncia", callback_data="set_modo_teste_pronuncia")
        ],
        [
            InlineKeyboardButton("🌐 Idioma", callback_data="menu_idioma"),
            InlineKeyboardButton("📊 Nível", callback_data="menu_nivel")
        ],
        [
            InlineKeyboardButton("👨‍👩‍👧 Público (Kids/Adulto)", callback_data="menu_publico"),
            InlineKeyboardButton("🎙️ Tipo de Voz", callback_data="menu_voz")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(mensagem, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(mensagem, reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = get_user_data(user_id)
    
    cb = query.data

    if cb.startswith("set_modo_"):
        modo_limpo = cb.replace("set_modo_", "")
        data["modo"] = modo_limpo
        await query.edit_message_text(f"✅ Modo alterado para {modo_limpo.capitalize()}!\nPode mandar uma mensagem de texto ou áudio para começarmos.")
        return

    if cb == "menu_idioma":
        keyboard = [
            [InlineKeyboardButton("🇺🇸 Inglês", callback_data="set_idioma_Inglês"), InlineKeyboardButton("🇪🇸 Espanhol", callback_data="set_idioma_Espanhol")],
            [InlineKeyboardButton("🇫🇷 Francês", callback_data="set_idioma_Francês"), InlineKeyboardButton("🇮🇹 Italiano", callback_data="set_idioma_Italiano")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="voltar_menu")]
        ]
        await query.edit_message_text("Escolha o idioma que deseja praticar:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if cb == "menu_nivel":
        keyboard = [
            [InlineKeyboardButton("Iniciante (A1-A2)", callback_data="set_nivel_Iniciante")],
            [InlineKeyboardButton("Intermediário (B1-B2)", callback_data="set_nivel_Intermediário")],
            [InlineKeyboardButton("Avançado (C1-C2)", callback_data="set_nivel_Avançado")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="voltar_menu")]
        ]
        await query.edit_message_text("Escolha seu nível de conhecimento:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if cb == "menu_publico":
        keyboard = [
            [InlineKeyboardButton("👤 Adulto", callback_data="set_publico_Adulto")],
            [InlineKeyboardButton("👧 Modo Kids (Crianças)", callback_data="set_publico_Kids")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="voltar_menu")]
        ]
        await query.edit_message_text("Selecione o perfil de aprendizado:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if cb == "menu_voz":
        keyboard = [
            [InlineKeyboardButton("👩 Feminina (Nova)", callback_data="set_voz_nova")],
            [InlineKeyboardButton("👨 Masculina (Onyx)", callback_data="set_voz_onyx")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="voltar_menu")]
        ]
        await query.edit_message_text("Escolha a voz do seu tutor:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if cb.startswith("set_idioma_"):
        data["idioma"] = cb.replace("set_idioma_", "")
    elif cb.startswith("set_nivel_"):
        data["nivel"] = cb.replace("set_nivel_", "")
    elif cb.startswith("set_publico_"):
        data["publico"] = cb.replace("set_publico_", "")
    elif cb.startswith("set_voz_"):
        data["voz"] = cb.replace("set_voz_", "")

    await start(update, context)

# --- PROCESSAMENTO DE MENSAGENS E ÁUDIOS ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user_data(user_id)
    
    texto_usuario = ""

    if update.message.voice or update.message.audio:
        await update.message.reply_text("🎙️ Ouvindo seu áudio...")
        
        try:
            file_id = (update.message.voice or update.message.audio).file_id
            new_file = await context.bot.get_file(file_id)
            
            audio_bytes = await new_file.download_as_bytearray()
            audio_buffer = io.BytesIO(audio_bytes)
            audio_buffer.name = "audio.ogg"

            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_buffer
            )
            texto_usuario = transcript.text
            await update.message.reply_text(f"📝 Entendi: \"{texto_usuario}\"")

        except Exception as e:
            print(f"ERRO NO WHISPER: {e}", flush=True)
            await update.message.reply_text("Ocorreu um erro ao processar o áudio. Verifique se sua conta da OpenAI possui saldo de créditos ativo.")
            return
    else:
        texto_usuario = update.message.text

    system_prompt = (
        f"Você é o LinguaBoot, um tutor de idiomas especialista.\n"
        f"• Idioma das aulas: {data['idioma']}\n"
        f"• Nível do aluno: {data['nivel']}\n"
        f"• Público: {data['publico']}\n"
        f"• Modo atual: {data['modo']}\n\n"
    )

    if data["publico"] == "Kids":
        system_prompt += "Mantenha o tom extremamente lúdico, amigável, divertido, use bastantes emojis e frases curtas e simples adequadas para crianças. Restrição total a temas adultos ou complexos.\n"
    
    if data["modo"] == "conversa":
        system_prompt += (
            f"Converse naturally sobre qualquer assunto no idioma {data['idioma']}. "
            "Ao final da sua resposta, se o aluno cometeu algum erro de gramática ou vocabulário, "
            "adicione uma seção '💡 Dica do Professor:' corrigindo com gentileza em português."
        )
    elif data["modo"] == "teste_escrita":
        system_prompt += (
            f"Você está aplicando um teste de escrita em {data['idioma']}. Avalie o texto do aluno, "
            "dê uma nota de 0 a 10, explique onde ele errou e envie uma nova pergunta para continuar o teste."
        )
    elif data["modo"] == "teste_pronuncia":
        system_prompt += (
            f"Você está avaliando a pronúncia/estrutura do áudio do aluno em {data['idioma']}. "
            "Avalie a clareza da frase enviada, aponte palavras a melhorar e passe uma nova frase no idioma para ele repetir."
        )

    data["historico"].append({"role": "user", "content": texto_usuario})
    if len(data["historico"]) > 6:
        data["historico"] = data["historico"][-6:]

    messages = [{"role": "system", "content": system_prompt}] + data["historico"]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        resposta_ia = response.choices[0].message.content
        data["historico"].append({"role": "assistant", "content": resposta_ia})

        await update.message.reply_text(resposta_ia)

        audio_response = client.audio.speech.create(
            model="tts-1",
            voice=data["voz"],
            input=resposta_ia
        )
        
        speech_buffer = io.BytesIO(audio_response.content)
        speech_buffer.name = "response.mp3"

        await update.message.reply_voice(voice=speech_buffer)

    except Exception as e:
        print(f"ERRO NA RESPOSTA DA IA/TTS: {e}", flush=True)
        await update.message.reply_text("Ocorreu um erro ao gerar a resposta da IA.")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("ERRO: BOT_TOKEN não encontrado!", flush=True)
        exit(1)

    threading.Thread(target=run_flask, daemon=True).start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.ALL, handle_message))

    print("LinguaBoot rodando com sucesso!", flush=True)
    application.run_polling(drop_pending_updates=True)
