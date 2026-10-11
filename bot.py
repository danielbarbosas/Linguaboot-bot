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
import google.generativeai as genai
import edge_tts

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = Flask(__name__)

user_sessions = {}

def get_user_data(user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "idioma": "Inglês",
            "nivel": "Iniciante",
            "publico": "Adulto",
            "voz": "en-US-AriaNeural",
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
        f"Seu tutor de idiomas interativo (100% Gratuito)!\n\n"
        f"⚙️ Sua Configuração Atual:\n"
        f"• Público: {data['publico']}\n"
        f"• Idioma: {data['idioma']}\n"
        f"• Nível: {data['nivel']}\n"
        f"• Voz: {'Feminina' if 'Aria' in data['voz'] or 'Elvira' in data['voz'] or 'Denise' in data['voz'] or 'Elsa' in data['voz'] else 'Masculina'}\n"
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
            [InlineKeyboardButton("👩 Feminina", callback_data="set_voz_fem")],
            [InlineKeyboardButton("👨 Masculina", callback_data="set_voz_masc")],
            [InlineKeyboardButton("⬅️ Voltar", callback_data="voltar_menu")]
        ]
        await query.edit_message_text("Escolha a voz do seu tutor:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if cb.startswith("set_idioma_"):
        data["idioma"] = cb.replace("set_idioma_", "")
        # Ajusta voz padrão para o idioma selecionado
        if data["idioma"] == "Inglês":
            data["voz"] = "en-US-AriaNeural"
        elif data["idioma"] == "Espanhol":
            data["voz"] = "es-ES-ElviraNeural"
        elif data["idioma"] == "Francês":
            data["voz"] = "fr-FR-DeniseNeural"
        elif data["idioma"] == "Italiano":
            data["voz"] = "it-IT-ElsaNeural"

    elif cb.startswith("set_nivel_"):
        data["nivel"] = cb.replace("set_nivel_", "")
    elif cb.startswith("set_publico_"):
        data["publico"] = cb.replace("set_publico_", "")
    elif cb == "set_voz_fem":
        voices = {"Inglês": "en-US-AriaNeural", "Espanhol": "es-ES-ElviraNeural", "Francês": "fr-FR-DeniseNeural", "Italiano": "it-IT-ElsaNeural"}
        data["voz"] = voices.get(data["idioma"], "en-US-AriaNeural")
    elif cb == "set_voz_masc":
        voices = {"Inglês": "en-US-GuyNeural", "Espanhol": "es-ES-AlvaroNeural", "Francês": "fr-FR-HenriNeural", "Italiano": "it-IT-DiegoNeural"}
        data["voz"] = voices.get(data["idioma"], "en-US-GuyNeural")

    await start(update, context)

# --- PROCESSAMENTO DE MENSAGENS E ÁUDIOS ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_user_data(user_id)
    
    contents = []

    if update.message.voice or update.message.audio:
        await update.message.reply_text("🎙️ Ouvindo seu áudio...")
        
        try:
            file_id = (update.message.voice or update.message.audio).file_id
            new_file = await context.bot.get_file(file_id)
            audio_bytes = await new_file.download_as_bytearray()
            
            # Formato esperado pela biblioteca google-generativeai
            contents.append({
                "mime_type": "audio/ogg",
                "data": bytes(audio_bytes)
            })
            contents.append("Transcreva exatamente o áudio enviado pelo aluno e responda em seguida mantendo o papel de professor de idiomas.")
        except Exception as e:
            print(f"ERRO AO PROCESSAR ÁUDIO: {e}", flush=True)
            await update.message.reply_text("Erro ao carregar o áudio. Tente novamente!")
            return
    else:
        contents.append(update.message.text)

    system_prompt = (
        f"Você é o LinguaBoot, um tutor de idiomas especialista.\n"
        f"• Idioma das aulas: {data['idioma']}\n"
        f"• Nível do aluno: {data['nivel']}\n"
        f"• Público: {data['publico']}\n"
        f"• Modo atual: {data['modo']}\n\n"
    )

    if data["publico"] == "Kids":
        system_prompt += "Mantenha o tom extremamente lúdico, amigável, divertido, use bastantes emojis e frases curtas e simples adequadas para crianças.\n"
    
    if data["modo"] == "conversa":
        system_prompt += (
            f"Converse naturalmente sobre qualquer assunto no idioma {data['idioma']}. "
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
            "Se for enviado áudio, transcreva o que entendeu, avalie a clareza e passe uma nova frase no idioma para ele repetir."
        )

    try:
        # Modelo oficial estável do Gemini
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_prompt
        )
        
        response = model.generate_content(contents)
        resposta_ia = response.text

        await update.message.reply_text(resposta_ia)

        # Geração de áudio com edge-tts (vozes neurais hiper-realistas e gratuitas)
        communicate = edge_tts.Communicate(resposta_ia, data["voz"])
        speech_bytes = bytearray()
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                speech_bytes.extend(chunk["data"])

        speech_buffer = io.BytesIO(speech_bytes)
        speech_buffer.name = "response.mp3"

        await update.message.reply_voice(voice=speech_buffer)

    except Exception as e:
        print(f"ERRO GEMINI/TTS: {e}", flush=True)
        await update.message.reply_text(f"Ocorreu um erro no processamento: {e}")

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

    print("LinguaBoot (Gemini + EdgeTTS) rodando com sucesso!", flush=True)
    application.run_polling(drop_pending_updates=True)
