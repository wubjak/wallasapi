# ai_services/settings.py
"""
Settings Manager — Handles user preferences like Timezone, Theme, etc.
"""
import os
import json
from .logger import log

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

class SettingsManager:
    @staticmethod
    def load_settings():
        if not os.path.exists(SETTINGS_FILE):
            # Default settings
            return {
                "timezone": "UTC",
                "username": "User",
                "notifications_enabled": True,
                "sound_enabled": True
            }
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.error(f"[SETTINGS] Load error: {e}")
            return {"timezone": "UTC"}

    @staticmethod
    def save_settings(settings):
        try:
            current = SettingsManager.load_settings()
            current.update(settings)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(current, f, ensure_ascii=False, indent=2)
            log.info("[SETTINGS] Saved successfully.")
            return True
        except Exception as e:
            log.error(f"[SETTINGS] Save error: {e}")
            return False

    @staticmethod
    def get_timezone():
        return SettingsManager.load_settings().get("timezone", "UTC")
