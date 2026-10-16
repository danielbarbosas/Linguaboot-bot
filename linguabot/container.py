"""Contêiner de serviços e fábrica de dependências."""

from __future__ import annotations

from dataclasses import dataclass

from .config import Settings
from .content.languages import get_language
from .models import UserProfileData
from .services.images import ImageService, build_image_service
from .services.llm import LLMClient, build_llm
from .services.stt import STTClient, build_stt
from .services.tts import SpeechService, build_speech
from .services.tutor import TutorService
from .storage.repository import Storage


@dataclass
class Services:
    """Recursos compartilhados, disponíveis em ``context.bot_data['services']``."""

    settings: Settings
    storage: Storage
    llm: LLMClient
    speech: SpeechService
    stt: STTClient
    images_adult: ImageService
    images_kids: ImageService

    def tutor_for(self, profile: UserProfileData) -> TutorService:
        name = "inglês"
        if profile.learn_lang is not None:
            name = get_language(profile.learn_lang).name_pt.lower()
        return TutorService(self.llm, learn_lang_name=name)


def build_services(settings: Settings) -> Services:
    """Monta todos os serviços a partir da configuração."""

    cache_dir = "./data/cache/images"
    return Services(
        settings=settings,
        storage=Storage(settings.database_path),
        llm=build_llm(settings),
        speech=build_speech(settings),
        stt=build_stt(settings),
        images_adult=build_image_service(settings.assets_dir, cache_dir, allow_external=True),
        images_kids=build_image_service(settings.assets_dir, cache_dir, allow_external=False),
    )
