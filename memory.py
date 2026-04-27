# ai_services/memory.py
"""
Conversation memory management for the AI Router.
Persists chat history per thread using JSON files.
"""
import os
import json
import time

from .logger import log
from .settings import SettingsManager
import pytz
from datetime import datetime

CONTEXT_DIR = os.path.join(os.path.dirname(__file__), "temp_context")


class MemoryManager:
    """Manages conversation history for a given thread_id."""

    MAX_MESSAGES = 20  # Keep the last N messages to stay within free-tier token limits

    def __init__(self, thread_id: str):
        self.thread_id = thread_id
        self.file_path = os.path.join(CONTEXT_DIR, f"thread_{thread_id}.json")
        self.title = None
        os.makedirs(CONTEXT_DIR, exist_ok=True)

    def load_history(self) -> list:
        """Loads the full message history and metadata from disk."""
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.title = data.get("title")
                return data.get("messages", [])
        except (json.JSONDecodeError, IOError) as e:
            log.warning(f"Error leyendo historial de {self.thread_id}: {e}")
            return []

    def get_localized_timestamp(self) -> str:
        """Returns a formatted timestamp based on the user's configured timezone."""
        try:
            tz_str = SettingsManager.get_timezone()
            tz = pytz.timezone(tz_str)
            now = datetime.now(tz)
            return now.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def sync_to_obsidian(self, message_index: int = None, full_chat: bool = False):
        """
        Manually sync a message or the full chat to Obsidian.
        Triggered by user action (button).
        """
        try:
            vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
            if not vault_path or not os.path.exists(vault_path):
                log.warning("OBSIDIAN_VAULT_PATH no configurada o no encontrada.")
                return False
                
            chats_dir = os.path.join(vault_path, "Gravedad_Chats")
            os.makedirs(chats_dir, exist_ok=True)
            
            # Use smart title if available, otherwise fallback to ID
            history = self.load_history()
            title = self.title or f"Chat_{self.thread_id}"
            
            # Sanitize filename
            safe_title = "".join([c for c in title if c.isalnum() or c in (" ", "-", "_")]).strip()
            md_path = os.path.join(chats_dir, f"{safe_title}.md")
            
            with open(md_path, "a", encoding="utf-8") as f:
                # Stamp date/time inside
                timestamp = self.get_localized_timestamp()
                
                if not os.path.exists(md_path) or os.path.getsize(md_path) == 0:
                    f.write(f"# {title}\n\n")
                    f.write(f"*Sincronizado el: {timestamp}*\n---\n\n")

                if full_chat:
                    f.write(f"\n## --- SINCRONIZACIÓN COMPLETA ({timestamp}) ---\n\n")
                    for msg in history:
                        role = "👤 **Tú**" if msg["role"] == "user" else "🤖 **Gravedad AI**"
                        f.write(f"{role}\n{msg['content']}\n\n---\n")
                elif message_index is not None and 0 <= message_index < len(history):
                    msg = history[message_index]
                    role = "👤 **Tú**" if msg["role"] == "user" else "🤖 **Gravedad AI**"
                    f.write(f"### [Sincronizado: {timestamp}]\n")
                    f.write(f"{role}\n{msg['content']}\n\n---\n")
                
            return True
        except Exception as e:
            log.warning(f"Error backup Obsidian: {e}")
            return False

    def save_message(self, role: str, content: str):
        """Appends a message to the thread history. No longer truncates disk data."""
        history = self.load_history()
        history.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })

        # We keep everything on disk instead of trimming
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "messages": history, 
                        "last_updated": time.time(),
                        "title": self.title
                    },
                    f, ensure_ascii=False, indent=2
                )
        except IOError as e:
            log.error(f"Error guardando historial de {self.thread_id}: {e}")
            
        # Real-time backup REMOVED - now manual.

    def get_context_messages(self, limit: int = None) -> list:
        """
        Returns the last `limit` messages (or MAX_MESSAGES by default) 
        as a list of {role, content} dicts ready for API consumption.
        """
        history = self.load_history()
        if not history:
            return []
            
        max_context = limit if limit else self.MAX_MESSAGES
        recent = history[-max_context:]
        return [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in recent
        ]

    def clear(self):
        """Deletes the thread's history file."""
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
            log.info(f"Memoria de thread '{self.thread_id}' borrada.")

    @staticmethod
    def list_threads() -> list:
        """
        Scans temp_context directory and returns metadata for all saved threads.
        Returns a list of dicts with: thread_id, message_count, last_updated, preview.
        """
        threads = []
        if not os.path.exists(CONTEXT_DIR):
            return threads
        for filename in sorted(os.listdir(CONTEXT_DIR), reverse=True):
            if not filename.startswith("thread_") or not filename.endswith(".json"):
                continue
            thread_id = filename.replace("thread_", "").replace(".json", "")
            filepath = os.path.join(CONTEXT_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    messages = data.get("messages", [])
                    last_updated = data.get("last_updated", 0)
                    # Get first user message as preview
                    preview = ""
                    for msg in messages:
                        if msg.get("role") == "user":
                            preview = msg.get("content", "")[:80]
                            break
                    threads.append({
                        "thread_id": thread_id,
                        "title": data.get("title", "Chat sin título"),
                        "message_count": len(messages),
                        "last_updated": last_updated,
                        "preview": preview or "Chat vacío",
                        "filename": filename,
                    })
            except (json.JSONDecodeError, IOError):
                continue
        return threads

    @staticmethod
    def get_thread_messages(thread_id: str) -> list:
        """Load all messages from a specific thread for display."""
        filepath = os.path.join(CONTEXT_DIR, f"thread_{thread_id}.json")
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("messages", [])
        except (json.JSONDecodeError, IOError):
            return []
