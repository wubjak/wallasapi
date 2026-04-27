# ai_services/reminders.py
"""
Reminders System — Local task/reminder storage with optional Google Calendar sync.
Supports creating, listing, updating, and deleting reminders.
"""
import os
import json
import time
import uuid
from typing import List, Dict, Any, Optional

from .logger import log
from .settings import SettingsManager

REMINDERS_FILE = os.path.join(os.path.dirname(__file__), "reminders.json")


class ReminderManager:
    """Manages local reminders with optional calendar sync."""

    @staticmethod
    def _load_all() -> List[Dict[str, Any]]:
        if not os.path.exists(REMINDERS_FILE):
            return []
        try:
            with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    @staticmethod
    def _save_all(reminders: List[Dict]):
        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(reminders, f, ensure_ascii=False, indent=2)

    @staticmethod
    def list_reminders(include_completed: bool = False) -> List[Dict[str, Any]]:
        """List all reminders, optionally including completed ones."""
        reminders = ReminderManager._load_all()
        if not include_completed:
            reminders = [r for r in reminders if not r.get("completed", False)]
        return sorted(reminders, key=lambda r: r.get("due_date", "9999"))

    @staticmethod
    def create_reminder(
        title: str,
        description: str = "",
        due_date: str = "",
        priority: str = "normal",
        category: str = "general",
        sync_calendar: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a new reminder.
        due_date: ISO format string, e.g. '2026-04-15T10:00:00-05:00'
        priority: 'low', 'normal', 'high', 'urgent'
        """
        reminders = ReminderManager._load_all()
        reminder = {
            "id": f"rem_{uuid.uuid4().hex[:12]}",
            "title": title,
            "description": description,
            "due_date": due_date,
            "priority": priority,
            "category": category,
            "completed": False,
            "notified": False,
            "calendar_event_id": None,
            "created_at": time.time(),
            "updated_at": time.time(),
        }

        # Optional Google Calendar sync
        if sync_calendar and due_date:
            try:
                from .google_service import GoogleManager
                gm = GoogleManager()
                if gm.is_authenticated:
                    import datetime as dt
                    # Create a 30-min event from the due date
                    start = due_date
                    # Parse and add 30 min for end time
                    try:
                        from datetime import datetime, timedelta
                        dt_start = datetime.fromisoformat(start)
                        dt_end = dt_start + timedelta(minutes=30)
                        end = dt_end.isoformat()
                    except Exception:
                        end = start  # Fallback
                    event = gm.calendar_create_event(
                        summary=f"🔔 {title}",
                        start=start,
                        end=end,
                        description=description,
                    )
                    if event:
                        reminder["calendar_event_id"] = event.get("id")
                        log.info(f"[REMINDERS] Synced to Calendar: {event.get('link')}")
            except Exception as e:
                log.warning(f"[REMINDERS] Calendar sync failed: {e}")

        reminders.append(reminder)
        ReminderManager._save_all(reminders)
        log.info(f"[REMINDERS] Created: {title}")
        return reminder

    @staticmethod
    def update_reminder(reminder_id: str, updates: Dict[str, Any]) -> Optional[Dict]:
        """Update a reminder's fields."""
        reminders = ReminderManager._load_all()
        for i, r in enumerate(reminders):
            if r["id"] == reminder_id:
                for key in ("title", "description", "due_date", "priority", "category", "completed", "notified"):
                    if key in updates:
                        reminders[i][key] = updates[key]
                reminders[i]["updated_at"] = time.time()
                ReminderManager._save_all(reminders)
                return reminders[i]
        return None

    @staticmethod
    def complete_reminder(reminder_id: str) -> Optional[Dict]:
        """Mark a reminder as completed."""
        return ReminderManager.update_reminder(reminder_id, {"completed": True})

    @staticmethod
    def delete_reminder(reminder_id: str) -> bool:
        """Delete a reminder by ID."""
        reminders = ReminderManager._load_all()
        original_len = len(reminders)
        reminders = [r for r in reminders if r["id"] != reminder_id]
        if len(reminders) < original_len:
            ReminderManager._save_all(reminders)
            log.info(f"[REMINDERS] Deleted: {reminder_id}")
            return True
        return False

    def get_due_reminders() -> List[Dict]:
        """Get reminders that are due (past due_date, not completed, and not yet notified)."""
        import datetime
        import pytz
        
        tz_name = SettingsManager.get_timezone()
        try:
            tz = pytz.timezone(tz_name)
        except Exception:
            tz = pytz.UTC
            
        now = datetime.datetime.now(tz)
        reminders = ReminderManager._load_all()
        due = []
        updated = False
        
        for r in reminders:
            if not r.get("completed") and not r.get("notified") and r.get("due_date"):
                try:
                    # Parse due_date (ISO)
                    r_due = datetime.datetime.fromisoformat(r["due_date"])
                    # Ensure it has timezone info for comparison
                    if r_due.tzinfo is None:
                        r_due = tz.localize(r_due)
                    
                    if r_due <= now:
                        due.append(r)
                        r["notified"] = True
                        updated = True
                except Exception as e:
                    log.error(f"[REMINDERS] Error comparing time: {e}")
                    
        if updated:
            ReminderManager._save_all(reminders)
            
        return due
