# ai_services/google_service.py
"""
Google Account Integration — OAuth2 flow + Drive, Calendar, Gmail APIs.
Handles token persistence and provides a clean interface for the Playground.
"""
import os
import json
import datetime
from typing import List, Dict, Any, Optional

from .logger import log

# Google API libraries
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    HAS_GOOGLE_API = True
except ImportError:
    HAS_GOOGLE_API = False
    log.warning("[GOOGLE] google-api-python-client / google-auth-oauthlib not installed.")

# Paths
_BASE_DIR = os.path.dirname(__file__)
TOKEN_PATH = os.path.join(_BASE_DIR, "google_token.json")
CREDENTIALS_PATH = os.path.join(_BASE_DIR, "credentials.json")

# Scopes for Drive, Calendar, Gmail
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]


class GoogleManager:
    """Manages Google OAuth2 and API interactions."""

    def __init__(self):
        self.creds: Optional[Credentials] = None
        self._load_token()

    def _load_token(self):
        """Load cached token from disk."""
        if not HAS_GOOGLE_API:
            return
        if os.path.exists(TOKEN_PATH):
            try:
                self.creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    try:
                        self.creds.refresh(Request())
                        self._save_token()
                        log.info("[GOOGLE] Token refreshed.")
                    except Exception as e:
                        log.warning(f"[GOOGLE] Token refresh failed: {e}")
                        self.creds = None
            except Exception as e:
                log.warning(f"[GOOGLE] Error loading token: {e}")
                self.creds = None

    def _save_token(self):
        """Persist token to disk."""
        if self.creds:
            with open(TOKEN_PATH, "w") as f:
                f.write(self.creds.to_json())

    @property
    def is_authenticated(self) -> bool:
        return self.creds is not None and self.creds.valid

    def get_auth_url(self, redirect_uri: str = "http://127.0.0.1:5000/google/callback") -> Optional[str]:
        """Generate Google OAuth2 authorization URL."""
        if not HAS_GOOGLE_API:
            return None
        if not os.path.exists(CREDENTIALS_PATH):
            log.error(f"[GOOGLE] credentials.json not found at {CREDENTIALS_PATH}")
            return None
        try:
            flow = Flow.from_client_secrets_file(
                CREDENTIALS_PATH, scopes=SCOPES, redirect_uri=redirect_uri
            )
            auth_url, _ = flow.authorization_url(
                access_type="offline", include_granted_scopes="true", prompt="consent"
            )
            return auth_url
        except Exception as e:
            log.error(f"[GOOGLE] Auth URL error: {e}")
            return None

    def handle_callback(self, auth_code: str, redirect_uri: str = "http://127.0.0.1:5000/google/callback") -> bool:
        """Exchange authorization code for credentials."""
        if not HAS_GOOGLE_API:
            return False
        try:
            flow = Flow.from_client_secrets_file(
                CREDENTIALS_PATH, scopes=SCOPES, redirect_uri=redirect_uri
            )
            flow.fetch_token(code=auth_code)
            self.creds = flow.credentials
            self._save_token()
            log.info("[GOOGLE] Successfully authenticated!")
            return True
        except Exception as e:
            log.error(f"[GOOGLE] Callback error: {e}")
            return False

    def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user's profile info."""
        if not self.is_authenticated:
            return {}
        try:
            from googleapiclient.discovery import build
            service = build("oauth2", "v2", credentials=self.creds, static_discovery=False)
            user_info = service.userinfo().get().execute()
            return {
                "email": user_info.get("email", ""),
                "name": user_info.get("name", ""),
                "picture": user_info.get("picture", ""),
            }
        except Exception as e:
            log.error(f"[GOOGLE] User info error: {e}")
            return {}

    def logout(self):
        """Remove stored credentials."""
        self.creds = None
        if os.path.exists(TOKEN_PATH):
            os.remove(TOKEN_PATH)
        log.info("[GOOGLE] Logged out.")

    # ========================================================================
    # Google Drive
    # ========================================================================

    def drive_list_files(self, max_results: int = 20) -> List[Dict]:
        """List recent files from Google Drive."""
        if not self.is_authenticated:
            return []
        try:
            from googleapiclient.discovery import build
            service = build("drive", "v3", credentials=self.creds, static_discovery=False)
            results = service.files().list(
                pageSize=max_results,
                fields="files(id, name, mimeType, modifiedTime, webViewLink)",
                orderBy="modifiedTime desc",
            ).execute()
            return results.get("files", [])
        except Exception as e:
            log.error(f"[DRIVE] List error: {e}")
            return []

    def drive_upload_file(self, file_path: str, mime_type: str = None) -> Optional[Dict]:
        """Upload a file to Google Drive."""
        if not self.is_authenticated:
            return None
        try:
            from googleapiclient.discovery import build
            service = build("drive", "v3", credentials=self.creds, static_discovery=False)
            file_metadata = {"name": os.path.basename(file_path)}
            media = MediaFileUpload(file_path, mimetype=mime_type)
            uploaded = service.files().create(
                body=file_metadata, media_body=media, fields="id, name, webViewLink"
            ).execute()
            log.info(f"[DRIVE] Uploaded: {uploaded.get('name')}")
            return uploaded
        except Exception as e:
            log.error(f"[DRIVE] Upload error: {e}")
            return None

    # ========================================================================
    # Google Calendar
    # ========================================================================

    def calendar_list_events(self, max_results: int = 10) -> List[Dict]:
        """List upcoming events from Google Calendar."""
        if not self.is_authenticated:
            return []
        try:
            import datetime
            from googleapiclient.discovery import build
            service = build("calendar", "v3", credentials=self.creds, static_discovery=False)
            now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "") + "Z"
            events_result = service.events().list(
                calendarId="primary", timeMin=now,
                maxResults=max_results, singleEvents=True,
                orderBy="startTime"
            ).execute()
            events = events_result.get("items", [])
            return [
                {
                    "id": e.get("id"),
                    "summary": e.get("summary", "Sin título"),
                    "start": e.get("start", {}).get("dateTime", e.get("start", {}).get("date", "")),
                    "end": e.get("end", {}).get("dateTime", e.get("end", {}).get("date", "")),
                    "link": e.get("htmlLink", ""),
                }
                for e in events
            ]
        except Exception as e:
            log.error(f"[CALENDAR] List error: {e}")
            return []

    def calendar_create_event(
        self, summary: str, start: str, end: str,
        description: str = "", location: str = ""
    ) -> Optional[Dict]:
        """
        Create a calendar event.
        start/end should be ISO format with timezone, e.g. '2026-04-15T10:00:00-05:00'
        """
        if not self.is_authenticated:
            return None
        try:
            from googleapiclient.discovery import build
            service = build("calendar", "v3", credentials=self.creds, static_discovery=False)
            event = {
                "summary": summary,
                "description": description,
                "location": location,
                "start": {"dateTime": start},
                "end": {"dateTime": end},
            }
            created = service.events().insert(calendarId="primary", body=event).execute()
            log.info(f"[CALENDAR] Created event: {created.get('htmlLink')}")
            return {
                "id": created.get("id"),
                "summary": created.get("summary"),
                "link": created.get("htmlLink"),
            }
        except Exception as e:
            log.error(f"[CALENDAR] Create error: {e}")
            return None

    # ========================================================================
    # Gmail
    # ========================================================================

    def gmail_list_messages(self, max_results: int = 10, query: str = "is:unread") -> List[Dict]:
        """List recent Gmail messages."""
        if not self.is_authenticated:
            return []
        try:
            from googleapiclient.discovery import build
            service = build("gmail", "v1", credentials=self.creds, static_discovery=False)
            results = service.users().messages().list(
                userId="me", maxResults=max_results, q=query
            ).execute()
            messages = results.get("messages", [])
            detailed = []
            for msg_ref in messages[:max_results]:
                msg = service.users().messages().get(
                    userId="me", id=msg_ref["id"], format="metadata",
                    metadataHeaders=["From", "Subject", "Date"]
                ).execute()
                headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
                detailed.append({
                    "id": msg["id"],
                    "from": headers.get("From", ""),
                    "subject": headers.get("Subject", ""),
                    "date": headers.get("Date", ""),
                    "snippet": msg.get("snippet", ""),
                })
            return detailed
        except Exception as e:
            log.error(f"[GMAIL] List error: {e}")
            return []

    def gmail_send(self, to: str, subject: str, body: str) -> bool:
        """Send an email via Gmail."""
        if not self.is_authenticated:
            return False
        try:
            import base64
            from email.mime.text import MIMEText
            from googleapiclient.discovery import build
            service = build("gmail", "v1", credentials=self.creds, static_discovery=False)
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()
            log.info(f"[GMAIL] Email sent to {to}")
            return True
        except Exception as e:
            log.error(f"[GMAIL] Send error: {e}")
            return False
