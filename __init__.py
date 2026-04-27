# wallasAPI/__init__.py
"""
WallasAPI v3.0 — Universal Multi-Provider AI Router.
Features: Chat, TTS, Image/Video Gen, Google Integration, Projects, Reminders.
Powered by ProyectoIG.
"""
import os
from dotenv import load_dotenv

_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    load_dotenv(_env_path)

from .router import AIRouter
from .model_fetcher import update_registry_cache, update_registry_async
from .config import (
    MODELS_REGISTRY, PROVIDERS, PROVIDER_SPEED_PRIORITY, NON_CHAT_TYPES,
    TEXT, VISION, AUDIO, FILE, FILE_SHIM,
    REASONING, MOE, CODE, EMBEDDING, RERANK, TTS, FREE,
    IMAGE_GEN, VIDEO_GEN,
)
from .google_service import GoogleManager
from .projects import ProjectManager
from .reminders import ReminderManager

__all__ = [
    "AIRouter",
    "update_registry_cache", "update_registry_async",
    "MODELS_REGISTRY", "PROVIDERS", "PROVIDER_SPEED_PRIORITY", "NON_CHAT_TYPES",
    "TEXT", "VISION", "AUDIO", "FILE", "FILE_SHIM",
    "REASONING", "MOE", "CODE", "EMBEDDING", "RERANK", "TTS", "FREE",
    "IMAGE_GEN", "VIDEO_GEN",
    "GoogleManager", "ProjectManager", "ReminderManager",
]

