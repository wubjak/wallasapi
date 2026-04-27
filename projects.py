# ai_services/projects.py
"""
Projects System — ChatGPT-style project management.
Each project has: name, instructions, files, color, icon, and a list of thread IDs.
Projects are stored as JSON files in ai_services/projects/.
"""
import os
import json
import time
import uuid
from typing import List, Dict, Any, Optional

from .logger import log

PROJECTS_DIR = os.path.join(os.path.dirname(__file__), "projects")
os.makedirs(PROJECTS_DIR, exist_ok=True)


class ProjectManager:
    """Manages project CRUD and thread association."""

    @staticmethod
    def _project_path(project_id: str) -> str:
        return os.path.join(PROJECTS_DIR, f"{project_id}.json")

    @staticmethod
    def list_projects() -> List[Dict[str, Any]]:
        """List all projects with metadata (without full file contents)."""
        projects = []
        for f in sorted(os.listdir(PROJECTS_DIR)):
            if f.endswith(".json"):
                try:
                    with open(os.path.join(PROJECTS_DIR, f), "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                        # Return summary only
                        projects.append({
                            "id": data.get("id"),
                            "name": data.get("name"),
                            "instructions": data.get("instructions", ""),
                            "color": data.get("color", "#3b82f6"),
                            "icon": data.get("icon", "📁"),
                            "thread_count": len(data.get("threads", [])),
                            "file_count": len(data.get("files", [])),
                            "created_at": data.get("created_at"),
                            "updated_at": data.get("updated_at"),
                        })
                except Exception as e:
                    log.warning(f"[PROJECTS] Error reading {f}: {e}")
        return projects

    @staticmethod
    def get_project(project_id: str) -> Optional[Dict[str, Any]]:
        """Get full project data including threads and file names."""
        path = ProjectManager._project_path(project_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.error(f"[PROJECTS] Error loading {project_id}: {e}")
            return None

    @staticmethod
    def create_project(
        name: str,
        instructions: str = "",
        color: str = "#3b82f6",
        icon: str = "📁",
    ) -> Dict[str, Any]:
        """Create a new project."""
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        now = time.time()
        project = {
            "id": project_id,
            "name": name,
            "instructions": instructions,
            "color": color,
            "icon": icon,
            "threads": [],
            "files": [],
            "created_at": now,
            "updated_at": now,
        }
        with open(ProjectManager._project_path(project_id), "w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=2)
        log.info(f"[PROJECTS] Created project: {name} ({project_id})")
        return project

    @staticmethod
    def update_project(project_id: str, updates: Dict[str, Any]) -> Optional[Dict]:
        """Update project fields (name, instructions, color, icon)."""
        project = ProjectManager.get_project(project_id)
        if not project:
            return None
        for key in ("name", "instructions", "color", "icon"):
            if key in updates:
                project[key] = updates[key]
        project["updated_at"] = time.time()
        with open(ProjectManager._project_path(project_id), "w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=2)
        return project

    @staticmethod
    def delete_project(project_id: str) -> bool:
        """Delete a project."""
        path = ProjectManager._project_path(project_id)
        if os.path.exists(path):
            os.remove(path)
            log.info(f"[PROJECTS] Deleted: {project_id}")
            return True
        return False

    @staticmethod
    def add_thread(project_id: str, thread_id: str) -> bool:
        """Associate a chat thread with a project."""
        project = ProjectManager.get_project(project_id)
        if not project:
            return False
        if thread_id not in project["threads"]:
            project["threads"].append(thread_id)
            project["updated_at"] = time.time()
            with open(ProjectManager._project_path(project_id), "w", encoding="utf-8") as f:
                json.dump(project, f, ensure_ascii=False, indent=2)
        return True

    @staticmethod
    def remove_thread(project_id: str, thread_id: str) -> bool:
        """Remove a thread from a project."""
        project = ProjectManager.get_project(project_id)
        if not project:
            return False
        if thread_id in project["threads"]:
            project["threads"].remove(thread_id)
            project["updated_at"] = time.time()
            with open(ProjectManager._project_path(project_id), "w", encoding="utf-8") as f:
                json.dump(project, f, ensure_ascii=False, indent=2)
        return True

    @staticmethod
    def add_file_reference(project_id: str, file_name: str, file_data_b64: str, mime_type: str) -> bool:
        """Store a file reference in the project (keeps base64 data for reuse)."""
        project = ProjectManager.get_project(project_id)
        if not project:
            return False
        project["files"].append({
            "name": file_name,
            "data": file_data_b64,
            "mime_type": mime_type,
            "added_at": time.time(),
        })
        project["updated_at"] = time.time()
        with open(ProjectManager._project_path(project_id), "w", encoding="utf-8") as f:
            json.dump(project, f, ensure_ascii=False, indent=2)
        return True
