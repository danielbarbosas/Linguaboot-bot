"""Objetos falsos para testar os handlers sem acessar o Telegram de verdade."""

from __future__ import annotations

import wave
from pathlib import Path
from typing import Any

from linguabot.models import Voice


class FakeUser:
    def __init__(self, user_id: int, first_name: str = "Teste", username: str = "teste"):
        self.id = user_id
        self.first_name = first_name
        self.username = username


class FakeFile:
    def __init__(self, data: bytes = b"\x00\x00") -> None:
        self.data = data

    async def download_to_drive(self, destination: str) -> None:
        Path(destination).write_bytes(self.data)


class FakeMessage:
    def __init__(self, bot: "FakeBot", chat_id: int, text: str | None = None, media=None):
        self.bot = bot
        self.chat_id = chat_id
        self.text = text
        self.voice = media
        self.audio = None
        self.video_note = None

    async def reply_text(self, text: str, reply_markup: Any = None, **kwargs) -> "FakeMessage":
        await self.bot.send_message(self.chat_id, text, reply_markup=reply_markup)
        return self


class FakeCallbackQuery:
    def __init__(self, data: str, user: FakeUser, message: FakeMessage):
        self.data = data
        self.from_user = user
        self.message = message
        self.answers: list[str | None] = []
        self.edits: list[str] = []

    async def answer(self, text: str | None = None) -> None:
        self.answers.append(text)

    async def edit_message_text(self, text: str, reply_markup: Any = None, **kwargs) -> None:
        self.edits.append(text)


class FakeVoice:
    def __init__(self, file_id: str = "voice-file"):
        self.file_id = file_id


class FakeBot:
    def __init__(self) -> None:
        self.messages: list[tuple[int, str]] = []
        self.voices: list[str] = []
        self.audios: list[str] = []
        self.photos: list[str] = []
        self.commands: list[Any] = []

    async def send_message(self, chat_id: int, text: str, reply_markup: Any = None, **kwargs):
        self.messages.append((chat_id, text))
        return FakeMessage(self, chat_id, text=text)

    async def send_voice(self, chat_id: int, voice, caption: str | None = None, **kwargs):
        voice.read()
        self.voices.append(caption or "")
        return FakeMessage(self, chat_id)

    async def send_audio(self, chat_id: int, audio, caption: str | None = None, **kwargs):
        audio.read()
        self.audios.append(caption or "")
        return FakeMessage(self, chat_id)

    async def send_photo(self, chat_id: int, photo, caption: str | None = None, reply_markup=None, **kwargs):
        photo.read()
        self.photos.append(caption or "")
        return FakeMessage(self, chat_id)

    async def get_file(self, file_id: str) -> FakeFile:
        return FakeFile()

    async def set_my_commands(self, commands) -> None:
        self.commands = list(commands)


class FakeUpdate:
    def __init__(self, *, message: FakeMessage | None = None, callback_query: FakeCallbackQuery | None = None, user: FakeUser | None = None):
        self.message = message
        self.callback_query = callback_query
        self.effective_user = user or (callback_query.from_user if callback_query else None)


class FakeContext:
    def __init__(self, services) -> None:
        self.bot = FakeBot()
        self.bot_data = {"services": services}
        self.user_data: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Fakes de serviços
# ---------------------------------------------------------------------------
class FakeLLM:
    name = "fake"

    def __init__(self, response: str | None = None, available: bool = True):
        self.response = response
        self._available = available
        self.prompts: list[str] = []

    @property
    def available(self) -> bool:
        return self._available

    def generate(self, prompt: str, system: str | None = None) -> str | None:
        self.prompts.append(prompt)
        return self.response


class FakeSTT:
    name = "fake"

    def __init__(self, transcript: str | None = "dog", available: bool = True):
        self.transcript = transcript
        self._available = available
        self.calls: list[tuple[str, str]] = []

    @property
    def available(self) -> bool:
        return self._available

    def transcribe(self, audio_path: str, lang: str) -> str | None:
        self.calls.append((audio_path, lang))
        return self.transcript


class FakeTTSEngine:
    name = "fake"
    supports_gender = True

    def __init__(self, fail: bool = False):
        self.fail = fail
        self.calls: list[tuple[str, str, Voice]] = []

    async def synthesize(self, text: str, lang: str, voice: Voice, out_path: str) -> str:
        self.calls.append((text, lang, voice))
        if self.fail:
            raise RuntimeError("tts falhou")
        _write_silence_wav(out_path)
        return out_path


def _write_silence_wav(path: str, seconds: float = 0.1) -> None:
    frames = int(16000 * seconds)
    with wave.open(path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * frames)


def make_photo_file(tmp_path: Path, name: str = "pic.jpg") -> Path:
    # JPEG mínimo válido (1x1) para testes de imagem de asset local.
    data = bytes.fromhex(
        "ffd8ffe000104a46494600010100000100010000ffdb004300"
        "0806060706050807070709090a0d100e0d0c0c0c14"
        "1f151016211f2325232022242b2f3a312b2f3a2c22243034"
        "34343434343434343434343434343434343434343434343434"
        "ffc0000b080001000101011100ffc4001f00000105010101"
        "010101000000000000000102030405060708090a0b"
        "ffda0008010100003f00d2cf20ffd9"
    )
    path = tmp_path / name
    path.write_bytes(data)
    return path


# ---------------------------------------------------------------------------
# Atalhos para montar updates nos testes
# ---------------------------------------------------------------------------
def callback_update(data: str, user: FakeUser, context: FakeContext) -> FakeUpdate:
    message = FakeMessage(context.bot, user.id)
    query = FakeCallbackQuery(data, user, message)
    return FakeUpdate(callback_query=query, user=user)


def text_update(text: str, user: FakeUser, context: FakeContext) -> FakeUpdate:
    message = FakeMessage(context.bot, user.id, text=text)
    return FakeUpdate(message=message, user=user)


def voice_update(user: FakeUser, context: FakeContext, media=None) -> FakeUpdate:
    message = FakeMessage(context.bot, user.id, media=media or FakeVoice())
    return FakeUpdate(message=message, user=user)
